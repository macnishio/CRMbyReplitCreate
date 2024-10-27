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

bp = Blueprint('schedules', __name__)

@bp.route('/')
@bp.route('')
@login_required
def list_schedules():
    query = Schedule.query.filter_by(user_id=current_user.id)

    # Apply filters if provided
    date_filter = request.args.get('date_filter')
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

    # Order by start time and eager load lead relationship
    schedules = query.options(db.joinedload(Schedule.lead)).order_by(Schedule.start_time.asc()).all()

    # Get AI analysis
    ai_analysis = analyze_schedules(schedules)

    return render_template('schedules/list_schedules.html',
                         schedules=schedules,
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

        if action == 'delete':
            for schedule in schedules:
                db.session.delete(schedule)
            flash(f'{len(schedules)}件のスケジュールを削除しました。', 'success')

        elif action == 'reschedule':
            new_date = request.form.get('new_date')
            new_time = request.form.get('new_time')

            if not new_date or not new_time:
                flash('新しい日時を選択してください。', 'error')
                return redirect(url_for('schedules.list_schedules'))

            try:
                new_datetime = datetime.strptime(f"{new_date} {new_time}", '%Y-%m-%d %H:%M')
                for schedule in schedules:
                    duration = schedule.end_time - schedule.start_time
                    schedule.start_time = new_datetime
                    schedule.end_time = new_datetime + duration
                flash(f'{len(schedules)}件のスケジュールを変更しました。', 'success')
            except ValueError:
                flash('日時の形式が正しくありません。', 'error')
                return redirect(url_for('schedules.list_schedules'))

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash('操作中にエラーが発生しました。', 'error')
        current_app.logger.error(f"Bulk action error: {str(e)}")

    return redirect(url_for('schedules.list_schedules'))

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_schedule():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start_time = datetime.strptime(f"{request.form['start_date']} {request.form['start_time']}", '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(f"{request.form['end_date']} {request.form['end_time']}", '%Y-%m-%d %H:%M')
        lead_id = request.form.get('lead_id')

        schedule = Schedule(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            user_id=current_user.id,
            lead_id=lead_id
        )

        db.session.add(schedule)
        db.session.commit()
        flash('スケジュールが追加されました。', 'success')
        return redirect(url_for('schedules.list_schedules'))

    leads = Lead.query.filter_by(user_id=current_user.id).all()
    return render_template('schedules/create.html', leads=leads)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_schedule(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.user_id != current_user.id:
        flash('このスケジュールを編集する権限がありません。', 'error')
        return redirect(url_for('schedules.list_schedules'))

    if request.method == 'POST':
        schedule.title = request.form['title']
        schedule.description = request.form['description']
        schedule.start_time = datetime.strptime(f"{request.form['start_date']} {request.form['start_time']}", '%Y-%m-%d %H:%M')
        schedule.end_time = datetime.strptime(f"{request.form['end_date']} {request.form['end_time']}", '%Y-%m-%d %H:%M')
        schedule.lead_id = request.form.get('lead_id')

        db.session.commit()
        flash('スケジュールが更新されました。', 'success')
        return redirect(url_for('schedules.list_schedules'))

    leads = Lead.query.filter_by(user_id=current_user.id).all()
    return render_template('schedules/edit_schedule.html', schedule=schedule, leads=leads)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_schedule(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.user_id != current_user.id:
        flash('このスケジュールを削除する権限がありません。', 'error')
        return redirect(url_for('schedules.list_schedules'))

    db.session.delete(schedule)
    db.session.commit()
    flash('スケジュールが削除されました。', 'success')
    return redirect(url_for('schedules.list_schedules'))

@bp.route('/transfer_to_google', methods=['POST'])
@login_required
def transfer_to_google():
    data = request.json
    selected_schedules = data.get('schedules', [])

    if not selected_schedules:
        current_app.logger.warning("転送するイベントが選択されていません。")
        return jsonify({"success": False, "message": "転送するイベントが選択されていません。"})

    # Google Calendar API の認証情報を設定
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = current_user.google_service_account_file

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)

    transferred_count = 0
    errors = []

    for schedule_id in selected_schedules:
        schedule = Schedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
        if schedule:
            event = {
                'summary': schedule.title,
                'description': schedule.description,
                'start': {
                    'dateTime': schedule.start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': schedule.end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            try:
                # Google Calendar ID を取得
                calendar_id = current_user.google_calendar_id
                if not calendar_id:
                    raise ValueError("Google Calendar ID が設定されていません。")

                # イベントをGoogleカレンダーに挿入
                created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
                transferred_count += 1
                current_app.logger.info(f"イベント {schedule.id} を Google カレンダーに転送しました。イベントID: {created_event.get('id')}")
            except Exception as e:
                error_msg = f"イベント {schedule.id} の転送中にエラーが発生しました: {str(e)}"
                current_app.logger.error(error_msg)
                errors.append(error_msg)
        else:
            current_app.logger.warning(f"ID {schedule_id} のスケジュールが見つかりません。")

    response = {
        "success": transferred_count > 0,
        "message": f"{transferred_count} 件のイベントを Google カレンダーに転送しました。",
        "transferred_count": transferred_count,
        "total_selected": len(selected_schedules),
        "errors": errors,
    }

    current_app.logger.info(f"Google カレンダーへの転送が完了しました。{response['message']}")
    return jsonify(response)