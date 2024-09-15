from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Opportunity, Account
from forms import OpportunityForm

bp = Blueprint('opportunities', __name__, url_prefix='/opportunities')

@bp.route('/')
@login_required
def list_opportunities():
    opportunities = Opportunity.query.filter_by(user_id=current_user.id).all()
    return render_template('opportunities/list.html', opportunities=opportunities)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_opportunity():
    form = OpportunityForm()
    form.account.choices = [(a.id, a.name) for a in Account.query.filter_by(user_id=current_user.id).all()]
    if form.validate_on_submit():
        opportunity = Opportunity(
            name=form.name.data,
            amount=form.amount.data,
            stage=form.stage.data,
            close_date=form.close_date.data,
            account_id=form.account.data,
            user_id=current_user.id
        )
        db.session.add(opportunity)
        db.session.commit()
        flash('Opportunity created successfully')
        return redirect(url_for('opportunities.list_opportunities'))
    return render_template('opportunities/create.html', form=form)

@bp.route('/<int:id>')
@login_required
def opportunity_detail(id):
    opportunity = Opportunity.query.get_or_404(id)
    return render_template('opportunities/detail.html', opportunity=opportunity)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_opportunity(id):
    opportunity = Opportunity.query.get_or_404(id)
    form = OpportunityForm(obj=opportunity)
    form.account.choices = [(a.id, a.name) for a in Account.query.filter_by(user_id=current_user.id).all()]
    if form.validate_on_submit():
        form.populate_obj(opportunity)
        db.session.commit()
        flash('Opportunity updated successfully')
        return redirect(url_for('opportunities.opportunity_detail', id=opportunity.id))
    return render_template('opportunities/create.html', form=form)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_opportunity(id):
    opportunity = Opportunity.query.get_or_404(id)
    db.session.delete(opportunity)
    db.session.commit()
    flash('Opportunity deleted successfully')
    return redirect(url_for('opportunities.list_opportunities'))
