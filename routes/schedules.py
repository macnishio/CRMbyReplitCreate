from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Schedule, Lead
from extensions import db
from datetime import datetime, timedelta
from ai_analysis import analyze_schedules

bp = Blueprint('schedules', __name__)

@bp.route('/')
@bp.route('')
@login_required
def list_schedules():
    schedules = Schedule.query.filter_by(user_id=current_user.id).order_by(Schedule.start_time.asc()).all()
    
    # Get AI analysis
    ai_analysis = analyze_schedules(schedules)
    
    return render_template('schedules/list_schedules.html',
                         schedules=schedules,
                         ai_analysis=ai_analysis,
                         now=datetime.utcnow,
                         timedelta=timedelta)

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
    return render_template('schedules/add_schedule.html', leads=leads)

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
