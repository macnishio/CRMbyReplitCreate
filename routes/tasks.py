from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Task, User, Lead, Opportunity, Account
from forms import TaskForm
from datetime import datetime

bp = Blueprint('tasks', __name__, url_prefix='/tasks')

@bp.route('/')
@login_required
def list_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks/list.html', tasks=tasks)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_task():
    form = TaskForm()
    form.user_id.choices = [(user.id, user.username) for user in User.query.all()]
    form.lead_id.choices = [(0, 'None')] + [(lead.id, lead.name) for lead in Lead.query.all()]
    form.opportunity_id.choices = [(0, 'None')] + [(opp.id, opp.name) for opp in Opportunity.query.all()]
    form.account_id.choices = [(0, 'None')] + [(acc.id, acc.name) for acc in Account.query.all()]
    
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            user_id=form.user_id.data,
            lead_id=form.lead_id.data if form.lead_id.data != 0 else None,
            opportunity_id=form.opportunity_id.data if form.opportunity_id.data != 0 else None,
            account_id=form.account_id.data if form.account_id.data != 0 else None
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully')
        return redirect(url_for('tasks.list_tasks'))
    return render_template('tasks/create.html', form=form)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    form = TaskForm(obj=task)
    form.user_id.choices = [(user.id, user.username) for user in User.query.all()]
    form.lead_id.choices = [(0, 'None')] + [(lead.id, lead.name) for lead in Lead.query.all()]
    form.opportunity_id.choices = [(0, 'None')] + [(opp.id, opp.name) for opp in Opportunity.query.all()]
    form.account_id.choices = [(0, 'None')] + [(acc.id, acc.name) for acc in Account.query.all()]
    
    if form.validate_on_submit():
        form.populate_obj(task)
        task.lead_id = form.lead_id.data if form.lead_id.data != 0 else None
        task.opportunity_id = form.opportunity_id.data if form.opportunity_id.data != 0 else None
        task.account_id = form.account_id.data if form.account_id.data != 0 else None
        db.session.commit()
        flash('Task updated successfully')
        return redirect(url_for('tasks.list_tasks'))
    return render_template('tasks/edit.html', form=form, task=task)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully')
    return redirect(url_for('tasks.list_tasks'))

@bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    task = Task.query.get_or_404(id)
    task.completed = not task.completed
    db.session.commit()
    flash('Task status updated')
    return redirect(url_for('tasks.list_tasks'))
