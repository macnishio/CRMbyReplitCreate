import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from models import Opportunity, Schedule, Task, Lead
from extensions import db
from anthropic import Anthropic, APIError, APIConnectionError, AuthenticationError
from flask import current_app
from models import UserSettings
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

# 現在の日時を日本時間で取得
jst_datetime = datetime.now(ZoneInfo("Asia/Tokyo"))
# 日付をフォーマット
formatted_date = jst_datetime.strftime("%Y-%m-%d")

def handle_ai_error(func_name, error):
    """Handle AI analysis errors with proper logging and localized messages"""
    error_msg = None
    if isinstance(error, AuthenticationError):
        error_msg = "APIキーが無効です。システム管理者に連絡してください。"
        current_app.logger.error(f"{func_name}: Invalid API key - {str(error)}")
    elif isinstance(error, APIConnectionError):
        error_msg = "AI分析サービスに接続できません。しばらく待ってから再試行してください。"
        current_app.logger.error(f"{func_name}: Connection error - {str(error)}")
    elif isinstance(error, APIError):
        error_msg = "AI分析中にエラーが発生しました。しばらく待ってから再試行してください。"
        current_app.logger.error(f"{func_name}: API error - {str(error)}")
    else:
        error_msg = "予期せぬエラーが発生しました。システム管理者に連絡してください。"
        current_app.logger.error(f"{func_name}: Unexpected error - {str(error)}")
    return f'<p class="error-message">{error_msg}</p>'

def analyze_data(data_type, data):
    """Analyze data using Claude AI"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'

        client = Anthropic(api_key=user_settings.claude_api_key)

        prompt = f"""今は日本時間の{formatted_date}です。以下の{data_type}データを分析してください:\n{data}\n
        以下の項目について簡潔に分析してください:
        1. {data_type}の全体的な状況
        2. 重要な要素の特定
        3. {data_type}管理の改善点
        4. 次のステップへの提案
        回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        if message and hasattr(message.content[0], 'text'):
            content = message.content[0].text
            if not content.startswith('<p>'):
                content = '<p>' + content.replace('\n\n', '</p><p>') + '</p>'
            return content
        return '<p>AI分析の結果を取得できませんでした。</p>'

    except Exception as e:
        return handle_ai_error(f"analyze_{data_type}", e)

def analyze_tasks(tasks):
    """Analyze tasks using Claude AI"""
    task_data = "\n".join([
        f"- タイトル: {task.title}, 期限: {task.due_date}, ステータス: {task.status}"
        for task in tasks
    ])
    return analyze_data("タスク", task_data)

def analyze_schedules(schedules):
    """Analyze schedules using Claude AI"""
    schedule_data = "\n".join([
        f"- タイトル: {sch.title}, 開始: {sch.start_time}, 終了: {sch.end_time}"
        for sch in schedules
    ])
    return analyze_data("スケジュール", schedule_data)

def analyze_opportunities(opportunities):
    """Analyze opportunities using Claude AI"""
    opp_data = "\n".join([
        f"- 名前: {opp.name}, ステージ: {opp.stage}, 金額: {opp.amount}, 完了予定: {opp.close_date}"
        for opp in opportunities
    ])
    return analyze_data("商談", opp_data)

def analyze_leads(leads):
    """Analyze leads using Claude AI"""
    lead_data = "\n".join([
        f"- 名前: {lead.name}, ステータス: {lead.status}, スコア: {lead.score}, 最終接触: {lead.last_contact}"
        for lead in leads
    ])
    return analyze_data("リード", lead_data)

def analyze_email(subject, content, user_id=None):
    """Analyze email content using Claude AI"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=user_id if user_id else current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return json.dumps({
                "Opportunities": [],
                "Schedules": [],
                "Tasks": []
            })

        client = Anthropic(api_key=user_settings.claude_api_key)

        system_message = """
            You are an AI assistant that analyzes emails and provides suggestions for opportunities, schedules, and tasks.
            Be concise and direct in your responses.
            """
        prompt = f"""
        今は日本時間の{formatted_date}です。以下のメールを分析し、機会、スケジュール、タスクを簡潔にJSON形式で提案してください。

        Subject: {subject}
        Content: {content}

        - 具体的な日時は「YYYY-MM-DD HH:MM」形式か「現在時刻」で記載
        - 推測は避け、メールに明示されている情報のみを使用

        フォーマット:
        {{
          "Opportunities": [
            "送信者名:機会の説明"
          ],
          "Schedules": [{{
            "Description": "送信元名:説明",
            "Start Time": "YYYY-MM-DD HH:MM" または"Start Time": {formatted_date},
            "End Time": "YYYY-MM-DD HH:MM" または"End Time": {formatted_date}"
          }}],
          "Tasks": [{{
            "Description": "送信元名:説明",
            "Due Date": "YYYY-MM-DD" または"Due Date": {formatted_date}"
          }}]
        }}
        """

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            temperature=0.7,
            system=system_message,
            messages=[{"role": "user", "content": prompt}]
        )

        if message and hasattr(message.content[0], 'text'):
            content = message.content[0].text
            if content.startswith('{'):
                return content
            return json.dumps({
                "Opportunities": [],
                "Schedules": [],
                "Tasks": []
            })
        return json.dumps({
            "Opportunities": [],
            "Schedules": [],
            "Tasks": []
        })

    except Exception as e:
        current_app.logger.error(f"AI analysis error: {str(e)}")
        return handle_ai_error("analyze_email", e) # handle_ai_error を呼び出す

def create_or_get_lead(email_data, user_id):
    """Create a new lead if it doesn't exist or get existing lead"""
    try:
        # メールアドレスでリードを検索
        lead = Lead.query.filter_by(email=email_data.sender).first()

        if not lead:
            # リードが存在しない場合は新規作成
            lead = Lead(
                name=email_data.sender_name or email_data.sender.split('@')[0],
                email=email_data.sender,
                user_id=user_id,
                status='New',
                score=0.0
            )
            db.session.add(lead)
            db.session.commit()
            current_app.logger.info(f"Created new lead: {lead.id}")

        return lead

    except Exception as e:
        current_app.logger.error(f"Error creating/getting lead: {str(e)}")
        db.session.rollback()
        return None

def create_opportunities_from_ai(opportunities, lead): #修正
    """Create opportunities from AI analysis data"""
    if not lead or not lead.id or not lead.user_id:
        raise ValueError("Invalid lead data for opportunity creation")

    for opp_desc in opportunities:
        opportunity = Opportunity(
            lead_id=lead.id,
            user_id=lead.user_id,
            description=opp_desc,
            status="New",
            created_at=datetime.utcnow(),
            is_ai_generated=True #is_ai_generatedフラグを追加
        )
        db.session.add(opportunity)

def create_schedules_from_ai(schedules, lead):  #修正
    """Create schedules from AI analysis data"""
    if not lead or not lead.id or not lead.user_id:
        raise ValueError("Invalid lead data for schedule creation")

    for schedule_data in schedules:
        schedule = Schedule(
            lead_id=lead.id,
            user_id=lead.user_id,
            description=schedule_data.get("Description", ""),
            start_time=parse_datetime(schedule_data.get("Start Time")),
            end_time=parse_datetime(schedule_data.get("End Time")),
            created_at=datetime.utcnow(),
            is_ai_generated=True #is_ai_generatedフラグを追加
        )
        db.session.add(schedule)


def create_tasks_from_ai(tasks, lead):  #修正
    """Create tasks from AI analysis data"""
    if not lead or not lead.id or not lead.user_id:
        raise ValueError("Invalid lead data for task creation")

    for task_data in tasks:
        task = Task(
            lead_id=lead.id,
            user_id=lead.user_id,
            description=task_data.get("Description", ""),
            due_date=parse_datetime(task_data.get("Due Date")),
            status="New",
            created_at=datetime.utcnow(),
            is_ai_generated=True #is_ai_generatedフラグを追加
        )
        db.session.add(task)

def normalize_json_response(response_text):
    """AIレスポンスのJSON形式を正規化する"""
    try:
        # デバッグログ追加
        current_app.logger.debug(f"Raw AI response: {response_text}")

        # 余分な空白や改行を削除
        response_text = response_text.strip()

        # JSON部分を抽出
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start == -1 or end == 0:
            current_app.logger.error("No valid JSON found in response")
            return None

        json_text = response_text[start:end]

        # デバッグログ追加
        current_app.logger.debug(f"Extracted JSON: {json_text}")

        # JSONをパースしてバリデーション
        data = json.loads(json_text)

        # 正規化されたデータ構造
        normalized = {
            "Opportunities": [],
            "Schedules": [],
            "Tasks": []
        }

        # Opportunities
        if "Opportunities" in data and isinstance(data["Opportunities"], list):
            normalized["Opportunities"] = [
                opp.strip() for opp in data["Opportunities"] if isinstance(opp, str)
            ]

        # Schedules
        if "Schedules" in data and isinstance(data["Schedules"], list):
            for schedule in data["Schedules"]:
                if isinstance(schedule, dict):
                    normalized_schedule = {
                        "Description": str(schedule.get("Description", "")),
                        "Start Time": str(schedule.get("Start Time", "2024-10-29")),
                        "End Time": str(schedule.get("End Time", "2024-10-29"))
                    }
                    normalized["Schedules"].append(normalized_schedule)

        # Tasks
        if "Tasks" in data and isinstance(data["Tasks"], list):
            for task in data["Tasks"]:
                if isinstance(task, dict):
                    normalized_task = {
                        "Description": str(task.get("Description", "")),
                        "Due Date": str(task.get("Due Date", "2024-10-29"))
                    }
                    normalized["Tasks"].append(normalized_task)

        # 正規化されたJSONを文字列に変換
        result = json.dumps(normalized, ensure_ascii=False)
        current_app.logger.debug(f"Normalized JSON: {result}")
        return result

    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON parse error: {str(e)}")
        return '<p class="error-message">AI分析の結果を取得できませんでした。</p>'
    except Exception as e:
        current_app.logger.error(f"Error normalizing JSON response: {str(e)}")
        return '<p class="error-message">AI分析の結果を取得できませんでした。</p>'

def create_opportunities_from_ai(opportunities, lead):
    """Create opportunities from AI analysis data"""
    if not lead or not lead.id or not lead.user_id:
        raise ValueError("Invalid lead data for opportunity creation")

    for opp_desc in opportunities:
        opportunity = Opportunity(
            lead_id=lead.id,
            user_id=lead.user_id,
            description=opp_desc,
            status="New",
            created_at=datetime.utcnow()
        )
        db.session.add(opportunity)

def create_schedules_from_ai(schedules, lead):
    """Create schedules from AI analysis data"""
    if not lead or not lead.id or not lead.user_id:
        raise ValueError("Invalid lead data for schedule creation")

    for schedule_data in schedules:
        schedule = Schedule(
            lead_id=lead.id,
            user_id=lead.user_id,
            description=schedule_data.get("Description", ""),
            start_time=parse_datetime(schedule_data.get("Start Time")),
            end_time=parse_datetime(schedule_data.get("End Time")),
            created_at=datetime.utcnow()
        )
        db.session.add(schedule)

def create_tasks_from_ai(tasks, lead):
    """Create tasks from AI analysis data"""
    if not lead or not lead.id or not lead.user_id:
        raise ValueError("Invalid lead data for task creation")

    for task_data in tasks:
        task = Task(
            lead_id=lead.id,
            user_id=lead.user_id,
            description=task_data.get("Description", ""),
            due_date=parse_datetime(task_data.get("Due Date")),
            status="New",
            created_at=datetime.utcnow()
        )
        db.session.add(task)

def process_ai_response(response: str, email_record: Email, app: Flask) -> None:
    """Process AI analysis response with improved transaction handling"""
    if not isinstance(response, str):
        app.logger.error(f"Invalid response type: {type(response)}")
        return

    if not email_record or not email_record.lead_id or not email_record.user_id:
        app.logger.error("Invalid email record for AI processing")
        return

    # 新しいセッションを作成
    new_session = db.session()
    try:
        # JSON解析とバリデーション
        try:
            data = json.loads(response)
            app.logger.debug(f"Parsed AI response data: {data}")
        except json.JSONDecodeError as e:
            app.logger.error(f"Failed to parse AI response JSON: {str(e)}")
            return

        # メールレコードを新しいセッションにマージ
        email_record = new_session.merge(email_record)

        # トランザクションを明示的に管理
        if new_session.is_active:
            app.logger.debug("Rolling back existing transaction")
            new_session.rollback()

        try:
            # AI分析情報の更新
            email_record.ai_analysis = response
            email_record.ai_analysis_date = datetime.utcnow()
            email_record.ai_model_used = "claude-3-haiku-20240307"
            new_session.add(email_record)

            # 検出されたアイテムの作成
            if 'Opportunities' in data:
                for opp in data['Opportunities']:
                    if isinstance(opp, str) and opp.strip():
                        opportunity = Opportunity(
                            lead_id=email_record.lead_id,
                            user_id=email_record.user_id,
                            description=opp.strip(),
                            status="New",
                            email_id=email_record.id,
                            created_at=datetime.utcnow()
                        )
                        new_session.add(opportunity)

            if 'Schedules' in data:
                for schedule_data in data['Schedules']:
                    if isinstance(schedule_data, dict):
                        schedule = Schedule(
                            lead_id=email_record.lead_id,
                            user_id=email_record.user_id,
                            description=schedule_data.get('Description', '').strip(),
                            start_time=parse_datetime(schedule_data.get('Start Time')),
                            end_time=parse_datetime(schedule_data.get('End Time')),
                            email_id=email_record.id,
                            created_at=datetime.utcnow()
                        )
                        new_session.add(schedule)

            if 'Tasks' in data:
                for task_data in data['Tasks']:
                    if isinstance(task_data, dict):
                        task = Task(
                            lead_id=email_record.lead_id,
                            user_id=email_record.user_id,
                            description=task_data.get('Description', '').strip(),
                            due_date=parse_datetime(task_data.get('Due Date')),
                            status="New",
                            email_id=email_record.id,
                            created_at=datetime.utcnow()
                        )
                        new_session.add(task)

            # 変更をコミット
            new_session.commit()
            app.logger.info(f"Successfully processed AI response for email {email_record.id}")

        except Exception as e:
            app.logger.error(f"Error processing AI data: {str(e)}", exc_info=True)
            new_session.rollback()
            raise

    except Exception as e:
        app.logger.error(f"Error in process_ai_response: {str(e)}", exc_info=True)
        if new_session.is_active:
            new_session.rollback()
    finally:
        new_session.close()


def parse_datetime(date_str):
    """Parse datetime string with improved error handling"""
    if not date_str:
        return None

    try:
        if isinstance(date_str, str):
            # YYYY-MM-DD形式の場合
            if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
                return datetime.strptime(date_str, '%Y-%m-%d').replace(
                    tzinfo=timezone.utc
                )
            # YYYY-MM-DD HH:MM:SS形式の場合
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').replace(
                tzinfo=timezone.utc
            )
    except ValueError as e:
        app.logger.warning(f"Error parsing datetime {date_str}: {str(e)}")
        return None

def analyze_email_endpoint(email_id):
    """Analyze email endpoint with improved session handling"""
    session = db.session()
    try:
        email = session.query(Email).get(email_id)
        if not email:
            return jsonify({"error": "Email not found"}), 404

        # セッションにアタッチされた状態でデータを取得
        email_data = {
            "email_id": email.id,
            "subject": email.subject,
            "content": email.content,
            "user_id": email.user_id
        }

        try:
            ai_response = analyze_email(
                email_data["subject"],
                email_data["content"],
                email_data["user_id"]
            )

            if ai_response:
                email.ai_analysis = ai_response
                email.ai_analysis_date = datetime.utcnow()
                email.ai_model_used = "claude-3-haiku-20240307"
                session.add(email)
                session.commit()

                # 新しいセッションでAIレスポンスの処理
                process_ai_response(ai_response, email, current_app)

                return jsonify({"success": True, "analysis": ai_response})

            return jsonify({"error": "AI analysis failed"}), 500

        except Exception as e:
            current_app.logger.error(f"Error analyzing email: {str(e)}", exc_info=True)
            session.rollback()
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        current_app.logger.error(f"Error in analyze_email_endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()

def parse_datetime(date_str):  #修正
    """Parse date string to datetime with timezone"""
    if not date_str:
        return None

    try:
        # まずYYYY-MM-DD形式を試す
        return datetime.strptime(date_str, '%Y-%m-%d').replace(
            hour=0, minute=0, second=0,
            tzinfo=timezone.utc
        )
    except ValueError:
        try:
            # YYYY-MM-DD HH:MM:SS形式を試す
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return None