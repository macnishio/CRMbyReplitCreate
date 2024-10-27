from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Opportunity, Lead, Account
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
    
    # Get leads and accounts for the current user for the dropdown
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    
    # Update the choices for lead and account dropdowns
    form.lead.choices = [(str(lead.id), f"{lead.name} ({lead.email})") for lead in leads]
    form.account.choices = [(str(account.id), account.name) for account in accounts]
    
    # Add empty choice
    form.lead.choices.insert(0, ('', '選択してください'))
    form.account.choices.insert(0, ('', '選択してください'))

    if form.validate_on_submit():
        try:
            opportunity = Opportunity(
                name=form.name.data,
                amount=form.amount.data,
                stage=form.stage.data,
                close_date=form.close_date.data,
                user_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            # Set lead and account if selected
            if form.lead.data:
                opportunity.lead_id = int(form.lead.data)
            if form.account.data:
                opportunity.account_id = int(form.account.data)
                
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
    
    # Get leads and accounts for the current user for the dropdown
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    
    # Update the choices for lead and account dropdowns
    form.lead.choices = [(str(lead.id), f"{lead.name} ({lead.email})") for lead in leads]
    form.account.choices = [(str(account.id), account.name) for account in accounts]
    
    # Add empty choice
    form.lead.choices.insert(0, ('', '選択してください'))
    form.account.choices.insert(0, ('', '選択してください'))

    if form.validate_on_submit():
        try:
            # Update basic fields
            opportunity.name = form.name.data
            opportunity.amount = form.amount.data
            opportunity.stage = form.stage.data
            opportunity.close_date = form.close_date.data
            
            # Update relationships
            if form.lead.data:
                opportunity.lead_id = int(form.lead.data)
            else:
                opportunity.lead_id = None
                
            if form.account.data:
                opportunity.account_id = int(form.account.data)
            else:
                opportunity.account_id = None
            
            db.session.commit()
            flash('商談が正常に更新されました。', 'success')
            return redirect(url_for('opportunities.list_opportunities'))
            
        except Exception as e:
            db.session.rollback()
            flash('商談の更新中にエラーが発生しました。', 'error')
    
    # Set initial values for lead and account if they exist
    if opportunity.lead_id:
        form.lead.data = str(opportunity.lead_id)
    if opportunity.account_id:
        form.account.data = str(opportunity.account_id)
            
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
