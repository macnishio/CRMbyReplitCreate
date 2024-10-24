from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Task
from extensions import db
from datetime import datetime
from sqlalchemy import func
from ai_analysis import analyze_tasks

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/')
@login_required
def list_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date.asc()).all()
    
    # Get task status counts
    status_counts = db.session.query(
        Task.status,
        func.count(Task.id).label('count')
    ).filter_by(user_id=current_user.id).group_by(Task.status).all()
    
    task_status_counts = [{'status': status, 'count': count} for status, count in status_counts]
    
    # Get AI analysis
    ai_analysis = analyze_tasks(tasks)
    
    return render_template('tasks/list_tasks.html', 
                         tasks=tasks,
                         task_status_counts=task_status_counts,
                         ai_analysis=ai_analysis,
                         utcnow=datetime.utcnow)

@tasks_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        status = request.form['status']
        new_task = Task(
            title=title,
            description=description,
            due_date=due_date,
            status=status,
            user_id=current_user.id,
            lead_id=request.form.get('lead_id')  # Make lead_id optional
        )
        db.session.add(new_task)
        db.session.commit()
        flash('新しいタスクが追加されました。', 'success')
        return redirect(url_for('tasks.list_tasks'))
    return render_template('tasks/add_task.html')

@tasks_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('このタスクを編集する権限がありません。', 'error')
        return redirect(url_for('tasks.list_tasks'))
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        task.status = request.form['status']
        task.completed = 'completed' in request.form
        db.session.commit()
        flash('タスクが更新されました。', 'success')
        return redirect(url_for('tasks.list_tasks'))
    return render_template('tasks/edit_task.html', task=task)

@tasks_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('このタスクを削除する権限がありません。', 'error')
        return redirect(url_for('tasks.list_tasks'))
    db.session.delete(task)
    db.session.commit()
    flash('タスクが削除されました。', 'success')
    return redirect(url_for('tasks.list_tasks'))
