from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Opportunity, Account, Lead
from extensions import db
from forms import OpportunityForm
from datetime import datetime

bp = Blueprint('opportunities', __name__)

@bp.route('/')
@login_required
def list_opportunities():
    opportunities = Opportunity.query.filter_by(user_id=current_user.id).order_by(Opportunity.created_at.desc()).all()
    return render_template('opportunities/list_opportunities.html', opportunities=opportunities)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_opportunity():
    form = OpportunityForm()
    
    # Get accounts and leads for the current user
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    
    # Update form choices with string IDs
    form.account.choices = [('0', '-- 選択してください --')] + [(str(a.id), a.name) for a in accounts]
    form.lead.choices = [('0', '-- 選択してください --')] + [(str(l.id), l.name) for l in leads]
    
    if form.validate_on_submit():
        try:
            opportunity = Opportunity(
                name=form.name.data,
                amount=form.amount.data,
                stage=form.stage.data,
                close_date=form.close_date.data,
                account_id=int(form.account.data) if form.account.data != '0' else None,
                lead_id=int(form.lead.data) if form.lead.data != '0' else None,
                user_id=current_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(opportunity)
            db.session.commit()
            flash('商談が正常に追加されました。', 'success')
            return redirect(url_for('opportunities.list_opportunities'))
        except Exception as e:
            db.session.rollback()
            flash('商談の追加中にエラーが発生しました。', 'error')
            
    return render_template('opportunities/add_opportunity.html', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_opportunity(id):
    opportunity = Opportunity.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = OpportunityForm(obj=opportunity)
    
    # Get accounts and leads for the current user
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    
    # Update form choices with string IDs
    form.account.choices = [('0', '-- 選択してください --')] + [(str(a.id), a.name) for a in accounts]
    form.lead.choices = [('0', '-- 選択してください --')] + [(str(l.id), l.name) for l in leads]
    
    if form.validate_on_submit():
        try:
            form.populate_obj(opportunity)
            opportunity.account_id = int(form.account.data) if form.account.data != '0' else None
            opportunity.lead_id = int(form.lead.data) if form.lead.data != '0' else None
            db.session.commit()
            flash('商談が正常に更新されました。', 'success')
            return redirect(url_for('opportunities.list_opportunities'))
        except Exception as e:
            db.session.rollback()
            flash('商談の更新中にエラーが発生しました。', 'error')
            
    return render_template('opportunities/edit_opportunity.html', form=form, opportunity=opportunity)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_opportunity(id):
    opportunity = Opportunity.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        db.session.delete(opportunity)
        db.session.commit()
        flash('商談が正常に削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('商談の削除中にエラーが発生しました。', 'error')
    return redirect(url_for('opportunities.list_opportunities'))
