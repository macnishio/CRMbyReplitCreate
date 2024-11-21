from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Lead, Email, UserSettings
from extensions import db
import json
from datetime import datetime
from sqlalchemy import func
from ai_analysis import analyze_leads
from forms import LeadForm

bp = Blueprint('leads', __name__)

@bp.route('/update_empty_names')
@login_required
def update_empty_names():
    try:
        # Get leads with empty names and their latest emails
        empty_name_leads = Lead.query.filter(
            (Lead.name == '') | (Lead.name == None)
        ).all()
        
        updated_count = 0
        for lead in empty_name_leads:
            # Get the latest email for this lead
            latest_email = Email.query.filter_by(
                lead_id=lead.id
            ).order_by(Email.created_at.desc()).first()
            
            if latest_email and latest_email.sender_name:
                lead.name = latest_email.sender_name
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            flash(f'{updated_count}件のリード名を更新しました。', 'success')
        else:
            flash('更新が必要なリードはありませんでした。', 'info')
            
    except Exception as e:
        current_app.logger.error(f"Error updating lead names: {str(e)}")
        db.session.rollback()
        flash('リード名の更新中にエラーが発生しました。', 'error')
        
    return redirect(url_for('leads.list_leads'))

@bp.route('/')
@bp.route('')
@login_required
def list_leads():
    query = Lead.query.filter_by(user_id=current_user.id)
    
    # Get filter preferences from UserSettings
    user_settings = current_user.settings
    if user_settings and user_settings.filter_preferences:
        try:
            saved_filters = json.loads(user_settings.filter_preferences).get('leads', {})
        except json.JSONDecodeError:
            saved_filters = {}
    else:
        saved_filters = {}

    # Advanced filter combinations
    filter_groups = json.loads(request.args.get('filter_groups', '[]'))
    if filter_groups:
        # Process each filter group
        group_conditions = []
        for group in filter_groups:
            group_operator = group.get('operator', 'AND')
            conditions = []
            
            for condition in group.get('conditions', []):
                field = condition.get('field')
                operator = condition.get('operator')
                value = condition.get('value')
                
                if not all([field, operator, value]):
                    continue

                # Handle Japanese text properly
                if isinstance(value, str):
                    value = value.strip()
                    
                if field == 'name':
                    if operator == 'contains':
                        conditions.append(Lead.name.ilike(f'%{value}%'))
                    elif operator == 'equals':
                        conditions.append(Lead.name == value)
                    elif operator == 'starts_with':
                        conditions.append(Lead.name.ilike(f'{value}%'))
                    elif operator == 'ends_with':
                        conditions.append(Lead.name.ilike(f'%{value}'))
                elif field == 'email':
                    if operator == 'contains':
                        conditions.append(Lead.email.ilike(f'%{value}%'))
                    elif operator == 'equals':
                        conditions.append(Lead.email == value)
                    elif operator == 'starts_with':
                        conditions.append(Lead.email.ilike(f'{value}%'))
                    elif operator == 'ends_with':
                        conditions.append(Lead.email.ilike(f'%{value}'))
                elif field == 'score':
                    try:
                        score_value = float(value)
                        if operator == 'greater_than':
                            conditions.append(Lead.score > score_value)
                        elif operator == 'less_than':
                            conditions.append(Lead.score < score_value)
                        elif operator == 'equals':
                            conditions.append(Lead.score == score_value)
                        elif operator == 'greater_equal':
                            conditions.append(Lead.score >= score_value)
                        elif operator == 'less_equal':
                            conditions.append(Lead.score <= score_value)
                    except ValueError:
                        continue
                elif field == 'status':
                    if operator == 'equals':
                        conditions.append(Lead.status == value)
                    elif operator == 'not_equals':
                        conditions.append(Lead.status != value)
                        
            if conditions:
                if group_operator == 'OR':
                    group_conditions.append(db.or_(*conditions))
                else:  # AND
                    group_conditions.append(db.and_(*conditions))
        
        if group_conditions:
            query = query.filter(db.and_(*group_conditions))
    else:  # Fall back to basic search
        search_name = request.args.get('search_name', '').strip()
        search_email = request.args.get('search_email', '').strip()
        search_operator = request.args.get('search_operator', 'AND')
        
        if search_name or search_email:
            name_filter = Lead.name.ilike(f'%{search_name}%') if search_name else None
            email_filter = Lead.email.ilike(f'%{search_email}%') if search_email else None
            
            if search_operator == 'OR':
                if name_filter and email_filter:
                    query = query.filter(db.or_(name_filter, email_filter))
                elif name_filter:
                    query = query.filter(name_filter)
                elif email_filter:
                    query = query.filter(email_filter)
            else:  # AND
                if name_filter:
                    query = query.filter(name_filter)
                if email_filter:
                    query = query.filter(email_filter)
        for group in filter_groups:
            group_operator = group.get('operator', 'AND')
            conditions = []
            
            for condition in group.get('conditions', []):
                field = condition.get('field')
                operator = condition.get('operator')
                value = condition.get('value')
                
                if not all([field, operator, value]):
                    continue
                    
                if field == 'name':
                    if operator == 'contains':
                        conditions.append(Lead.name.ilike(f'%{value}%'))
                    elif operator == 'equals':
                        conditions.append(Lead.name == value)
                elif field == 'email':
                    if operator == 'contains':
                        conditions.append(Lead.email.ilike(f'%{value}%'))
                    elif operator == 'equals':
                        conditions.append(Lead.email == value)
                elif field == 'score':
                    try:
                        score_value = float(value)
                        if operator == 'greater_than':
                            conditions.append(Lead.score > score_value)
                        elif operator == 'less_than':
                            conditions.append(Lead.score < score_value)
                        elif operator == 'equals':
                            conditions.append(Lead.score == score_value)
                    except ValueError:
                        continue
                        
            if conditions:
                if group_operator == 'OR':
                    group_conditions.append(db.or_(*conditions))
                else:
                    group_conditions.append(db.and_(*conditions))
        
        if group_conditions:
            query = query.filter(db.and_(*group_conditions))
    
    # Apply status filters
    statuses = request.args.getlist('status')
    if statuses:
        query = query.filter(Lead.status.in_(statuses))
    
    # Apply score range filter
    min_score = request.args.get('min_score')
    max_score = request.args.get('max_score')
    if min_score and min_score.isdigit():
        query = query.filter(Lead.score >= float(min_score))
    if max_score and max_score.isdigit():
        query = query.filter(Lead.score <= float(max_score))
    
    # Apply date filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date_field = request.args.get('date_field', 'created_at')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            if date_field == 'last_contact':
                query = query.filter(Lead.last_contact >= date_from)
            else:
                query = query.filter(Lead.created_at >= date_from)
        except ValueError:
            flash('Invalid date format for Date From', 'error')
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            if date_field == 'last_contact':
                query = query.filter(Lead.last_contact <= date_to)
            else:
                query = query.filter(Lead.created_at <= date_to)
        except ValueError:
            flash('Invalid date format for Date To', 'error')
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'last_contact')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_by == 'name':
        sort_field = Lead.name
    elif sort_by == 'email':
        sort_field = Lead.email
    elif sort_by == 'score':
        sort_field = Lead.score
    elif sort_by == 'created_at':
        sort_field = Lead.created_at
    else:
        sort_field = Lead.last_contact
    
    if sort_order == 'asc':
        query = query.order_by(sort_field.asc().nullslast())
    else:
        query = query.order_by(sort_field.desc().nullslast())
    
    # Save current filters if requested
    if request.args.get('save_filters'):
        current_filters = {
            'search_name': search_name,
            'search_email': search_email,
            'search_operator': search_operator,
            'statuses': statuses,
            'min_score': min_score,
            'max_score': max_score,
            'date_from': date_from.strftime('%Y-%m-%d') if isinstance(date_from, datetime) else date_from,
            'date_to': date_to.strftime('%Y-%m-%d') if isinstance(date_to, datetime) else date_to,
            'date_field': date_field,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        if not user_settings:
            user_settings = UserSettings(user_id=current_user.id)
            db.session.add(user_settings)
        
        saved_filters = json.loads(user_settings.filter_preferences) if user_settings.filter_preferences else {}
        saved_filters['leads'] = current_filters
        user_settings.filter_preferences = json.dumps(saved_filters)
        db.session.commit()
        flash('Filter preferences saved successfully', 'success')
    
    leads = query.all()
    return render_template('leads/list_leads.html', leads=leads, saved_filters=saved_filters)

@bp.route('/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    action = request.form.get('action')
    selected_leads = request.form.getlist('selected_leads[]')
    
    if not action or not selected_leads:
        flash('操作とリードを選択してください。', 'error')
        return redirect(url_for('leads.list_leads'))
    
    try:
        leads = Lead.query.filter(
            Lead.id.in_(selected_leads),
            Lead.user_id == current_user.id
        ).all()
        
        if action == 'delete':
            for lead in leads:
                db.session.delete(lead)
            flash(f'{len(leads)}件のリードを削除しました。', 'success')
            
        elif action == 'change_status':
            new_status = request.form.get('new_status')
            if new_status:
                for lead in leads:
                    lead.status = new_status
                flash(f'{len(leads)}件のリードのステータスを変更しました。', 'success')
            else:
                flash('新しいステータスを選択してください。', 'error')
                
        elif action == 'update_score':
            new_score = request.form.get('new_score')
            if new_score and new_score.isdigit():
                score = float(new_score)
                if 0 <= score <= 100:
                    for lead in leads:
                        lead.score = score
                    flash(f'{len(leads)}件のリードのスコアを更新しました。', 'success')
                else:
                    flash('スコアは0から100の間で指定してください。', 'error')
            else:
                flash('有効なスコアを入力してください。', 'error')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash('操作中にエラーが発生しました。', 'error')
        current_app.logger.error(f"Bulk action error: {str(e)}")
    
    return redirect(url_for('leads.list_leads'))

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_lead():
    form = LeadForm()  # フォームのインスタンスを作成
    if form.validate_on_submit():  # POSTリクエストとバリデーションチェック
        lead = Lead(
            name=form.name.data,  # request.form[] の代わりに form.name.data を使用
            email=form.email.data,
            phone=form.phone.data,
            status=form.status.data,
            score=form.score.data if form.score.data is not None else 0.0,
            user_id=current_user.id
        )
        db.session.add(lead)
        db.session.commit()
        flash('リードが追加されました。', 'success')
        return redirect(url_for('leads.list_leads'))
    return render_template('leads/create.html', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_lead(id):
    lead = Lead.query.get_or_404(id)
    if lead.user_id != current_user.id:
        flash('このリードを編集する権限がありません。', 'error')
        return redirect(url_for('leads.list_leads'))
    
    if request.method == 'POST':
        lead.name = request.form['name']
        lead.email = request.form['email']
        lead.phone = request.form['phone']
        lead.status = request.form['status']
        lead.score = float(request.form['score']) if request.form['score'] else 0.0
        db.session.commit()
        flash('リードが更新されました。', 'success')
        return redirect(url_for('leads.list_leads'))
    return render_template('leads/edit_lead.html', lead=lead)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_lead(id):
    lead = Lead.query.get_or_404(id)
    if lead.user_id != current_user.id:
        flash('このリードを削除する権限がありません。', 'error')
        return redirect(url_for('leads.list_leads'))
    
    db.session.delete(lead)
    db.session.commit()
    flash('リードが削除されました。', 'success')
    return redirect(url_for('leads.list_leads'))
