from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Task, Lead

tasks = Blueprint('tasks', __name__)

@tasks.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    task = Task.query.get_or_404(task_id)
    leads = Lead.query.all()
    
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.due_date = request.form['due_date']
        task.priority = request.form['priority']
        task.status = request.form['status']
        task.lead_id = request.form['lead_id'] if request.form['lead_id'] else None
        
        try:
            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('tasks.list_tasks'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating task. Please try again.', 'error')
            
    return render_template('tasks/edit_task.html', task=task, leads=leads)
