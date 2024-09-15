from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Account
from forms import AccountForm

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
        account = Account(name=form.name.data, industry=form.industry.data, website=form.website.data, user_id=current_user.id)
        db.session.add(account)
        db.session.commit()
        flash('Account created successfully')
        return redirect(url_for('accounts.list_accounts'))
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
        form.populate_obj(account)
        db.session.commit()
        flash('Account updated successfully')
        return redirect(url_for('accounts.account_detail', id=account.id))
    return render_template('accounts/create.html', form=form)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_account(id):
    account = Account.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    flash('Account deleted successfully')
    return redirect(url_for('accounts.list_accounts'))
