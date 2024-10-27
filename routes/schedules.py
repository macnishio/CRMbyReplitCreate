from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from models import Schedule, Lead, Opportunity, Account, User
from extensions import db
from forms import ScheduleForm
from datetime import datetime
from google_calendar import create_calendar_event, update_calendar_event, delete_calendar_event
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('schedules', __name__)

@bp.route('/')
@login_required
def list_schedules():
    schedules = Schedule.query.filter_by(user_id=current_user.id).order_by(Schedule.start_time).all()
    return render_template('schedules/list_schedules.html', schedules=schedules)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_schedule():
    form = ScheduleForm()
    form.user_id.data = current_user.id
    
    if form.validate_on_submit():
        schedule = Schedule(
            title=form.title.data,
            description=form.description.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            user_id=current_user.id,
            lead_id=form.lead_id.data if form.lead_id.data else None,
            opportunity_id=form.opportunity_id.data if form.opportunity_id.data else None,
            account_id=form.account_id.data if form.account_id.data else None
        )
        
        try:
            db.session.add(schedule)
            db.session.flush()  # Get ID without committing
            
            # Create Google Calendar event if integration is configured
            if current_user.google_calendar_id and current_user.google_service_account_file:
                event_id = create_calendar_event(current_user, schedule)
                if event_id:
                    schedule.google_event_id = event_id
                else:
                    flash('Failed to create Google Calendar event', 'error')
            
            db.session.commit()
            flash('Schedule added successfully!', 'success')
            return redirect(url_for('schedules.list_schedules'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding schedule: {str(e)}")
            flash('Error adding schedule', 'error')
    
    return render_template('schedules/add_schedule.html', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_schedule(id):
    schedule = Schedule.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = ScheduleForm(obj=schedule)
    
    if form.validate_on_submit():
        try:
            schedule.title = form.title.data
            schedule.description = form.description.data
            schedule.start_time = form.start_time.data
            schedule.end_time = form.end_time.data
            schedule.lead_id = form.lead_id.data if form.lead_id.data else None
            schedule.opportunity_id = form.opportunity_id.data if form.opportunity_id.data else None
            schedule.account_id = form.account_id.data if form.account_id.data else None
            
            # Update Google Calendar event if integration is configured
            if current_user.google_calendar_id and current_user.google_service_account_file:
                event_id = update_calendar_event(current_user, schedule)
                if event_id:
                    schedule.google_event_id = event_id
                else:
                    flash('Failed to update Google Calendar event', 'error')
            
            db.session.commit()
            flash('Schedule updated successfully!', 'success')
            return redirect(url_for('schedules.list_schedules'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating schedule: {str(e)}")
            flash('Error updating schedule', 'error')
    
    return render_template('schedules/edit_schedule.html', form=form, schedule=schedule)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_schedule(id):
    schedule = Schedule.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        # Delete from Google Calendar if integration is configured
        if current_user.google_calendar_id and current_user.google_service_account_file:
            if not delete_calendar_event(current_user, schedule):
                flash('Failed to delete Google Calendar event', 'error')
        
        db.session.delete(schedule)
        db.session.commit()
        flash('Schedule deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting schedule: {str(e)}")
        flash('Error deleting schedule', 'error')
    
    return redirect(url_for('schedules.list_schedules'))

@bp.route('/transfer_to_google', methods=['POST'])
@login_required
def transfer_to_google():
    if not current_user.google_calendar_id or not current_user.google_service_account_file:
        return jsonify({
            "success": False,
            "message": "Google Calendar integration not configured. Please configure it in settings."
        })

    data = request.get_json()
    schedule_ids = data.get('schedules', [])
    
    if not schedule_ids:
        return jsonify({
            "success": False,
            "message": "No schedules selected for transfer."
        })
    
    success_count = 0
    error_messages = []
    
    for schedule_id in schedule_ids:
        schedule = Schedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
        if schedule:
            try:
                event_id = create_calendar_event(current_user, schedule)
                if event_id:
                    schedule.google_event_id = event_id
                    success_count += 1
                else:
                    error_messages.append(f"Failed to create event for schedule: {schedule.title}")
            except Exception as e:
                error_messages.append(f"Error processing schedule {schedule.title}: {str(e)}")
    
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Database error while saving Google Calendar event IDs",
            "errors": [str(e)]
        })
    
    return jsonify({
        "success": success_count > 0,
        "message": f"Successfully transferred {success_count} events to Google Calendar",
        "errors": error_messages
    })
