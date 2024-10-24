from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import Task, Lead
from extensions import db

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Ensure the task belongs to the current user
    if task.user_id != current_user.id:
        flash('You do not have permission to edit this task.', 'danger')
        return redirect(url_for('tasks.list_tasks'))
    
    if request.method == 'POST':
        try:
            task.title = request.form['title']
            task.description = request.form['description']
            task.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
            task.priority = request.form['priority']
            task.status = request.form['status']
            task.lead_id = request.form['lead_id'] if request.form['lead_id'] else None
            
            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('tasks.list_tasks'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating task: {str(e)}', 'danger')
    
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks/edit_task.html', task=task, leads=leads)
