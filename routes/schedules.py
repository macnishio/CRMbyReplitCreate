from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from models import Schedule, Lead
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
from ai_analysis import analyze_schedules
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json
from forms import ScheduleForm

bp = Blueprint('schedules', __name__)

@bp.route('/')
@bp.route('')
@login_required
def list_schedules():
    # Load user's saved filter preferences
    user_settings = current_user.settings
    saved_filters = {}
    if user_settings and user_settings.filter_preferences:
        try:
            all_filters = json.loads(user_settings.filter_preferences)
            saved_filters = all_filters.get('schedules', {})
        except json.JSONDecodeError:
            current_app.logger.error("Failed to parse saved filter preferences")

    # Get filter parameters from request, fallback to saved filters
    date_filter = request.args.get('date_filter', saved_filters.get('date_filter', ''))
    lead_filter = request.args.get('lead_filter', saved_filters.get('lead_filter', ''))
    ai_generated_filter = request.args.get('ai_generated_filter', saved_filters.get('ai_generated_filter', ''))

    # Build base query
    query = Schedule.query.filter_by(user_id=current_user.id)

    # Apply date filter
    if date_filter:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if date_filter == 'today':
            query = query.filter(
                Schedule.start_time >= today,
                Schedule.start_time < today + timedelta(days=1)
            )
        elif date_filter == 'week':
            query = query.filter(
                Schedule.start_time >= today,
                Schedule.start_time < today + timedelta(days=7)
            )
        elif date_filter == 'month':
            query = query.filter(
                Schedule.start_time >= today,
                Schedule.start_time < today + timedelta(days=30)
            )

    # Apply lead filter
    if lead_filter:
        query = query.filter(Schedule.lead_id == lead_filter)

    # Apply AI generated filter
    if ai_generated_filter:
        is_ai_generated = ai_generated_filter.lower() == 'true'
        query = query.filter(Schedule.is_ai_generated == is_ai_generated)

    # Get all leads for the filter dropdown
    leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.name).all()

    # Order by start time and eager load lead relationship
    schedules = query.options(db.joinedload(Schedule.lead)).order_by(Schedule.start_time.asc()).all()

    # Get AI analysis
    ai_analysis = analyze_schedules(schedules)

    return render_template('schedules/list_schedules.html',
                         schedules=schedules,
                         leads=leads,
                         ai_analysis=ai_analysis,
                         now=datetime.utcnow,
                         timedelta=timedelta)

@bp.route('/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    action = request.form.get('action')
    selected_schedules = request.form.getlist('selected_schedules[]')
    
    if not action or not selected_schedules:
        flash('操作とスケジュールを選択してください。', 'error')
        return redirect(url_for('schedules.list_schedules'))

    try:
        schedules = Schedule.query.filter(
            Schedule.id.in_(selected_schedules),
            Schedule.user_id == current_user.id
        ).all()

        if not schedules:
            flash('選択されたスケジュールが見つかりません。', 'error')
            return redirect(url_for('schedules.list_schedules'))

        if action == 'delete':
            deleted_count = 0
            for schedule in schedules:
                db.session.delete(schedule)
                deleted_count += 1
            db.session.commit()
            flash(f'{deleted_count}件のスケジュールを削除しました。', 'success')

        elif action == 'reschedule':
            new_date = request.form.get('new_date')
            new_time = request.form.get('new_time')

            if not new_date or not new_time:
                flash('新しい日時を選択してください。', 'error')
                return redirect(url_for('schedules.list_schedules'))

            try:
                new_datetime = datetime.strptime(f"{new_date} {new_time}", '%Y-%m-%d %H:%M')
                updated_count = 0
                for schedule in schedules:
                    duration = schedule.end_time - schedule.start_time
                    schedule.start_time = new_datetime
                    schedule.end_time = new_datetime + duration
                    updated_count += 1
                db.session.commit()
                flash(f'{updated_count}件のスケジュールを変更しました。', 'success')
            except ValueError:
                flash('日時の形式が正しくありません。', 'error')
                return redirect(url_for('schedules.list_schedules'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk action error: {str(e)}")
        flash('操作中にエラーが発生しました。', 'error')

    return redirect(url_for('schedules.list_schedules'))


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_schedule():
    form = ScheduleForm()
    leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.name).all()
    form.lead_id.choices = [(0, '選択してください')] + [(lead.id, f"{lead.name} ({lead.email})") for lead in leads]
    
    if form.validate_on_submit():
        try:
            schedule = Schedule(
                title=form.title.data,
                description=form.description.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                user_id=current_user.id,  # 現在のユーザーIDを自動設定
                lead_id=form.lead_id.data if form.lead_id.data and form.lead_id.data != 0 else None
            )
            db.session.add(schedule)
            db.session.commit()
            flash('スケジュールが追加されました。', 'success')
            return redirect(url_for('schedules.list_schedules'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Schedule creation error: {str(e)}")
            flash('スケジュールの作成中にエラーが発生しました。', 'error')
    
    return render_template('schedules/create.html', form=form, leads=leads)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_schedule(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.user_id != current_user.id:
        flash('このスケジュールを編集する権限がありません。', 'error')
        return redirect(url_for('schedules.list_schedules'))

    form = ScheduleForm(obj=schedule)
    leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.name).all()

    if form.validate_on_submit():
        try:
            schedule.title = form.title.data
            schedule.description = form.description.data
            schedule.start_time = form.start_time.data
            schedule.end_time = form.end_time.data
            # フォームから送信されたlead_idを直接取得
            lead_id = request.form.get('lead_id')
            schedule.lead_id = int(lead_id) if lead_id else None

            db.session.commit()
            flash('スケジュールが更新されました。', 'success')
            return redirect(url_for('schedules.list_schedules'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Schedule update error: {str(e)}")
            flash('スケジュールの更新中にエラーが発生しました。', 'error')

    return render_template('schedules/edit.html', form=form, schedule=schedule, leads=leads)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_schedule(id):
    try:
        schedule = Schedule.query.get_or_404(id)
        if schedule.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'このスケジュールを削除する権限がありません。'
            }), 403

        db.session.delete(schedule)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'スケジュールが削除されました。'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Schedule deletion error: {str(e)}")
        return jsonify({
            'success': False,
            'message': '削除中にエラーが発生しました。'
        }), 500

@bp.route('/transfer_to_google', methods=['POST'])
@login_required
def transfer_to_google():
    try:
        data = request.get_json()
        selected_schedules = data.get('schedules', [])

        if not selected_schedules:
            return jsonify({
                'success': False,
                'message': '転送するスケジュールが選択されていません。'
            })

        if not current_user.google_service_account_file or not current_user.google_calendar_id:
            return jsonify({
                'success': False,
                'message': 'Googleカレンダーの設定が完了していません。'
            })

        # Google Calendar API の設定
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        credentials = service_account.Credentials.from_service_account_file(
            current_user.google_service_account_file, 
            scopes=SCOPES
        )
        service = build('calendar', 'v3', credentials=credentials)

        success_count = 0
        errors = []

        for schedule_id in selected_schedules:
            try:
                schedule = Schedule.query.filter_by(
                    id=schedule_id,
                    user_id=current_user.id
                ).first()

                if not schedule:
                    continue

                event = {
                    'summary': schedule.title,
                    'description': schedule.description,
                    'start': {
                        'dateTime': schedule.start_time.isoformat(),
                        'timeZone': 'Asia/Tokyo',
                    },
                    'end': {
                        'dateTime': schedule.end_time.isoformat(),
                        'timeZone': 'Asia/Tokyo',
                    },
                }

                service.events().insert(
                    calendarId=current_user.google_calendar_id,
                    body=event
                ).execute()
                success_count += 1

            except Exception as e:
                errors.append(f"ID {schedule_id}: {str(e)}")
                current_app.logger.error(f"Google Calendar transfer error: {str(e)}")

        return jsonify({
            'success': success_count > 0,
            'message': f'{success_count}件のスケジュールを転送しました。',
            'errors': errors if errors else None
        })

    except Exception as e:
        current_app.logger.error(f"Google Calendar transfer error: {str(e)}")
        return jsonify({
            'success': False,
            'message': '転送中にエラーが発生しました。',
            'error': str(e)
        }), 500