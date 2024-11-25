from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from models import Lead, Opportunity, Task, Schedule, Email
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from sqlalchemy.exc import SQLAlchemyError
from ai_analysis import analyze_email, process_ai_response, summarize_email_content
import html
import re
from email_encoding import convert_encoding, clean_email_content, analyze_iso2022jp_text

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def dashboard():
    try:
        leads_page = request.args.get('leads_page', 1, type=int)
        tasks_page = request.args.get('tasks_page', 1, type=int)
        schedules_page = request.args.get('schedules_page', 1, type=int)
        emails_page = request.args.get('emails_page', 1, type=int)
        per_page = 5

        leads = Lead.query.filter_by(user_id=current_user.id)\
            .order_by(Lead.created_at.desc())\
            .paginate(page=leads_page, per_page=per_page, error_out=False)

        today = datetime.utcnow()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        this_month_revenue = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0.0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage == 'Closed Won',
            Opportunity.close_date >= first_day_of_month,
            Opportunity.close_date <= today
        ).scalar() or 0.0

        first_day_prev_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
        last_day_prev_month = first_day_of_month - timedelta(microseconds=1)
        previous_month_revenue = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0.0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage == 'Closed Won',
            Opportunity.close_date >= first_day_prev_month,
            Opportunity.close_date <= last_day_prev_month
        ).scalar() or 0.0

        opportunities_by_stage = db.session.query(
            Opportunity.stage,
            func.count(Opportunity.id).label('count'),
            func.coalesce(func.sum(Opportunity.amount), 0.0).label('total_amount')
        ).filter(
            Opportunity.user_id == current_user.id
        ).group_by(Opportunity.stage).all() or []

        total_pipeline = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0.0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage.in_(['Initial Contact', 'Qualification', 'Proposal', 'Negotiation'])
        ).scalar() or 0.0

        tasks = Task.query.filter_by(
            user_id=current_user.id,
            completed=False
        ).filter(
            Task.due_date >= datetime.utcnow()
        ).order_by(Task.due_date)\
        .paginate(page=tasks_page, per_page=per_page, error_out=False)
        
        schedules = Schedule.query.filter_by(user_id=current_user.id)\
            .filter(Schedule.start_time >= datetime.utcnow())\
            .order_by(Schedule.start_time)\
            .paginate(page=schedules_page, per_page=per_page, error_out=False)
        
        emails = Email.query.filter_by(user_id=current_user.id)\
            .order_by(Email.received_date.desc())\
            .paginate(page=emails_page, per_page=20, error_out=False)

        return render_template('dashboard.html',
                            leads=leads,
                            opportunities=opportunities_by_stage,
                            tasks=tasks,
                            schedules=schedules,
                            emails=emails,
                            this_month_revenue=float(this_month_revenue),
                            previous_month_revenue=float(previous_month_revenue),
                            total_pipeline=float(total_pipeline))

    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in dashboard: {str(e)}")
        flash('データベースエラーが発生しました。', 'error')
        return render_template('dashboard.html',
                            leads=None,
                            opportunities=[],
                            tasks=None,
                            schedules=None,
                            emails=None,
                            this_month_revenue=0.0,
                            previous_month_revenue=0.0,
                            total_pipeline=0.0)
    except Exception as e:
        current_app.logger.error(f"Unexpected error in dashboard: {str(e)}")
        flash('予期せぬエラーが発生しました。', 'error')
        return render_template('dashboard.html',
                            leads=None,
                            opportunities=[],
                            tasks=None,
                            schedules=None,
                            emails=None,
                            this_month_revenue=0.0,
                            previous_month_revenue=0.0,
                            total_pipeline=0.0)

@bp.route('/api/emails/<int:email_id>')
@login_required
def get_email_content(email_id):
    try:
        email = Email.query.filter_by(
            id=email_id,
            user_id=current_user.id
        ).first()

        if not email:
            return jsonify({'error': 'メールが見つかりません'}), 404

        content = email.content
        current_app.logger.debug(f"Processing email {email_id} content type: {type(content)}")
        
        if isinstance(content, bytes):
            current_app.logger.debug(f"Content length: {len(content)} bytes")
            # First check for ISO-2022-JP markers
            current_app.logger.debug("Checking for ISO-2022-JP markers")
            if analyze_iso2022jp_text(content):
                try:
                    current_app.logger.debug("ISO-2022-JP markers found, attempting decode")
                    decoded_content = content.decode('iso-2022-jp')
                    current_app.logger.debug("Successfully decoded using ISO-2022-JP")
                    encoding_used = 'iso-2022-jp'
                except UnicodeDecodeError as e:
                    current_app.logger.warning(f"ISO-2022-JP decoding failed: {str(e)}")
                    try:
                        current_app.logger.debug("Trying Shift-JIS as fallback")
                        decoded_content = content.decode('shift_jis')
                        encoding_used = 'shift_jis'
                    except UnicodeDecodeError:
                        current_app.logger.debug("Falling back to general encoding conversion")
                        decoded_content, encoding_used = convert_encoding(content)
            else:
                current_app.logger.debug("No ISO-2022-JP markers found, trying general encoding conversion")
                decoded_content, encoding_used = convert_encoding(content)
        else:
            decoded_content = str(content) if content else ''
            encoding_used = 'text'
            current_app.logger.debug("Content was already in text format")

        # Clean and sanitize the content
        current_app.logger.debug("Cleaning and sanitizing content")
        cleaned_content = clean_email_content(decoded_content)
        current_app.logger.debug(f"Cleaned content length: {len(cleaned_content)}")
        
        sanitized_content = html.escape(cleaned_content)
        formatted_content = sanitized_content.replace('\n', '<br>')
        current_app.logger.debug(f"Final formatted content length: {len(formatted_content)}")

        return jsonify({
            'id': email.id,
            'subject': email.subject,
            'sender': email.sender,
            'sender_name': email.sender_name,
            'content': formatted_content,
            'received_date': email.received_date.isoformat() if email.received_date else None,
            'encoding_used': encoding_used
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching email content: {str(e)}")
        return jsonify({
            'error': 'メール内容の取得中にエラーが発生しました',
            'details': str(e)
        }), 500

@bp.route('/api/emails/<int:email_id>/analyze', methods=['POST'])
@login_required
def analyze_email_endpoint(email_id):
    try:
        email = Email.query.filter_by(
            id=email_id,
            user_id=current_user.id
        ).first_or_404()

        analysis_result = analyze_email(
            email.subject,
            email.content,
            current_user.id
        )

        email.ai_analysis = analysis_result
        email.ai_analysis_date = datetime.now()

        process_ai_response(analysis_result, email, current_app)
        
        db.session.commit()

        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'tasks': [{
                'title': task.title,
                'due_date': task.due_date.isoformat()
            } for task in Task.query.filter_by(
                email_id=email.id,
                is_ai_generated=True
            ).all()],
            'schedules': [{
                'title': schedule.title,
                'start_time': schedule.start_time.isoformat(),
                'end_time': schedule.end_time.isoformat()
            } for schedule in Schedule.query.filter_by(
                email_id=email.id,
                is_ai_generated=True
            ).all()]
        })

    except Exception as e:
        current_app.logger.error(f"Error analyzing email: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'error': 'メールの分析中にエラーが発生しました',
            'details': str(e)
        }), 500


@bp.route('/api/emails/<int:email_id>/summarize', methods=['POST'])
def summarize_email(email_id):
    try:
        email = Email.query.get_or_404(email_id)
        # AI要約処理を実行
        summary = summarize_email_content(email.subject, email.content)
        if summary:
            return jsonify({'success': True, 'summary': summary})
        else:
            return jsonify({
                'success': False, 
                'error': '要約の生成に失敗しました。'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'エラーが発生しました: {str(e)}'
        }), 500


@bp.route('/api/emails/<int:email_id>/related-items', methods=['GET'])
def get_related_items(email_id):
    email = Email.query.get_or_404(email_id)
    tasks = Task.query.filter_by(email_id=email_id).all()
    schedules = Schedule.query.filter_by(email_id=email_id).all()
    tasks_data = [{'title': t.title, 'description': t.description, 'due_date': t.due_date.strftime('%Y-%m-%d')} for t in tasks]
    schedules_data = [{'title': s.title, 'description': s.description, 'datetime': s.start_time.strftime('%Y-%m-%d %H:%M')} for s in schedules]
    return jsonify({'tasks': tasks_data, 'schedules': schedules_data})