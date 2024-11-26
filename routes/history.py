from flask import Blueprint, render_template, jsonify, request, current_app, abort, send_file
from flask_login import login_required, current_user
from models import Lead, Email
import traceback
from datetime import datetime
from io import StringIO
import csv

bp = Blueprint('history', __name__)

@bp.route('/')
@login_required
def list_history():
    try:
        leads = Lead.query.filter_by(user_id=current_user.id).all()
        leads_json = []
        for lead in leads:
            leads_json.append({
                'id': lead.id,
                'name': lead.name,
                'email': lead.email,
                'status': lead.status,
                'phone': lead.phone,
                'last_contact': lead.last_contact.isoformat() if lead.last_contact else None,
            })
        return render_template('history/index.html', leads=leads, leads_json=leads_json)
    except Exception as e:
        current_app.logger.error(f"Error in list_history: {str(e)}")
        return jsonify({'error': 'データの取得中にエラーが発生しました'}), 500

@bp.route('/leads/<int:lead_id>')
@login_required
def show_history(lead_id):
    try:
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            abort(404)
        return render_template('history.html', lead=lead)
    except Exception as e:
        current_app.logger.error(f"Error in show_history: {str(e)}")
        return jsonify({'error': 'データの取得中にエラーが発生しました'}), 500

@bp.route('/api/leads/<int:lead_id>/messages')
@login_required
def get_history(lead_id):
    try:
        # リードの存在確認を追加
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            return jsonify({'error': 'リードが見つかりません'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = 20

        # 基本クエリの構築
        query = Email.query.filter_by(lead_id=lead_id)

        # 検索パラメータの取得と処理
        search_query = request.args.get('query', '')
        search_type = request.args.get('type', 'content')

        if search_query:
            if search_type == 'content':
                query = query.filter(Email.content.ilike(f'%{search_query}%'))
            elif search_type == 'date':
                date_from = request.args.get('date_from')
                date_to = request.args.get('date_to')
                if date_from and date_to:
                    try:
                        query = query.filter(Email.received_date.between(date_from, date_to))
                    except Exception as date_error:
                        current_app.logger.error(f"Date filter error: {str(date_error)}")
                        return jsonify({'error': '日付フィルターが無効です'}), 400
            elif search_type == 'sender':
                query = query.filter(Email.sender.ilike(f'%{search_query}%'))

        try:
            # ページネーション
            pagination = query.order_by(Email.received_date.desc()).paginate(
                page=page, per_page=per_page, error_out=False)

            if not pagination.items and page > 1:
                return jsonify({'error': '指定されたページは存在しません'}), 404

            messages = []
            for email in pagination.items:
                messages.append({
                    'id': email.id,
                    'content': email.content,
                    'sender': email.sender,
                    'received_date': email.received_date.isoformat() if email.received_date else None,
                    'is_from_lead': True if email.sender == lead.email else False
                })

            return jsonify({
                'messages': messages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'total_pages': pagination.pages,
                'current_page': pagination.page
            })

        except Exception as query_error:
            current_app.logger.error(f"Query execution error: {str(query_error)}")
            return jsonify({'error': 'データの取得中にエラーが発生しました'}), 500

    except Exception as e:
        current_app.logger.error(f"Error in get_history: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'データの取得中にエラーが発生しました'}), 500

@bp.route('/leads/<int:lead_id>/export')
@login_required
def export_history(lead_id):
    try:
        # リードの存在確認
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            abort(404)

        # メールデータの取得
        emails = Email.query.filter_by(lead_id=lead_id).order_by(Email.received_date.desc()).all()

        # CSVの作成
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['日付', '送信者', '内容'])

        for email in emails:
            writer.writerow([
                email.received_date.strftime('%Y-%m-%d %H:%M:%S') if email.received_date else '',
                email.sender,
                email.content
            ])

        # レスポンスの作成
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'communication_history_{lead.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    except Exception as e:
        current_app.logger.error(f"Error in export_history: {str(e)}")
        return jsonify({'error': 'エクスポート中にエラーが発生しました'}), 500

@bp.route('/api/leads/<int:lead_id>/analyze', methods=['POST'])
@login_required
def analyze_lead(lead_id):
    try:
        # AIRollbackServiceのインスタンス化
        from services.ai_rollback import AIRollbackService
        from models import UserSettings
        
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        ai_service = AIRollbackService(user_settings)
        
        # 行動パターン分析の実行
        result = ai_service.analyze_customer_behavior(lead_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"リード分析中にエラーが発生: {str(e)}")
        return jsonify({'error': '分析中にエラーが発生しました'}), 500