from flask import Blueprint, render_template, jsonify, request, current_app, abort, send_file
from flask_login import login_required, current_user
from models import Lead, Email, UserSettings
import traceback
from datetime import datetime
from io import StringIO
import csv
from services.ai_analysis_service import AIAnalysisService

bp = Blueprint('history', __name__)

@bp.route('/history')
@login_required
def list_history():
    """リード履歴の一覧を表示"""
    # 現在のユーザーのリードを取得
    leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.created_at.desc()).all()

    # 各リードの最新のメール日時を取得
    lead_data = []
    for lead in leads:
        latest_email = Email.query.filter_by(lead_id=lead.id)\
            .order_by(Email.received_date.desc())\
            .first()

        lead_data.append({
            'lead': lead,
            'latest_email_date': latest_email.received_date if latest_email else None,
            'email_count': Email.query.filter_by(lead_id=lead.id).count()
        })

    return render_template('history/list.html', lead_data=lead_data)

@bp.route('/history/<int:lead_id>')
@login_required
def show_history(lead_id):
    """リードとのコミュニケーション履歴を表示"""
    lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
    if not lead:
        abort(404)
    return render_template('history/detail.html', lead=lead)

@bp.route('/leads/<int:lead_id>/messages')
@login_required
def get_messages(lead_id):
    """リードとのメッセージ履歴を取得"""
    try:
        # リードの存在確認
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            return jsonify({'error': 'リードが見つかりません'}), 404

        # ページネーションパラメータ
        page = request.args.get('page', 1, type=int)
        per_page = min(int(request.args.get('per_page', 20)), 50)  # 最大50件まで

        # メールを日付の降順で取得
        query = Email.query.filter_by(lead_id=lead_id)\
            .order_by(Email.received_date.desc())
        
        # 総件数を取得
        total = query.count()
        
        # ページネーション適用
        emails = query.paginate(page=page, per_page=per_page, error_out=False)

        messages = []
        for email in emails.items:
            messages.append({
                'id': email.id,
                'content': email.content,
                'sender': email.sender,
                'subject': email.subject,
                'received_date': email.received_date.strftime('%Y-%m-%d %H:%M:%S'),
                'is_from_lead': email.sender == lead.email
            })

        return jsonify({
            'messages': messages,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_pages': emails.pages,
                'total_items': total,
                'has_next': emails.has_next,
                'has_prev': emails.has_prev
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error in get_messages: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'メッセージの取得中にエラーが発生しました'}), 500

@bp.route('/leads/<int:lead_id>/search')
@login_required
def search_history(lead_id):
    """履歴を検索"""
    try:
        query = request.args.get('q', '')
        search_type = request.args.get('type', 'content')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            return jsonify({'error': 'リードが見つかりません'}), 404

        # 検索クエリの構築
        emails_query = Email.query.filter_by(lead_id=lead_id)

        if search_type == 'content' and query:
            emails_query = emails_query.filter(Email.content.ilike(f'%{query}%'))
        elif search_type == 'sender' and query:
            emails_query = emails_query.filter(Email.sender.ilike(f'%{query}%'))
        elif search_type == 'date':
            if date_from:
                emails_query = emails_query.filter(Email.received_date >= datetime.strptime(date_from, '%Y-%m-%d'))
            if date_to:
                emails_query = emails_query.filter(Email.received_date <= datetime.strptime(date_to, '%Y-%m-%d'))

        # 結果の取得
        emails = emails_query.order_by(Email.received_date.desc()).all()

        results = [{
            'id': email.id,
            'content': email.content,
            'sender': email.sender,
            'subject': email.subject,
            'received_date': email.received_date.strftime('%Y-%m-%d %H:%M:%S'),
            'is_from_lead': email.sender == lead.email
        } for email in emails]

        return jsonify({'results': results})

    except Exception as e:
        current_app.logger.error(f"Error in search_history: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': '検索中にエラーが発生しました'}), 500

@bp.route('/leads/<int:lead_id>/export')
@login_required
def export_history(lead_id):
    """履歴をCSVでエクスポート"""
    try:
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            return jsonify({'error': 'リードが見つかりません'}), 404

        # CSVファイルの作成
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['送信日時', '送信者', '件名', '内容'])

        emails = Email.query.filter_by(lead_id=lead_id).order_by(Email.received_date.desc()).all()
        for email in emails:
            writer.writerow([
                email.received_date.strftime('%Y-%m-%d %H:%M:%S'),
                email.sender,
                email.subject,
                email.content
            ])

        output.seek(0)

        # ファイル名の生成
        filename = f"history_{lead.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # レスポンスの作成
        response = send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        return response

    except Exception as e:
        current_app.logger.error(f"Error in export_history: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'エクスポート中にエラーが発生しました'}), 500

@bp.route('/leads/<int:lead_id>/analyze', methods=['POST'])
@login_required
def analyze_lead_behavior(lead_id):
    """リードの行動パターンをAIで分析"""
    try:
        # ユーザー設定を取得
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return jsonify({'error': 'Claude APIキーが設定されていません'}), 400

        # リードの存在確認
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            return jsonify({'error': 'リードが見つかりません'}), 404

        # AI分析を実行
        ai_service = AIAnalysisService(user_settings)
        analysis_result = ai_service.analyze_lead_behavior(lead_id)

        if 'error' in analysis_result:
            return jsonify(analysis_result), 400

        return jsonify(analysis_result)

    except Exception as e:
        current_app.logger.error(f"Lead behavior analysis error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': '分析中にエラーが発生しました'}), 500
