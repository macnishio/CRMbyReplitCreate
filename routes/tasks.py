from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Task, Lead, Opportunity, Account
from extensions import db
from forms import TaskForm
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/')
@login_required
def list_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date.asc()).all()
    return render_template('tasks/list_tasks.html', tasks=tasks)

@tasks_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    form = TaskForm()
    
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
            task = Task(
                title=form.title.data,
                description=form.description.data,
                due_date=form.due_date.data,
                completed=form.completed.data,
                user_id=current_user.id,
                created_at=datetime.utcnow()
            )

            # Set relationships if selected
            if form.lead_id.data and form.lead_id.data != '0':
                task.lead_id = int(form.lead_id.data)
            if form.opportunity_id.data and form.opportunity_id.data != '0':
                task.opportunity_id = int(form.opportunity_id.data)
            if form.account_id.data and form.account_id.data != '0':
                task.account_id = int(form.account_id.data)

            db.session.add(task)
            db.session.commit()
            flash('タスクが正常に追加されました。', 'success')
            return redirect(url_for('tasks.list_tasks'))

        except Exception as e:
            db.session.rollback()
            flash('タスクの追加中にエラーが発生しました。', 'error')

    return render_template('tasks/add_task.html', form=form)

@tasks_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = TaskForm(obj=task)
    
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
            # Update basic fields
            task.title = form.title.data
            task.description = form.description.data
            task.due_date = form.due_date.data
            task.completed = form.completed.data
            
            # Update relationships with proper type conversion
            if not form.lead_id.data or form.lead_id.data == '0':
                task.lead_id = None
            else:
                task.lead_id = int(form.lead_id.data)
                
            if not form.opportunity_id.data or form.opportunity_id.data == '0':
                task.opportunity_id = None
            else:
                task.opportunity_id = int(form.opportunity_id.data)
                
            if not form.account_id.data or form.account_id.data == '0':
                task.account_id = None
            else:
                task.account_id = int(form.account_id.data)
                
            db.session.commit()
            flash('タスクが正常に更新されました。', 'success')
            return redirect(url_for('tasks.list_tasks'))
            
        except Exception as e:
            db.session.rollback()
            flash('タスクの更新中にエラーが発生しました。', 'error')
    
    # Set initial values for relationships
    if task.lead_id:
        form.lead_id.data = str(task.lead_id)
    if task.opportunity_id:
        form.opportunity_id.data = str(task.opportunity_id)
    if task.account_id:
        form.account_id.data = str(task.account_id)
        
    return render_template('tasks/edit_task.html', form=form, task=task)

@tasks_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_task(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        db.session.delete(task)
        db.session.commit()
        flash('タスクが正常に削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('タスクの削除中にエラーが発生しました。', 'error')
    return redirect(url_for('tasks.list_tasks'))

@tasks_bp.route('/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    action = request.form.get('action')
    selected_ids = request.form.getlist('selected_tasks')
    
    if not selected_ids:
        flash('タスクが選択されていません。', 'error')
        return redirect(url_for('tasks.list_tasks'))
    
    try:
        if action == 'delete':
            for task_id in selected_ids:
                task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
                if task:
                    db.session.delete(task)
            flash('選択したタスクが正常に削除されました。', 'success')
        elif action == 'complete':
            for task_id in selected_ids:
                task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
                if task:
                    task.completed = True
            flash('選択したタスクが完了としてマークされました。', 'success')
        elif action == 'incomplete':
            for task_id in selected_ids:
                task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
                if task:
                    task.completed = False
            flash('選択したタスクが未完了としてマークされました。', 'success')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('一括操作中にエラーが発生しました。', 'error')
    
    return redirect(url_for('tasks.list_tasks'))
