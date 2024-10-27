from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Lead, Email
from extensions import db
from datetime import datetime
from sqlalchemy import func
from ai_analysis import analyze_leads

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
    
    # Apply filters
    status = request.args.get('status')
    if status:
        query = query.filter(Lead.status == status)
    
    min_score = request.args.get('min_score')
    if min_score and min_score.isdigit():
        query = query.filter(Lead.score >= float(min_score))
    
    # Order by last contact date
    leads = query.order_by(Lead.last_contact.desc().nullslast(), Lead.created_at.desc()).all()
    
    return render_template('leads/list_leads.html', leads=leads)

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
    if request.method == 'POST':
        lead = Lead(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone'],
            status=request.form['status'],
            score=float(request.form['score']) if request.form['score'] else 0.0,
            user_id=current_user.id
        )
        db.session.add(lead)
        db.session.commit()
        flash('リードが追加されました。', 'success')
        return redirect(url_for('leads.list_leads'))
    return render_template('leads/create.html')

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
