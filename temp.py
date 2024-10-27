def process_emails_for_user(settings, parent_session, app):
    """Process emails for a single user with exponential backoff"""
    try:
        # 設定の検証を追加
        validate_email_settings(settings, app)
    except ValueError as e:
        app.logger.error(f"Email settings validation failed for user {settings.user_id}: {str(e)}")
        return

    # Get or create tracker
    tracker = parent_session.query(EmailFetchTracker)\
        .filter_by(user_id=settings.user_id)\
        .order_by(EmailFetchTracker.last_fetch_time.desc())\
        .first()

    if not tracker:
        tracker = EmailFetchTracker(
            user_id=settings.user_id,
            last_fetch_time=datetime.utcnow() - timedelta(minutes=5)
        )
        parent_session.add(tracker)
        parent_session.flush()

    # Connect to email server with exponential backoff
    mail = None
    retry_delays = [5, 10, 20]  # Exponential backoff delays in seconds

    for attempt, delay in enumerate(retry_delays):
        try:
            app.logger.info(f"Attempt {attempt + 1} to connect to mail server for user {settings.user_id}")
            mail = connect_to_email_server(app, settings)
            if mail:
                break
            app.logger.warning(f"Failed to connect on attempt {attempt + 1}, waiting {delay}s before retry...")
            time.sleep(delay)
        except imaplib.IMAP4.error as e:
            error_str = str(e)
            if '[UNAVAILABLE]' in error_str:
                app.logger.error(f"Server temporarily unavailable (attempt {attempt + 1}): {error_str}")
                if attempt < len(retry_delays) - 1:
                    time.sleep(delay)
                    continue
                app.logger.error("Server still unavailable after all retries")
                return
            app.logger.error(f"IMAP error on attempt {attempt + 1}: {error_str}")
            if attempt < len(retry_delays) - 1:
                time.sleep(delay)
                continue
        except Exception as e:
            app.logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < len(retry_delays) - 1:
                time.sleep(delay)
                continue
            app.logger.error("Failed all connection attempts")
            return

        if not mail:
            app.logger.error(f"Failed to connect to email server for user {settings.user_id} after all retries")
            return

        # Search for new emails
        date_str = tracker.last_fetch_time.strftime("%d-%b-%Y")
        try:
            _, message_numbers = mail.search(None, f'(SINCE "{date_str}")')
        except imaplib.IMAP4.error as e:
            app.logger.error(f"IMAP search error: {str(e)}")
            return

        # Process each email
        processed_count = 0
        for num in message_numbers[0].split():
            try:
                _, msg_data = mail.fetch(num, '(RFC822)')
                if not (msg_data and msg_data[0] and msg_data[0][1]):
                    continue

                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)

                # メールの重複チェックのために必要な情報を取得
                message_id = clean_string(msg.get('Message-ID', ''))

                # 既に処理済みのメールかチェック
                if message_id:
                    existing_email = parent_session.query(Email)\
                        .filter_by(
                            message_id=message_id,
                            user_id=settings.user_id
                        ).first()

                    if existing_email:
                        app.logger.info(f"Skipping already processed email: {message_id}")
                        continue

                subject = clean_string(decode_email_header(msg['subject']))
                sender = clean_string(decode_email_header(msg['from']))
                sender_name = clean_string(extract_sender_name(sender))
                sender_email = clean_string(extract_email_address(sender))
                content = clean_string(get_email_content(msg))
                received_date = parse_email_date(msg.get('date'))

                # リードの検索と作成をトランザクション内で行う
                try:
                    lead = parent_session.query(Lead)\
                        .filter_by(email=sender_email, user_id=settings.user_id)\
                        .with_for_update()\
                        .first()

                    if not lead:
                        app.logger.debug(f"Creating new lead - Name: {sender_name}, Email: {sender_email}, User ID: {settings.user_id}")
                        lead = Lead(
                            name=sender_name,
                            email=sender_email,
                            status='New',
                            score=0.0,
                            user_id=settings.user_id,
                            last_contact=received_date or datetime.utcnow()
                        )
                        parent_session.add(lead)
                        parent_session.flush()
                        app.logger.debug(f"Created new lead with ID: {lead.id}")

                    # Check if email is mass mail
                    is_mass_mail, spam_reason = is_mass_email(msg, content)
                    if is_mass_mail:
                        app.logger.info(f"Detected mass email from {sender_email}. Reason: {spam_reason}")
                        update_lead_status_for_mass_email(lead, is_mass_mail, spam_reason, parent_session, app)
                    # Analyze email if not spam
                    elif lead.status != 'Spam':
                        try:
                            ai_response = analyze_email(subject, content, lead.user_id)
                            process_ai_response(ai_response, lead, app)
                        except Exception as e:
                            app.logger.error(f"AI analysis error: {str(e)}")

                    email_record = Email(
                        message_id=message_id,
                        sender=sender_email,
                        sender_name=sender_name,
                        subject=subject,
                        content=content,
                        lead_id=lead.id,
                        user_id=settings.user_id,
                        received_date=received_date
                    )
                    parent_session.add(email_record)
                    parent_session.flush()

                    processed_count += 1
                    app.logger.info(f"Processed email: {message_id} from {sender_email}")

                except Exception as e:
                    app.logger.error(f"Error processing lead and email record: {str(e)}")
                    parent_session.rollback()
                    continue

            except Exception as e:
                app.logger.error(f"Error processing email {num}: {str(e)}")
                continue

        # Update tracker
        try:
            tracker.last_fetch_time = datetime.utcnow()
            parent_session.commit()
            app.logger.info(f"Processed {processed_count} emails for user {settings.user_id}")
        except Exception as e:
            app.logger.error(f"Error updating tracker: {str(e)}")
            parent_session.rollback()
            raise

    except Exception as e:
        app.logger.error(f"Error checking emails for user {settings.user_id}: {str(e)}")
        parent_session.rollback()
        raise
    finally:
        try:
            if mail:
                mail.close()
                mail.logout()
        except:
            pass