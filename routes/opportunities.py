from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Opportunity, Account
from forms import OpportunityForm
import traceback

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
        try:
            current_app.logger.info(f"Attempting to create opportunity: {form.name.data}")
            current_app.logger.info(f"Form data: {form.data}")
            opportunity = Opportunity(
                name=form.name.data,
                amount=form.amount.data,
                stage=form.stage.data,
                close_date=form.close_date.data,
                account_id=form.account.data,
                user_id=current_user.id,
                lead_id=None  # Set to None by default
            )
            current_app.logger.info(f"Opportunity object created: {opportunity.__dict__}")
            db.session.add(opportunity)
            current_app.logger.info("Opportunity added to session")
            db.session.commit()
            current_app.logger.info("Opportunity committed to database")
            flash('Opportunity created successfully')
            return redirect(url_for('opportunities.list_opportunities'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Opportunity creation error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash('An error occurred while creating the opportunity. Please try again.')
    else:
        current_app.logger.info(f"Form validation failed: {form.errors}")
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
        try:
            form.populate_obj(opportunity)
            db.session.commit()
            flash('Opportunity updated successfully')
            return redirect(url_for('opportunities.opportunity_detail', id=opportunity.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Opportunity update error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash('An error occurred while updating the opportunity. Please try again.')
    return render_template('opportunities/create.html', form=form)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_opportunity(id):
    opportunity = Opportunity.query.get_or_404(id)
    try:
        db.session.delete(opportunity)
        db.session.commit()
        flash('Opportunity deleted successfully')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Opportunity deletion error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash('An error occurred while deleting the opportunity. Please try again.')
    return redirect(url_for('opportunities.list_opportunities'))
