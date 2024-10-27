from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Schedule, Lead, Opportunity, Account
from extensions import db
from forms import ScheduleForm
from datetime import datetime
from analytics import analyze_schedule

schedules_bp = Blueprint('schedules', __name__)

@schedules_bp.route('/')
@login_required
def list_schedules():
    schedules = Schedule.query.filter_by(user_id=current_user.id).order_by(Schedule.start_time.asc()).all()
    return render_template('schedules/list_schedules.html', schedules=schedules)

@schedules_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_schedule():
    form = ScheduleForm()
    
    # Get leads, opportunities and accounts for the current user for dropdowns
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    opportunities = Opportunity.query.filter_by(user_id=current_user.id).all()
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    
    # Update the choices for dropdowns
    form.lead_id.choices = [('0', '選択してください')] + [(str(lead.id), f"{lead.name} ({lead.email})") for lead in leads]
    form.opportunity_id.choices = [('0', '選択してください')] + [(str(opp.id), opp.name) for opp in opportunities]
    form.account_id.choices = [('0', '選択してください')] + [(str(account.id), account.name) for account in accounts]

    if form.validate_on_submit():
        try:
            schedule = Schedule(
                title=form.title.data,
                description=form.description.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                user_id=current_user.id
            )
            
            # Set relationships if selected
            if form.lead_id.data and form.lead_id.data != '0':
                schedule.lead_id = int(form.lead_id.data)
            if form.opportunity_id.data and form.opportunity_id.data != '0':
                schedule.opportunity_id = int(form.opportunity_id.data)
            if form.account_id.data and form.account_id.data != '0':
                schedule.account_id = int(form.account_id.data)
            
            db.session.add(schedule)
            db.session.commit()
            
            # Analyze the schedule after creation
            analyze_schedule(schedule)
            
            flash('スケジュールが正常に追加されました。', 'success')
            return redirect(url_for('schedules.list_schedules'))
        except Exception as e:
            db.session.rollback()
            flash('スケジュールの追加中にエラーが発生しました。', 'error')
    
    return render_template('schedules/add_schedule.html', form=form)

# Rest of the code remains the same...
