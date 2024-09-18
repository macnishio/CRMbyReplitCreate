from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Account
from forms import AccountForm
import traceback

bp = Blueprint('accounts', __name__, url_prefix='/accounts')

@bp.route('/')
@login_required
def list_accounts():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('accounts/list.html', accounts=accounts)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_account():
    form = AccountForm()
    if form.validate_on_submit():
        try:
            account = Account(name=form.name.data, industry=form.industry.data, website=form.website.data, user_id=current_user.id)
            db.session.add(account)
            db.session.commit()
            flash('Account created successfully')
            return redirect(url_for('accounts.list_accounts'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Account creation error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash('An error occurred while creating the account. Please try again.')
    return render_template('accounts/create.html', form=form)

@bp.route('/<int:id>')
@login_required
def account_detail(id):
    account = Account.query.get_or_404(id)
    return render_template('accounts/detail.html', account=account)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_account(id):
    account = Account.query.get_or_404(id)
    form = AccountForm(obj=account)
    if form.validate_on_submit():
        try:
            form.populate_obj(account)
            db.session.commit()
            flash('Account updated successfully')
            return redirect(url_for('accounts.account_detail', id=account.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Account update error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash('An error occurred while updating the account. Please try again.')
    return render_template('accounts/create.html', form=form)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_account(id):
    account = Account.query.get_or_404(id)
    try:
        db.session.delete(account)
        db.session.commit()
        flash('Account deleted successfully')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Account deletion error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash('An error occurred while deleting the account. Please try again.')
    return redirect(url_for('accounts.list_accounts'))
