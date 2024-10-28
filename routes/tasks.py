from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import Task, Lead
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
from ai_analysis import analyze_tasks
from forms import TaskForm

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/')
@login_required
def list_tasks():
    query = Task.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    status = request.args.get('status')
    if status:
        query = query.filter(Task.status == status)
        
    due_date = request.args.get('due_date')
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if due_date == 'today':
        query = query.filter(
            Task.due_date >= today,
            Task.due_date < today + timedelta(days=1)
        )
    elif due_date == 'week':
        query = query.filter(
            Task.due_date >= today,
            Task.due_date < today + timedelta(days=7)
        )
    elif due_date == 'month':
        query = query.filter(
            Task.due_date >= today,
            Task.due_date < today + timedelta(days=30)
        )
    elif due_date == 'overdue':
        query = query.filter(Task.due_date < today)

    # Order by due date and eager load lead relationship
    tasks = query.options(db.joinedload(Task.lead)).order_by(Task.due_date.asc()).all()
    
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

@tasks_bp.route('/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    action = request.form.get('action')
    selected_tasks = request.form.getlist('selected_tasks[]')
    
    if not action or not selected_tasks:
        flash('操作とタスクを選択してください。', 'error')
        return redirect(url_for('tasks.list_tasks'))
    
    try:
        tasks = Task.query.filter(
            Task.id.in_(selected_tasks),
            Task.user_id == current_user.id
        ).all()
        
        if action == 'complete':
            for task in tasks:
                task.completed = True
                task.status = 'Completed'
            flash(f'{len(tasks)}件のタスクを完了にしました。', 'success')
            
        elif action == 'delete':
            for task in tasks:
                db.session.delete(task)
            flash(f'{len(tasks)}件のタスクを削除しました。', 'success')
            
        elif action == 'change_status':
            new_status = request.form.get('new_status')
            if new_status:
                for task in tasks:
                    task.status = new_status
                flash(f'{len(tasks)}件のタスクのステータスを変更しました。', 'success')
            else:
                flash('新しいステータスを選択してください。', 'error')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash('操作中にエラーが発生しました。', 'error')
        current_app.logger.error(f"Bulk action error: {str(e)}")
    
    return redirect(url_for('tasks.list_tasks'))

@tasks_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    form = TaskForm()  # フォームのインスタンスを作成
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        status = request.form['status']
        lead_id = request.form.get('lead_id')
        
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            status=status,
            user_id=current_user.id,
            lead_id=lead_id
        )
        db.session.add(task)
        db.session.commit()
        flash('新しいタスクが追加されました。', 'success')
        return redirect(url_for('tasks.list_tasks'))
    
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks/create.html',form=form , leads=leads)

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
        task.lead_id = request.form.get('lead_id')
        
        db.session.commit()
        flash('タスクが更新されました。', 'success')
        return redirect(url_for('tasks.list_tasks'))
    
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks/edit_task.html', task=task, leads=leads)

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
