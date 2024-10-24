from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Opportunity, Lead
from extensions import db
from datetime import datetime
from sqlalchemy import func
from ai_analysis import analyze_opportunities

bp = Blueprint('opportunities', __name__)

@bp.route('/')
@bp.route('')
@login_required
def list_opportunities():
    opportunities = Opportunity.query.filter_by(user_id=current_user.id).options(db.joinedload(Opportunity.lead)).order_by(Opportunity.close_date.asc()).all()
    
    # Get stage counts and total amount
    stage_stats = db.session.query(
        Opportunity.stage,
        func.count(Opportunity.id).label('count'),
        func.sum(Opportunity.amount).label('amount')
    ).filter_by(user_id=current_user.id).group_by(Opportunity.stage).all()
    
    opp_stage_stats = [
        {'stage': stage, 'count': count, 'amount': amount}
        for stage, count, amount in stage_stats
    ]
    
    # Get AI analysis
    ai_analysis = analyze_opportunities(opportunities)
    
    return render_template('opportunities/list_opportunities.html',
                         opportunities=opportunities,
                         opp_stage_stats=opp_stage_stats,
                         ai_analysis=ai_analysis)

@bp.route('/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    action = request.form.get('action')
    selected_opportunities = request.form.getlist('selected_opportunities[]')
    
    if not action or not selected_opportunities:
        flash('操作と商談を選択してください。', 'error')
        return redirect(url_for('opportunities.list_opportunities'))
    
    try:
        opportunities = Opportunity.query.filter(
            Opportunity.id.in_(selected_opportunities),
            Opportunity.user_id == current_user.id
        ).all()
        
        if action == 'delete':
            for opportunity in opportunities:
                db.session.delete(opportunity)
            flash(f'{len(opportunities)}件の商談を削除しました。', 'success')
            
        elif action == 'change_stage':
            new_stage = request.form.get('new_stage')
            if new_stage:
                for opportunity in opportunities:
                    opportunity.stage = new_stage
                flash(f'{len(opportunities)}件の商談のステージを変更しました。', 'success')
            else:
                flash('新しいステージを選択してください。', 'error')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash('操作中にエラーが発生しました。', 'error')
        current_app.logger.error(f"Bulk action error: {str(e)}")
    
    return redirect(url_for('opportunities.list_opportunities'))

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_opportunity():
    if request.method == 'POST':
        name = request.form['name']
        stage = request.form['stage']
        amount = float(request.form['amount']) if request.form['amount'] else None
        close_date = datetime.strptime(request.form['close_date'], '%Y-%m-%d') if request.form['close_date'] else None
        lead_id = request.form.get('lead_id')
        
        opportunity = Opportunity(
            name=name,
            stage=stage,
            amount=amount,
            close_date=close_date,
            user_id=current_user.id,
            lead_id=lead_id
        )
        
        db.session.add(opportunity)
        db.session.commit()
        flash('商談が追加されました。', 'success')
        return redirect(url_for('opportunities.list_opportunities'))
    
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    return render_template('opportunities/add_opportunity.html', leads=leads)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_opportunity(id):
    opportunity = Opportunity.query.get_or_404(id)
    if opportunity.user_id != current_user.id:
        flash('この商談を編集する権限がありません。', 'error')
        return redirect(url_for('opportunities.list_opportunities'))
    
    if request.method == 'POST':
        opportunity.name = request.form['name']
        opportunity.stage = request.form['stage']
        opportunity.amount = float(request.form['amount']) if request.form['amount'] else None
        opportunity.close_date = datetime.strptime(request.form['close_date'], '%Y-%m-%d') if request.form['close_date'] else None
        opportunity.lead_id = request.form.get('lead_id')
        
        db.session.commit()
        flash('商談が更新されました。', 'success')
        return redirect(url_for('opportunities.list_opportunities'))
    
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    return render_template('opportunities/edit_opportunity.html', opportunity=opportunity, leads=leads)

@bp.route('/delete/<int:id>', methods=['POST'])
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
