from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from models import Lead, Opportunity, Task, Schedule, Email
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from sqlalchemy.exc import SQLAlchemyError
from ai_analysis import analyze_email, process_ai_response
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

        # バイト列の場合の処理
        if isinstance(content, bytes):
            # ISO-2022-JPの特徴的なマーカーをチェック
            if b'$B' in content or b'(B' in content:
                try:
                    decoded_content = content.decode('iso-2022-jp', errors='replace')
                    encoding_used = 'iso-2022-jp'
                    current_app.logger.debug(f"Successfully decoded as ISO-2022-JP, length: {len(decoded_content)}")
                except UnicodeDecodeError as e:
                    current_app.logger.error(f"ISO-2022-JP decoding failed: {e}")
                    # フォールバック処理
                    decoded_content = content.decode('utf-8', errors='replace')
                    encoding_used = 'utf-8-fallback'
            else:
                # その他のエンコーディングを試行
                encodings = ['utf-8', 'shift_jis', 'euc-jp']
                for encoding in encodings:
                    try:
                        decoded_content = content.decode(encoding)
                        encoding_used = encoding
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # どのエンコーディングも失敗した場合
                    decoded_content = content.decode('utf-8', errors='replace')
                    encoding_used = 'utf-8-fallback'
        else:
            decoded_content = str(content) if content else ''
            encoding_used = 'text'

        # クリーニングと整形
        cleaned_content = clean_email_content(decoded_content)
        sanitized_content = html.escape(cleaned_content)
        formatted_content = sanitized_content.replace('\n', '<br>')

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
        current_app.logger.error(f"Error processing email content: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'メール内容の処理中にエラーが発生しました',
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
