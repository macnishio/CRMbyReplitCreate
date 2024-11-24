from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from models import Task, Lead
from extensions import db
import json
from datetime import datetime, timedelta
from sqlalchemy import func
from ai_analysis import analyze_tasks
from forms import TaskForm

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/')
@login_required
def list_tasks():
    settings = current_user.settings

    # Check if we should save the current filters
    if request.args.get('save_filters'):
        try:
            current_filters = {
                'status': request.args.get('status'),
                'due_date': request.args.get('due_date'),
                'lead_search': request.args.get('lead_search'),
                'date_from': request.args.get('date_from'),
                'date_to': request.args.get('date_to')
            }

            if settings:
                if not hasattr(settings, 'filter_preferences'):
                    settings.filter_preferences = '{}'
                filters = json.loads(settings.filter_preferences)
                filters['tasks'] = current_filters
                settings.filter_preferences = json.dumps(filters)
                db.session.commit()
                flash('フィルター設定が保存されました。', 'success')
            else:
                flash('ユーザー設定が見つかりません。', 'error')

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving filter preferences: {str(e)}")
            flash('フィルター設定の保存中にエラーが発生しました。', 'error')

        return redirect(url_for('tasks.list_tasks'))

    # Load saved filters if no parameters are provided
    saved_filters = {}
    if settings and settings.filter_preferences:
        try:
            filters = json.loads(settings.filter_preferences)
            saved_filters = filters.get('tasks', {})
        except json.JSONDecodeError:
            current_app.logger.error("Error parsing saved filters")

    use_saved = not any(request.args.values())

    # Get filter parameters
    status = request.args.get('status') or (saved_filters.get('status') if use_saved else None)
    due_date = request.args.get('due_date') or (saved_filters.get('due_date') if use_saved else None)
    lead_search = request.args.get('lead_search') or (saved_filters.get('lead_search') if use_saved else None)
    date_from = request.args.get('date_from') or (saved_filters.get('date_from') if use_saved else None)
    date_to = request.args.get('date_to') or (saved_filters.get('date_to') if use_saved else None)

    # Base query
    query = Task.query.filter_by(user_id=current_user.id)

    # Join Lead model if we need it for filtering
    if lead_search:
        query = query.join(Lead, Task.lead_id == Lead.id)

    # Apply filters
    if status:
        query = query.filter(Task.status == status)

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

    if lead_search:
        query = query.filter(Lead.name.ilike(f'%{lead_search}%'))

    if date_from:
        query = query.filter(Task.due_date >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Task.due_date <= datetime.strptime(date_to, '%Y-%m-%d'))

    # Get page number from request
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page

    # Order by due date descending and eager load lead relationship
    query = query.options(db.joinedload(Task.lead)).order_by(Task.due_date.desc())  # ここを変更

    # Paginate the results
    paginated_tasks = query.paginate(page=page, per_page=per_page, error_out=False)

    # Get task status counts
    status_counts = db.session.query(
        Task.status,
        func.count(Task.id).label('count')
    ).filter_by(user_id=current_user.id).group_by(Task.status).all()

    task_status_counts = [{'status': status, 'count': count} for status, count in status_counts]

    return render_template('tasks/list_tasks.html',
                         tasks=paginated_tasks.items,
                         pagination=paginated_tasks,
                         task_status_counts=task_status_counts,
                         ai_analysis=None,
                         filters={
                             'status': status,
                             'due_date': due_date,
                             'lead_search': lead_search,
                             'date_from': date_from,
                             'date_to': date_to
                         },
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
    form = TaskForm()
    leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.name).all()

    if request.method == 'POST':
        try:
            task = Task(
                title=request.form['title'],
                description=request.form['description'],
                due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d'),
                status=request.form['status'],
                completed='completed' in request.form,
                user_id=current_user.id,
                lead_id=request.form.get('lead_id') if request.form.get('lead_id') else None
            )

            db.session.add(task)
            db.session.commit()
            flash('新しいタスクが追加されました。', 'success')
            return redirect(url_for('tasks.list_tasks'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Task creation error: {str(e)}")
            flash('タスクの作成中にエラーが発生しました。', 'error')

    return render_template('tasks/create.html', form=form, leads=leads)

@tasks_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('このタスクを編集する権限がありません。', 'error')
        return redirect(url_for('tasks.list_tasks'))

    form = TaskForm(obj=task)
    leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.name).all()

    if request.method == 'POST':
        try:
            form = TaskForm(request.form)
            if form.validate():
                task.title = form.title.data
                task.description = form.description.data
                task.due_date = form.due_date.data
                task.status = form.status.data
                task.completed = 'completed' in request.form
                lead_id = request.form.get('lead_id')
                task.lead_id = int(lead_id) if lead_id else None

                db.session.commit()
                flash('タスクが更新されました。', 'success')
                return redirect(url_for('tasks.list_tasks'))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{getattr(form, field).label.text}: {error}', 'error')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Task update error: {str(e)}")
            flash('タスクの更新中にエラーが発生しました。', 'error')

    return render_template('tasks/edit.html', form=form, task=task, leads=leads)
    
@tasks_bp.route('/delete/<int:id>', methods=['POST', 'DELETE']) 
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

@tasks_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_tasks_endpoint():
    try:
        # Get current tasks for the user with filters applied
        query = Task.query.filter_by(user_id=current_user.id)

        # Apply filters if they exist
        status = request.args.get('status')
        if status:
            query = query.filter(Task.status == status)

        due_date_filter = request.args.get('due_date')
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if due_date_filter == 'today':
            query = query.filter(Task.due_date >= today, 
                               Task.due_date < today + timedelta(days=1))
        elif due_date_filter == 'week':
            query = query.filter(Task.due_date >= today,
                               Task.due_date < today + timedelta(days=7))
        elif due_date_filter == 'month':
            query = query.filter(Task.due_date >= today,
                               Task.due_date < today + timedelta(days=30))
        elif due_date_filter == 'overdue':
            query = query.filter(Task.due_date < today)

        lead_search = request.args.get('lead_search')
        if lead_search:
            query = query.join(Lead, Task.lead_id == Lead.id).filter(Lead.name.ilike(f'%{lead_search}%'))

        date_from = request.args.get('date_from')
        if date_from:
            query = query.filter(Task.due_date >= datetime.strptime(date_from, '%Y-%m-%d'))

        date_to = request.args.get('date_to')
        if date_to:
            query = query.filter(Task.due_date <= datetime.strptime(date_to, '%Y-%m-%d'))

        # Get tasks
        tasks = query.all()

        # Get task status counts for statistics
        status_counts = db.session.query(
            Task.status,
            func.count(Task.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Task.status).all()

        # Format status counts
        task_status_counts = [
            {'status': status, 'count': count}
            for status, count in status_counts
        ]

        # Get AI analysis
        ai_analysis = analyze_tasks(tasks)

        return jsonify({
            'success': True,
            'status_counts': task_status_counts,
            'ai_analysis': ai_analysis
        })

    except Exception as e:
        current_app.logger.error(f"Task analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'タスクの分析中にエラーが発生しました'
        }), 500