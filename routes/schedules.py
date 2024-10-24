from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Schedule, Lead
from extensions import db
from datetime import datetime

bp = Blueprint('schedules', __name__)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_schedule():
    leads = Lead.query.all()
    if request.method == 'POST':
        try:
            schedule = Schedule(
                title=request.form['title'],
                description=request.form['description'],
                start_time=datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M'),
                end_time=datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M'),
                lead_id=int(request.form['lead_id']) if request.form['lead_id'] else None
            )
            db.session.add(schedule)
            db.session.commit()
            flash('Schedule created successfully!', 'success')
            return redirect(url_for('schedules.list_schedules'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating schedule: {str(e)}', 'error')
    
    return render_template('schedules/create.html', schedule=None, leads=leads)

@bp.route('/edit/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def edit_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    leads = Lead.query.all()
    
    if request.method == 'POST':
        try:
            schedule.title = request.form['title']
            schedule.description = request.form['description']
            schedule.start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
            schedule.end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
            schedule.lead_id = int(request.form['lead_id']) if request.form['lead_id'] else None
            
            db.session.commit()
            flash('Schedule updated successfully!', 'success')
            return redirect(url_for('schedules.list_schedules'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating schedule: {str(e)}', 'error')
            
    return render_template('schedules/edit.html', schedule=schedule, leads=leads)

@bp.route('/')
@bp.route('/list')
@login_required
def list_schedules():
    schedules = Schedule.query.all()
    return render_template('schedules/list_schedules.html', schedules=schedules)
