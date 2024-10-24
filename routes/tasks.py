from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Task, Lead
from extensions import db
from datetime import datetime

bp = Blueprint('tasks', __name__)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_task():
    leads = Lead.query.all()
    if request.method == 'POST':
        try:
            task = Task(
                title=request.form['title'],
                description=request.form['description'],
                due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d'),
                priority=request.form['priority'],
                status=request.form['status'],
                lead_id=int(request.form['lead_id']) if request.form['lead_id'] else None
            )
            db.session.add(task)
            db.session.commit()
            flash('Task created successfully!', 'success')
            return redirect(url_for('tasks.list_tasks'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating task: {str(e)}', 'error')
    
    return render_template('tasks/create.html', task=None, leads=leads)

@bp.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    leads = Lead.query.all()
    
    if request.method == 'POST':
        try:
            task.title = request.form['title']
            task.description = request.form['description']
            task.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
            task.priority = request.form['priority']
            task.status = request.form['status']
            task.lead_id = int(request.form['lead_id']) if request.form['lead_id'] else None
            
            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('tasks.list_tasks'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating task: {str(e)}', 'error')
            
    return render_template('tasks/edit.html', task=task, leads=leads)

@bp.route('/')
@bp.route('/list')
@login_required
def list_tasks():
    tasks = Task.query.all()
    return render_template('tasks/list.html', tasks=tasks)
