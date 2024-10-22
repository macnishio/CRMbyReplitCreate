from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from extensions import db
from models import Schedule, User, Account, Lead, Opportunity
from forms import ScheduleForm
from datetime import datetime

bp = Blueprint('schedules', __name__, url_prefix='/schedules')

@bp.route('/')
@login_required
def list_schedules():
    schedules = Schedule.query.filter_by(user_id=current_user.id).all()
    return render_template('schedules/list_schedules.html', schedules=schedules)

@bp.route('/add_schedule', methods=['GET', 'POST'])
@login_required
def add_schedule():
    form = ScheduleForm()
    form.user_id.choices = [(user.id, user.username) for user in User.query.all()]
    form.account_id.choices = [(0, 'None')] + [(account.id, account.name) for account in Account.query.all()]
    form.lead_id.choices = [(0, 'None')] + [(lead.id, lead.name) for lead in Lead.query.all()]
    form.opportunity_id.choices = [(0, 'None')] + [(opportunity.id, opportunity.name) for opportunity in Opportunity.query.all()]
    
    if form.validate_on_submit():
        try:
            schedule = Schedule(
                title=form.title.data,
                description=form.description.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                user_id=current_user.id,
                account_id=form.account_id.data if form.account_id.data != 0 else None,
                lead_id=form.lead_id.data if form.lead_id.data != 0 else None,
                opportunity_id=form.opportunity_id.data if form.opportunity_id.data != 0 else None
            )
            db.session.add(schedule)
            db.session.commit()
            current_app.logger.info(f"Schedule created: {schedule}")
            flash('スケジュールが正常に作成されました', 'success')
            return redirect(url_for('schedules.list_schedules'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating schedule: {str(e)}")
            flash('スケジュールの作成中にエラーが発生しました。もう一度お試しください。', 'error')
    else:
        current_app.logger.info(f"Form validation failed: {form.errors}")
    
    return render_template('schedules/add_schedule.html', form=form)

@bp.route('/<int:id>')
@login_required
def schedule_detail(id):
    schedule = Schedule.query.get_or_404(id)
    return render_template('schedules/detail.html', schedule=schedule)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_schedule(id):
    schedule = Schedule.query.get_or_404(id)
    form = ScheduleForm(obj=schedule)
    form.user_id.choices = [(user.id, user.username) for user in User.query.all()]
    form.account_id.choices = [(0, 'None')] + [(account.id, account.name) for account in Account.query.all()]
    form.lead_id.choices = [(0, 'None')] + [(lead.id, lead.name) for lead in Lead.query.all()]
    form.opportunity_id.choices = [(0, 'None')] + [(opportunity.id, opportunity.name) for opportunity in Opportunity.query.all()]
    
    if form.validate_on_submit():
        try:
            form.populate_obj(schedule)
            schedule.account_id = form.account_id.data if form.account_id.data != 0 else None
            schedule.lead_id = form.lead_id.data if form.lead_id.data != 0 else None
            schedule.opportunity_id = form.opportunity_id.data if form.opportunity_id.data != 0 else None
            db.session.commit()
            current_app.logger.info(f"Schedule updated: {schedule}")
            flash('スケジュールが正常に更新されました', 'success')
            return redirect(url_for('schedules.schedule_detail', id=schedule.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating schedule: {str(e)}")
            flash('スケジュールの更新中にエラーが発生しました。もう一度お試しください。', 'error')
    else:
        current_app.logger.info(f"Form validation failed: {form.errors}")
    
    return render_template('schedules/edit.html', form=form, schedule=schedule)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_schedule(id):
    schedule = Schedule.query.get_or_404(id)
    try:
        db.session.delete(schedule)
        db.session.commit()
        current_app.logger.info(f"Schedule deleted: {schedule}")
        flash('スケジュールが正常に削除されました', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting schedule: {str(e)}")
        flash('スケジュールの削除中にエラーが発生しました。もう一度お試しください。', 'error')
    return redirect(url_for('schedules.list_schedules'))
