from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from models import Opportunity, Lead
from extensions import db
import csv
from io import StringIO, BytesIO
from datetime import datetime
from sqlalchemy import func
from ai_analysis import analyze_opportunities
from forms import OpportunityForm

bp = Blueprint('opportunities', __name__)

@bp.route('/')
@bp.route('')
@login_required
def list_opportunities():
    settings = current_user.settings

    # Check if we should save the current filters
    if request.args.get('save_filters'):
        try:
            # Get all filter parameters with proper type conversion
            min_amount = request.args.get('min_amount')
            max_amount = request.args.get('max_amount')
            
            # Convert amount strings to float if they exist
            try:
                min_amount = float(min_amount) if min_amount else None
            except ValueError:
                min_amount = None
                
            try:
                max_amount = float(max_amount) if max_amount else None
            except ValueError:
                max_amount = None
                
            current_filters = {
                'stage': request.args.get('stage'),
                'min_amount': min_amount,
                'max_amount': max_amount,
                'lead_search': request.args.get('lead_search'),
                'lead_status': request.args.get('lead_status'),
                'date_from': request.args.get('date_from'),
                'date_to': request.args.get('date_to'),
                'sort_by': request.args.get('sort_by', 'close_date'),
                'sort_order': request.args.get('sort_order', 'asc')
            }
            
            if settings:
                settings.opportunity_filters = current_filters
                db.session.commit()
                flash('フィルター設定が保存されました。', 'success')
            else:
                # Create new settings if they don't exist
                settings = UserSettings(
                    user_id=current_user.id,
                    filter_preferences=json.dumps({'opportunities': current_filters})
                )
                db.session.add(settings)
                db.session.commit()
                flash('フィルター設定が作成されました。', 'success')
                
        except Exception as e:
            current_app.logger.error(f"Error saving filter preferences: {str(e)}")
            db.session.rollback()
            flash('フィルター設定の保存中にエラーが発生しました。', 'error')
            
        return redirect(url_for('opportunities.list_opportunities'))

    # Load saved filters if no parameters are provided
    saved_filters = settings.opportunity_filters if settings else {}
    use_saved = not any(request.args.values())

    # Get filter parameters with proper error handling
    stage_filter = request.args.get('stage') or (saved_filters.get('stage') if use_saved else None)
    
    # Handle numeric filters with safe conversion
    try:
        min_amount = request.args.get('min_amount', type=float) or (
            float(saved_filters.get('min_amount')) if use_saved and saved_filters.get('min_amount') else None
        )
    except (ValueError, TypeError):
        min_amount = None
        
    try:
        max_amount = request.args.get('max_amount', type=float) or (
            float(saved_filters.get('max_amount')) if use_saved and saved_filters.get('max_amount') else None
        )
    except (ValueError, TypeError):
        max_amount = None
        
    lead_search = request.args.get('lead_search') or (saved_filters.get('lead_search') if use_saved else None)
    lead_status = request.args.get('lead_status') or (saved_filters.get('lead_status') if use_saved else None)
    date_from = request.args.get('date_from') or (saved_filters.get('date_from') if use_saved else None)
    date_to = request.args.get('date_to') or (saved_filters.get('date_to') if use_saved else None)
    
    # Ensure we have valid sorting parameters
    valid_sort_columns = ['close_date', 'amount', 'name', 'stage']
    sort_by = request.args.get('sort_by')
    if not sort_by and use_saved:
        sort_by = saved_filters.get('sort_by')
    if not sort_by or sort_by not in valid_sort_columns:
        sort_by = 'close_date'
        
    sort_order = request.args.get('sort_order')
    if not sort_order and use_saved:
        sort_order = saved_filters.get('sort_order')
    if not sort_order or sort_order not in ['asc', 'desc']:
        sort_order = 'asc'

    # Get page number from request
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page

    # Base query
    query = Opportunity.query.filter_by(user_id=current_user.id)

    # Join Lead model if we need it for filtering
    if lead_search or lead_status:
        query = query.join(Lead, Opportunity.lead_id == Lead.id)

    # Apply filters
    if stage_filter:
        query = query.filter(Opportunity.stage == stage_filter)
    if min_amount is not None:
        query = query.filter(Opportunity.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Opportunity.amount <= max_amount)
    if lead_search:
        query = query.filter(Lead.name.ilike(f'%{lead_search}%'))
    if lead_status:
        query = query.filter(Lead.status == lead_status)
    if date_from:
        query = query.filter(Opportunity.close_date >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Opportunity.close_date <= datetime.strptime(date_to, '%Y-%m-%d'))

    # Add eager loading of lead data after all filters
    query = query.options(db.joinedload(Opportunity.lead))

    # Apply sorting with safe column access
    sort_column = getattr(Opportunity, sort_by, Opportunity.close_date)
    if sort_order == 'desc':
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    # Paginate the results
    opportunities = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('opportunities/list_opportunities.html',
                         opportunities=opportunities,
                         filters={
                             'stage': stage_filter,
                             'min_amount': min_amount,
                             'max_amount': max_amount,
                             'lead_search': lead_search,
                             'date_from': date_from,
                             'date_to': date_to,
                             'sort_by': sort_by,
                             'sort_order': sort_order,
                              'lead_status': lead_status
                         })

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_opportunity():
    form = OpportunityForm()
    leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.name).all()

    if request.method == 'POST':
        try:
            opportunity = Opportunity(
                name=request.form['name'],
                stage=request.form['stage'],
                amount=float(request.form['amount']) if request.form['amount'] else None,
                close_date=datetime.strptime(request.form['close_date'], '%Y-%m-%d') if request.form['close_date'] else None,
                user_id=current_user.id,
                lead_id=request.form.get('lead_id') if request.form.get('lead_id') else None
            )

            db.session.add(opportunity)
            db.session.commit()
            flash('商談が追加されました。', 'success')
            return redirect(url_for('opportunities.list_opportunities'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Opportunity creation error: {str(e)}")
            flash('商談の作成中にエラーが発生しました。', 'error')

    return render_template('opportunities/edit.html', form=form, leads=leads, opportunity=None)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_opportunity(id):
    opportunity = Opportunity.query.get_or_404(id)
    if opportunity.user_id != current_user.id:
        flash('この商談を編集する権限がありません。', 'error')
        return redirect(url_for('opportunities.list_opportunities'))

    form = OpportunityForm(obj=opportunity)
    leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.name).all()

    if request.method == 'POST':
        try:
            opportunity.name = request.form['name']
            opportunity.stage = request.form['stage']
            opportunity.amount = float(request.form['amount']) if request.form['amount'] else None
            opportunity.close_date = datetime.strptime(request.form['close_date'], '%Y-%m-%d') if request.form['close_date'] else None
            opportunity.lead_id = request.form.get('lead_id') if request.form.get('lead_id') else None

            db.session.commit()
            flash('商談が更新されました。', 'success')
            return redirect(url_for('opportunities.list_opportunities'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Opportunity update error: {str(e)}")
            flash('商談の更新中にエラーが発生しました。', 'error')

    return render_template('opportunities/edit.html', form=form, opportunity=opportunity, leads=leads)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_opportunity(id):
    opportunity = Opportunity.query.get_or_404(id)
    if opportunity.user_id != current_user.id:
        flash('この商談を削除する権限がありません。', 'error')
        return redirect(url_for('opportunities.list_opportunities'))

    try:
        db.session.delete(opportunity)
        db.session.commit()
        flash('商談が削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Opportunity deletion error: {str(e)}")
        flash('商談の削除中にエラーが発生しました。', 'error')

    return redirect(url_for('opportunities.list_opportunities'))

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

@bp.route('/analyze', methods=['POST'])
@login_required
def analyze_opportunities_data():
    try:
        opportunities = Opportunity.query.filter_by(user_id=current_user.id).all()
        stage_stats = db.session.query(
            Opportunity.stage,
            func.count(Opportunity.id).label('count'),
            func.sum(Opportunity.amount).label('amount')
        ).filter_by(user_id=current_user.id).group_by(Opportunity.stage).all()

        opp_stage_stats = [
            {'stage': stage, 'count': count, 'amount': amount}
            for stage, count, amount in stage_stats
        ]

        ai_analysis = analyze_opportunities(opportunities)

        return {
            'success': True,
            'stage_stats': opp_stage_stats,
            'ai_analysis': ai_analysis
        }
    except Exception as e:
        current_app.logger.error(f"Analysis error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@bp.route('/export')
@login_required
def export_opportunities():
    """
    Export opportunities list as CSV with proper Japanese encoding support
    and error handling.
    """
    try:
        current_app.logger.info("Starting opportunities export")
        # Get filter parameters
        stage_filter = request.args.get('stage')
        min_amount = request.args.get('min_amount', type=float)
        max_amount = request.args.get('max_amount', type=float)
        lead_search = request.args.get('lead_search')
        lead_status = request.args.get('lead_status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        # Base query
        query = Opportunity.query.filter_by(user_id=current_user.id)

        # Join Lead model if we need it for filtering
        if lead_search or lead_status:
            query = query.join(Lead, Opportunity.lead_id == Lead.id)

        # Apply filters
        if stage_filter:
            query = query.filter(Opportunity.stage == stage_filter)
        if min_amount is not None:
            query = query.filter(Opportunity.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(Opportunity.amount <= max_amount)
        if lead_search:
            query = query.filter(Lead.name.ilike(f'%{lead_search}%'))
        if lead_status:
            query = query.filter(Lead.status == lead_status)
        if date_from:
            query = query.filter(Opportunity.close_date >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(Opportunity.close_date <= datetime.strptime(date_to, '%Y-%m-%d'))

        # Add eager loading of lead data
        query = query.options(db.joinedload(Opportunity.lead))

        # Get opportunities
        opportunities = query.all()

        # Create CSV file
        si = StringIO()
        writer = csv.writer(si)
        
        # Japanese headers with their corresponding translations
        headers = [
            '商談名', 'ステージ', '金額（円）', '完了予定日', 
            'リード名', 'リードメール', 'リードスコア', 'リードステータス',
            '作成日', '最終更新日'
        ]
        writer.writerow(headers)
        
        # Write data with proper Japanese stage translations
        stage_translations = {
            'Initial Contact': '初期接触',
            'Qualification': '資格確認',
            'Proposal': '提案',
            'Negotiation': '交渉',
            'Closed Won': '成約',
            'Closed Lost': '失注'
        }

        status_translations = {
            'New': '新規',
            'Contacted': '連絡済み',
            'Qualified': '適格',
            'Unqualified': '不適格',
            'Converted': '成約'
        }
        
        for opp in opportunities:
            try:
                row = [
                    opp.name,
                    stage_translations.get(opp.stage, opp.stage),
                    f"¥{opp.amount:,.0f}" if opp.amount else '',
                    opp.close_date.strftime('%Y-%m-%d') if opp.close_date else '',
                    opp.lead.name if opp.lead else '',
                    opp.lead.email if opp.lead else '',
                    f"{opp.lead.score:.1f}" if opp.lead and opp.lead.score else '',
                    status_translations.get(opp.lead.status, opp.lead.status) if opp.lead else '',
                    opp.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(opp, 'created_at') else '',
                    opp.updated_at.strftime('%Y-%m-%d %H:%M') if hasattr(opp, 'updated_at') else ''
                ]
                writer.writerow(row)
            except Exception as row_error:
                current_app.logger.error(f"Error writing row for opportunity {opp.id}: {str(row_error)}")
                continue

        # Prepare response
        output = si.getvalue()
        si.close()
        
        # Create response with Japanese filename
        filename = f'商談リスト_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Convert string to bytes for file sending
        output_bytes = output.encode('utf-8-sig')  # Use UTF-8 with BOM for Excel compatibility
        
        return send_file(
            BytesIO(output_bytes),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Export error: {str(e)}", exc_info=True)
        return {
            'error': 'エクスポート中にエラーが発生しました。',
            'details': str(e)
        }, 500
        return {'success': False, 'error': str(e)}, 500