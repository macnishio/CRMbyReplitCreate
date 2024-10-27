from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Lead
from extensions import db
from forms import LeadForm
from datetime import datetime

bp = Blueprint('leads', __name__)

@bp.route('/')
@login_required
def list_leads():
    leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.created_at.desc()).all()
    return render_template('leads/list_leads.html', leads=leads)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_lead():
    form = LeadForm()
    if form.validate_on_submit():
        try:
            lead = Lead(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                status=form.status.data,
                score=form.score.data or 0.0,
                user_id=current_user.id,
                created_at=datetime.utcnow(),
                last_contact=datetime.utcnow()
            )
            db.session.add(lead)
            db.session.commit()
            flash('リードが正常に追加されました。', 'success')
            return redirect(url_for('leads.list_leads'))
        except Exception as e:
            db.session.rollback()
            flash('リードの追加中にエラーが発生しました。', 'error')
    return render_template('leads/add_lead.html', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_lead(id):
    lead = Lead.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = LeadForm(obj=lead)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(lead)
            db.session.commit()
            flash('リードが正常に更新されました。', 'success')
            return redirect(url_for('leads.list_leads'))
        except Exception as e:
            db.session.rollback()
            flash('リードの更新中にエラーが発生しました。', 'error')
            
    return render_template('leads/edit_lead.html', form=form, lead=lead)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_lead(id):
    lead = Lead.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        db.session.delete(lead)
        db.session.commit()
        flash('リードが正常に削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('リードの削除中にエラーが発生しました。', 'error')
    return redirect(url_for('leads.list_leads'))
    
@bp.route('/update-empty-names', methods=['POST'])
@login_required
def update_empty_names():
    try:
        # Get all leads with empty names for current user
        leads = Lead.query.filter_by(
            user_id=current_user.id
        ).filter(
            (Lead.name == '') | (Lead.name == None)
        ).all()

        # Update empty names with email addresses
        updated_count = 0
        for lead in leads:
            if lead.email and not lead.name:
                lead.name = lead.email.split('@')[0]  # Use part before @ as name
                updated_count += 1

        if updated_count > 0:
            db.session.commit()
            flash(f'{updated_count}件のリードの名前を更新しました。', 'success')
        else:
            flash('更新が必要な空の名前はありませんでした。',