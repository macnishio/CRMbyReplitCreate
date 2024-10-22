from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Lead
from extensions import db
from datetime import datetime

bp = Blueprint('leads', __name__)

@bp.route('/leads')
@login_required
def list_leads():
    leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.last_contact.desc()).all()
    return render_template('leads/list_leads.html', leads=leads)

@bp.route('/leads/add', methods=['GET', 'POST'])
@login_required
def add_lead():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        new_lead = Lead(name=name, email=email, user_id=current_user.id, last_contact=datetime.utcnow())
        db.session.add(new_lead)
        db.session.commit()
        flash('新しいリードが追加されました。', 'success')
        return redirect(url_for('leads.list_leads'))
    return render_template('leads/add_lead.html')

@bp.route('/leads/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_lead(id):
    lead = Lead.query.get_or_404(id)
    if lead.user_id != current_user.id:
        flash('このリードを編集する権限がありません。', 'error')
        return redirect(url_for('leads.list_leads'))
    if request.method == 'POST':
        lead.name = request.form['name']
        lead.email = request.form['email']
        lead.status = request.form['status']
        lead.score = float(request.form['score'])
        lead.last_contact = datetime.utcnow()
        db.session.commit()
        flash('リードが更新されました。', 'success')
        return redirect(url_for('leads.list_leads'))
    return render_template('leads/edit_lead.html', lead=lead)

@bp.route('/leads/delete/<int:id>')
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
