from flask import Blueprint, render_template, jsonify, request, current_app, abort, send_file
from flask_login import login_required, current_user
from models import Lead, Email, UserSettings, FilterPreset # Added FilterPreset import
from services.ai_analysis import AIAnalysisService
from extensions import db
from io import BytesIO, StringIO
import csv
import json
from datetime import datetime
import traceback

bp = Blueprint('history', __name__)

@bp.route('/')
@login_required
def index():
    """履歴一覧ページを表示"""
    try:
        current_app.logger.debug(f"Fetching leads for user {current_user.id}")

        leads = Lead.query.filter_by(user_id=current_user.id)\
            .order_by(Lead.last_contact.desc())\
            .all()

        current_app.logger.debug(f"Found {len(leads) if leads else 0} leads")

        leads_json = [{
            'id': lead.id,
            'name': lead.name,
            'email': lead.email,
            'status': lead.status,
            'last_contact': lead.last_contact.isoformat() if lead.last_contact else None,
            'phone': lead.phone if hasattr(lead, 'phone') else None
        } for lead in leads] if leads else []

        return render_template('history/index.html', 
                           leads=leads,
                           leads_json=leads_json)

    except Exception as e:
        current_app.logger.error(f"Error in index: {str(e)}\n{traceback.format_exc()}")
        db.session.rollback()
        return render_template('history/index.html', 
                           leads=[],
                           leads_json=[],
                           error="データの取得中にエラーが発生しました")

@bp.route('/leads/<int:lead_id>')  
@login_required
def show_history(lead_id):
    """個別の履歴詳細を表示"""
    try:
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            abort(404)
        return render_template('history/detail.html', lead=lead)  
    except Exception as e:
        current_app.logger.error(f"Error in show_history: {str(e)}")
        return render_template('history/detail.html', error="データの取得中にエラーが発生しました")

@bp.route('/api/leads/<int:lead_id>/messages')
@login_required
def get_messages(lead_id):
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
            try:
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
                                'subject': email.subject if hasattr(email, 'subject') else None
                            }
                        })
            except Exception as e:
                current_app.logger.error(f"メールデータの取得中にエラーが発生: {str(e)}\n{traceback.format_exc()}")
                return jsonify({
                    'success': False,
                    'error': 'メールデータの取得中にエラーが発生しました',
                    'code': 'EMAIL_FETCH_ERROR'
                }), 500
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

@bp.route('/api/save-filter-preset', methods=['POST'])
@login_required
def save_filter_preset():
    """フィルタープリセットを保存"""
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'filters' not in data:
            return jsonify({'error': '必要なデータが不足しています'}), 400

        # 既存のプリセットをチェック
        existing_preset = FilterPreset.query.filter_by(
            user_id=current_user.id,
            name=data['name']
        ).first()

        if existing_preset:
            # 既存のプリセットを更新
            existing_preset.filters = data['filters']
            existing_preset.updated_at = datetime.utcnow()
            message = 'フィルタープリセットを更新しました'
        else:
            # 新しいプリセットを作成
            preset = FilterPreset(
                user_id=current_user.id,
                name=data['name'],
                filters=data['filters']
            )
            db.session.add(preset)
            message = 'フィルタープリセットを保存しました'

        db.session.commit()
        return jsonify({'success': True, 'message': message})

    except Exception as e:
        current_app.logger.error(f"Error saving filter preset: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'プリセットの保存中にエラーが発生しました'}), 500

@bp.route('/api/delete-filter-preset', methods=['POST'])
@login_required
def delete_filter_preset():
    """フィルタープリセットを削除"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'プリセット名が指定されていません'}), 400

        preset = FilterPreset.query.filter_by(
            user_id=current_user.id,
            name=data['name']
        ).first()

        if not preset:
            return jsonify({'error': '指定されたプリセットが見つかりません'}), 404

        db.session.delete(preset)
        db.session.commit()

        return jsonify({'success': True, 'message': 'プリセットを削除しました'})

    except Exception as e:
        current_app.logger.error(f"Error deleting filter preset: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'プリセットの削除中にエラーが発生しました'}), 500

@bp.route('/api/filter-presets', methods=['GET'])
@login_required
def get_filter_presets():
    """ユーザーのフィルタープリセットを取得"""
    try:
        presets = FilterPreset.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'success': True,
            'presets': [preset.to_dict() for preset in presets]
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching filter presets: {str(e)}")
        return jsonify({'error': 'プリセットの取得中にエラーが発生しました'}), 500

@bp.route('/search', methods=['GET'])
@login_required
def search_history():
    """履歴検索機能"""
    try:
        lead_id = request.args.get('lead_id', type=int)
        if not lead_id:
            return jsonify({
                'success': False,
                'error': 'リードIDが指定されていません',
                'code': 'LEAD_ID_REQUIRED'
            }), 400

        lead = Lead.query.get(lead_id)
        if not lead or lead.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': '指定されたリードが見つかりません',
                'code': 'LEAD_NOT_FOUND'
            }), 404

        # 検索パラメータの取得
        search_type = request.args.get('type', 'all')
        query = request.args.get('query', '').strip()
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        # メールのクエリ構築
        emails_query = Email.query.filter_by(lead_id=lead_id)

        # 検索条件の適用
        if query:
            if search_type == 'subject':
                emails_query = emails_query.filter(Email.subject.ilike(f'%{query}%'))
            elif search_type == 'content':
                emails_query = emails_query.filter(Email.content.ilike(f'%{query}%'))
            elif search_type == 'all':
                emails_query = emails_query.filter(
                    db.or_(
                        Email.subject.ilike(f'%{query}%'),
                        Email.content.ilike(f'%{query}%')
                    )
                )

        # 日付範囲の適用
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                emails_query = emails_query.filter(Email.received_date >= from_date)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '開始日の形式が不正です',
                    'code': 'INVALID_DATE_FORMAT'
                }), 400

        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                # 終了日の場合は日付の最後（23:59:59）までを含める
                to_date = to_date.replace(hour=23, minute=59, second=59)
                emails_query = emails_query.filter(Email.received_date <= to_date)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '終了日の形式が不正です',
                    'code': 'INVALID_DATE_FORMAT'
                }), 400

        # 結果を取得
        emails = emails_query.order_by(Email.received_date.desc()).all()

        # 結果を整形
        results = [{
            'id': email.id,
            'content': email.content,
            'sender': email.sender,
            'received_date': email.received_date.isoformat() if email.received_date else None,
            'is_from_lead': email.sender == lead.email,
            'subject': email.subject if hasattr(email, 'subject') else None
        } for email in emails]

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'search_params': {
                'type': search_type,
                'query': query,
                'date_from': date_from,
                'date_to': date_to
            }
        })

    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': '検索中にエラーが発生しました',
            'code': 'SEARCH_ERROR',
            'details': str(e) if current_app.debug else None
        }), 500