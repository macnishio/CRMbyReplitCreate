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

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def dashboard():
    try:
        # Get pagination parameters for each section
        leads_page = request.args.get('leads_page', 1, type=int)
        tasks_page = request.args.get('tasks_page', 1, type=int)
        schedules_page = request.args.get('schedules_page', 1, type=int)
        emails_page = request.args.get('emails_page', 1, type=int)
        per_page = 5

        # Get recent leads with pagination
        leads = Lead.query.filter_by(user_id=current_user.id)\
            .order_by(Lead.created_at.desc())\
            .paginate(page=leads_page, per_page=per_page, error_out=False)

        # Calculate revenue metrics with proper error handling
        today = datetime.utcnow()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Current month revenue
        this_month_revenue = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0.0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage == 'Closed Won',
            Opportunity.close_date >= first_day_of_month,
            Opportunity.close_date <= today
        ).scalar() or 0.0

        # Previous month revenue
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

        # Get opportunities by stage with proper error handling
        opportunities_by_stage = db.session.query(
            Opportunity.stage,
            func.count(Opportunity.id).label('count'),
            func.coalesce(func.sum(Opportunity.amount), 0.0).label('total_amount')
        ).filter(
            Opportunity.user_id == current_user.id
        ).group_by(Opportunity.stage).all() or []

        # Calculate total pipeline value
        total_pipeline = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0.0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage.in_(['Initial Contact', 'Qualification', 'Proposal', 'Negotiation'])
        ).scalar() or 0.0

        # Get upcoming tasks with pagination
        tasks = Task.query.filter_by(
            user_id=current_user.id,
            completed=False
        ).filter(
            Task.due_date >= datetime.utcnow()
        ).order_by(Task.due_date)\
        .paginate(page=tasks_page, per_page=per_page, error_out=False)
        
        # Get upcoming schedules with pagination
        schedules = Schedule.query.filter_by(user_id=current_user.id)\
            .filter(Schedule.start_time >= datetime.utcnow())\
            .order_by(Schedule.start_time)\
            .paginate(page=schedules_page, per_page=per_page, error_out=False)
        
        # Get recent emails with pagination
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

        # Content decoding with improved Japanese encoding handling
        content = email.content
        decoded_content = None
        encoding_used = None

        if isinstance(content, bytes):
            # Check for $B marker which indicates iso-2022-jp encoding
            if b'$B' in content:
                try:
                    decoded_content = content.decode('iso-2022-jp')
                    encoding_used = 'iso-2022-jp'
                except UnicodeDecodeError:
                    pass

            # If $B marker decode failed or wasn't present, try ordered encodings
            if not decoded_content:
                encodings = [
                    'iso-2022-jp',
                    'shift_jis',
                    'euc_jp',
                    'utf-8',
                    'cp932'
                ]

                for encoding in encodings:
                    try:
                        decoded = content.decode(encoding)
                        # Check if decode produced meaningful content
                        if decoded and not all(c == '?' for c in decoded):
                            decoded_content = decoded
                            encoding_used = encoding
                            break
                    except (UnicodeDecodeError, LookupError):
                        continue

            # If all specific encodings fail, use utf-8 with error handling
            if not decoded_content:
                decoded_content = content.decode('utf-8', errors='replace')
                encoding_used = 'utf-8 (with replacements)'

        else:
            decoded_content = str(content) if content else ''
            encoding_used = 'text'

        # Clean and format content
        decoded_content = decoded_content or ''
        
        # Remove any remaining escape sequences
        decoded_content = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', decoded_content)
        
        # Sanitize content
        sanitized_content = html.escape(decoded_content)
        
        # Replace newlines with <br> tags for proper display
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
        current_app.logger.error(f"Error fetching email content: {str(e)}")
        return jsonify({'error': 'メール内容の取得中にエラーが発生しました'}), 500

@bp.route('/api/emails/<int:email_id>/analyze', methods=['POST'])
@login_required
def analyze_email_endpoint(email_id):
    try:
        email = Email.query.filter_by(
            id=email_id,
            user_id=current_user.id
        ).first_or_404()

        # AI分析を実行
        analysis_result = analyze_email(
            email.subject,
            email.content,
            current_user.id
        )

        # メールの分析情報を更新
        email.ai_analysis = analysis_result
        email.ai_analysis_date = datetime.now()

        # process_ai_responseを使用して自動的にタスクとスケジュールを作成
        process_ai_response(analysis_result, email, current_app)
        
        db.session.commit()

        # 作成されたアイテムをレスポンスに含める
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
