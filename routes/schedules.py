from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Schedule, Lead

schedules = Blueprint('schedules', __name__)

@schedules.route('/schedules/edit/<int:schedule_id>', methods=['GET', 'POST'])
def edit_schedule(schedule_id):
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    schedule = Schedule.query.get_or_404(schedule_id)
    leads = Lead.query.all()
    
    if request.method == 'POST':
        schedule.title = request.form['title']
        schedule.description = request.form['description']
        schedule.start_time = request.form['start_time']
        schedule.end_time = request.form['end_time']
        schedule.lead_id = request.form['lead_id'] if request.form['lead_id'] else None
        
        try:
            db.session.commit()
            flash('Schedule updated successfully!', 'success')
            return redirect(url_for('schedules.list_schedules'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating schedule. Please try again.', 'error')
            
    return render_template('schedules/edit_schedule.html', schedule=schedule, leads=leads)
