from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Opportunity
from extensions import db
from datetime import datetime

bp = Blueprint('opportunities', __name__)

@bp.route('/opportunities')
@login_required
def list_opportunities():
    opportunities = Opportunity.query.filter_by(user_id=current_user.id).order_by(Opportunity.close_date.asc()).all()
    return render_template('opportunities/list_opportunities.html', opportunities=opportunities)

@bp.route('/opportunities/add', methods=['GET', 'POST'])
@login_required
def add_opportunity():
    if request.method == 'POST':
        name = request.form['name']
        stage = request.form['stage']
        amount = float(request.form['amount'])
        close_date = datetime.strptime(request.form['close_date'], '%Y-%m-%d')
        new_opportunity = Opportunity(name=name, stage=stage, amount=amount, close_date=close_date, user_id=current_user.id)
        db.session.add(new_opportunity)
        db.session.commit()
        flash('新しい商談が追加されました。', 'success')
        return redirect(url_for('opportunities.list_opportunities'))
    return render_template('opportunities/add_opportunity.html')

@bp.route('/opportunities/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_opportunity(id):
    opportunity = Opportunity.query.get_or_404(id)
    if opportunity.user_id != current_user.id:
        flash('この商談を編集する権限がありません。', 'error')
        return redirect(url_for('opportunities.list_opportunities'))
    if request.method == 'POST':
        opportunity.name = request.form['name']
        opportunity.stage = request.form['stage']
        opportunity.amount = float(request.form['amount'])
        opportunity.close_date = datetime.strptime(request.form['close_date'], '%Y-%m-%d')
        db.session.commit()
        flash('商談が更新されました。', 'success')
        return redirect(url_for('opportunities.list_opportunities'))
    return render_template('opportunities/edit_opportunity.html', opportunity=opportunity)

@bp.route('/opportunities/delete/<int:id>')
@login_required
def delete_opportunity(id):
    opportunity = Opportunity.query.get_or_404(id)
    if opportunity.user_id != current_user.id:
        flash('この商談を削除する権限がありません。', 'error')
        return redirect(url_for('opportunities.list_opportunities'))
    db.session.delete(opportunity)
    db.session.commit()
    flash('商談が削除されました。', 'success')
    return redirect(url_for('opportunities.list_opportunities'))
