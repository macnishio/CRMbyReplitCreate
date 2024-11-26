from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import Lead, Email
from extensions import db
from datetime import datetime
import traceback
import json

bp = Blueprint('history', __name__)

from flask import Blueprint, render_template, jsonify, request, current_app, abort, send_file
from flask_login import login_required, current_user
from models import Lead, Email, UserSettings
from services.ai_analysis import AIAnalysisService
from io import BytesIO, StringIO
import traceback
from datetime import datetime
import csv
import json

bp = Blueprint('history', __name__)

@bp.route('/')
@login_required
def index():
    """履歴一覧ページを表示"""
    try:
        # ユーザーのリードを取得し、last_contactで降順ソート
        leads = Lead.query.filter_by(user_id=current_user.id).order_by(Lead.last_contact.desc()).all()
        
        # テンプレート用のJSONデータを準備
        leads_json = [{
            'id': lead.id,
            'name': lead.name,
            'email': lead.email,
            'status': lead.status,
            'last_contact': lead.last_contact.isoformat() if lead.last_contact else None,
            'phone': lead.phone,
            'cc': lead.cc,
            'bcc': lead.bcc
        } for lead in leads]

        current_app.logger.debug(f"Found {len(leads)} leads for user {current_user.id}")
        return render_template('history/index.html', 
                            leads=leads,
                            leads_json=leads_json)
    except Exception as e:
        current_app.logger.error(f"Error in history index: {str(e)}")
        return render_template('history/index.html', 
                            leads=[],
                            leads_json=[])

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
            current_app.logger.warning(f"Lead {lead_id} not found for user {current_user.id}")
            abort(404)

        # メールデータの取得
        emails = Email.query.filter_by(lead_id=lead_id).order_by(Email.received_date.desc()).all()
        
        # 一時的なStringIOを使用してUTF-8でCSVを作成
        string_output = StringIO()
        writer = csv.writer(string_output)
        writer.writerow(['日付', '送信者', '内容'])

        for email in emails:
            writer.writerow([
                email.received_date.strftime('%Y-%m-%d %H:%M:%S') if email.received_date else '',
                email.sender,
                email.content
            ])

        # StringIOの内容をBytesIOに変換（BOM付きUTF-8）
        output = BytesIO()
        output.write(u'\ufeff'.encode('utf-8'))  # BOMを追加
        output.write(string_output.getvalue().encode('utf-8'))
        output.seek(0)
        
        filename = f'communication_history_{lead.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename,
            max_age=0
        )

    except Exception as e:
        current_app.logger.error(f"Error in export_history: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': 'エクスポート中にエラーが発生しました',
            'details': str(e) if current_app.debug else None
        }), 500

@bp.route('/api/leads/<int:lead_id>/analyze', methods=['POST'])
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

@bp.route('/api/leads/<int:lead_id>/timeline')
@login_required
def get_lead_timeline(lead_id):
    """リードに関する重要なイベントのタイムラインを取得"""
    try:
        # リードの存在確認
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            return jsonify({
                'success': False,
                'error': 'リードが見つかりません',
                'code': 'LEAD_NOT_FOUND'
            }), 404

        timeline_events = []
        
        try:
            # メールイベントの取得と追加
            emails = Email.query.filter_by(lead_id=lead_id).order_by(Email.received_date.desc()).all()
            for email in emails:
                if email.received_date:
                    timeline_events.append({
                        'type': 'email',
                        'date': email.received_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': email.received_date.timestamp(),
                        'title': 'メールのやり取り',
                        'description': email.content[:100] + ('...' if len(email.content) > 100 else ''),
                        'is_from_lead': email.sender == lead.email,
                        'icon': 'fa-envelope',
                        'metadata': {
                            'sender': email.sender,
                            'subject': email.subject
                        }
                    })
        except Exception as e:
            current_app.logger.error(f"メールデータの取得エラー: {str(e)}")
            
        try:
            # ステータス変更イベントの追加
            if hasattr(lead, 'status_changes') and lead.status_changes:
                for change in lead.status_changes:
                    timeline_events.append({
                        'type': 'status_change',
                        'date': change.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': change.timestamp.timestamp(),
                        'title': 'ステータス変更',
                        'description': f'{change.old_status} → {change.new_status}',
                        'icon': 'fa-exchange-alt',
                        'metadata': {
                            'old_status': change.old_status,
                            'new_status': change.new_status
                        }
                    })
        except Exception as e:
            current_app.logger.error(f"ステータス変更データの取得エラー: {str(e)}")
                
        try:
            # スコア更新イベントの追加
            if hasattr(lead, 'score_history') and lead.score_history:
                for score_update in lead.score_history:
                    timeline_events.append({
                        'type': 'score_update',
                        'date': score_update.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': score_update.timestamp.timestamp(),
                        'title': 'スコア更新',
                        'description': f'新しいスコア: {score_update.new_score}',
                        'icon': 'fa-chart-line',
                        'metadata': {
                            'old_score': score_update.old_score if hasattr(score_update, 'old_score') else None,
                            'new_score': score_update.new_score
                        }
                    })
        except Exception as e:
            current_app.logger.error(f"スコア履歴データの取得エラー: {str(e)}")

        try:
            # 行動パターン分析イベントの追加
            if lead.behavior_patterns:
                for pattern in lead.behavior_patterns:
                    if isinstance(pattern, dict) and pattern.get('timestamp'):
                        try:
                            pattern_date = datetime.fromisoformat(pattern['timestamp'].replace('Z', '+00:00'))
                            timeline_events.append({
                                'type': 'behavior_analysis',
                                'date': pattern_date.strftime('%Y-%m-%d %H:%M:%S'),
                                'timestamp': pattern_date.timestamp(),
                                'title': '行動パターン分析',
                                'description': pattern.get('summary', '行動パターンの更新'),
                                'icon': 'fa-brain',
                                'metadata': {
                                    'analysis_type': pattern.get('type'),
                                    'confidence': pattern.get('confidence')
                                }
                            })
                        except ValueError as e:
                            current_app.logger.error(f"日付パース時エラー: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"行動パターンデータの取得エラー: {str(e)}")

        # 日付でソート（timestampを使用）
        timeline_events.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

        return jsonify({
            'success': True,
            'timeline': timeline_events,
            'lead': {
                'id': lead.id,
                'name': lead.name,
                'email': lead.email,
                'status': lead.status
            }
        })

    except Exception as e:
        current_app.logger.error(f"Timeline generation error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'タイムラインの生成中にエラーが発生しました',
            'code': 'TIMELINE_GENERATION_ERROR'
        }), 500