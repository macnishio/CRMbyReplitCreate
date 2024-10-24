from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import Schedule, Lead
from extensions import db

schedules_bp = Blueprint('schedules', __name__)

@schedules_bp.route('/')
@login_required
def list_schedules():
    schedules = Schedule.query.filter_by(user_id=current_user.id).all()
    return render_template('schedules/list_schedules.html', schedules=schedules)

@schedules_bp.route('/edit/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def edit_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    
    # Ensure the schedule belongs to the current user
    if schedule.user_id != current_user.id:
        flash('You do not have permission to edit this schedule.', 'danger')
        return redirect(url_for('schedules.list_schedules'))
    
    if request.method == 'POST':
        try:
            schedule.title = request.form['title']
            schedule.description = request.form['description']
            schedule.start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
            schedule.end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
            schedule.lead_id = request.form['lead_id'] if request.form['lead_id'] else None
            
            db.session.commit()
            flash('Schedule updated successfully!', 'success')
            return redirect(url_for('schedules.list_schedules'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating schedule: {str(e)}', 'danger')
    
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    return render_template('schedules/edit_schedule.html', schedule=schedule, leads=leads)
