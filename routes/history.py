from flask import Blueprint, render_template, jsonify, request, current_app, abort, send_file
from flask_login import login_required, current_user
from models import Lead, Email, UserSettings
from services.ai_analysis import AIAnalysisService
from extensions import db
from io import BytesIO, StringIO
import traceback
from datetime import datetime
import csv
import json

bp = Blueprint('history', __name__, url_prefix='/history')

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
        # リードの存在確認
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            current_app.logger.warning(f"Lead {lead_id} not found for user {current_user.id}")
            return render_template('history/error.html', 
                                error="指定されたリードが見つかりません", 
                                back_url=url_for('leads.list_leads'))

        return render_template('history/detail.html', 
                           lead=lead,
                           page_title=f"{lead.name}とのコミュニケーション履歴")

    except Exception as e:
        current_app.logger.error(f"Error in show_history: {str(e)}\n{traceback.format_exc()}")
        return render_template('history/error.html', 
                           error="データの取得中にエラーが発生しました",
                           back_url=url_for('leads.list_leads'))

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
        current_app.logger.info(f"リードID {lead_id} の存在確認を開始")
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
                current_app.logger.info(f"リードID {lead_id} のメールデータ取得を開始")
                emails = Email.query.filter_by(lead_id=lead_id).order_by(Email.received_date.desc()).all()
                current_app.logger.info(f"メールデータ取得完了。件数: {len(emails)}")
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
                                'subject': email.subject if hasattr(email, 'subject') else None,
                                'email_id': email.id
                            }
                        })
            except Exception as e:
                current_app.logger.error(f"メールデータの取得中にエラーが発生: {str(e)}\n{traceback.format_exc()}")
                return jsonify({
                    'success': False,
                    'error': 'メールデータの取得中にエラーが発生しました',
                    'code': 'EMAIL_FETCH_ERROR'
                }), 500

            # 案件（商談）の取得と追加
            try:
                from models import Opportunity
                opportunities = Opportunity.query.filter_by(lead_id=lead_id).all()
                for opportunity in opportunities:
                    # 作成イベント
                    timeline_events.append({
                        'type': 'opportunity',
                        'date': opportunity.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': opportunity.created_at.timestamp(),
                        'title': '商談の作成',
                        'description': f'商談「{opportunity.name}」が作成されました\n金額: ¥{"{:,.0f}".format(opportunity.amount)}',
                        'icon': 'fa-handshake',
                        'metadata': {
                            'id': opportunity.id,
                            'stage': opportunity.stage,
                            'amount': opportunity.amount,
                            'name': opportunity.name,
                            'close_date': opportunity.close_date.strftime('%Y-%m-%d') if opportunity.close_date else None
                        }
                    })
                    # ステージ変更イベント（もし存在する場合）
                    if hasattr(opportunity, 'stage_changes') and opportunity.stage_changes:
                        for change in opportunity.stage_changes:
                            timeline_events.append({
                                'type': 'opportunity_stage_change',
                                'date': change.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                'timestamp': change.timestamp.timestamp(),
                                'title': '商談ステージの変更',
                                'description': f'商談「{opportunity.name}」のステージが\n{change.old_stage} → {change.new_stage}に変更されました',
                                'icon': 'fa-exchange-alt',
                                'metadata': {
                                    'opportunity_id': opportunity.id,
                                    'old_stage': change.old_stage,
                                    'new_stage': change.new_stage
                                }
                            })
            except Exception as e:
                current_app.logger.error(f"商談データの取得中にエラーが発生: {str(e)}")

            # タスクの取得と追加
            try:
                from models import Task
                tasks = Task.query.filter_by(lead_id=lead_id).all()
                for task in tasks:
                    # タスク作成イベント
                    timeline_events.append({
                        'type': 'task',
                        'date': task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': task.created_at.timestamp(),
                        'title': 'タスクの作成',
                        'description': task.description[:100] + ('...' if len(task.description) > 100 else ''),
                        'icon': 'fa-tasks',
                        'metadata': {
                            'id': task.id,
                            'status': task.status,
                            'priority': task.priority if hasattr(task, 'priority') else None,
                            'due_date': task.due_date.strftime('%Y-%m-%d') if hasattr(task, 'due_date') and task.due_date else None
                        }
                    })
                    # タスクステータス変更イベント（もし存在する場合）
                    if hasattr(task, 'status_changes') and task.status_changes:
                        for change in task.status_changes:
                            timeline_events.append({
                                'type': 'task_status_change',
                                'date': change.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                'timestamp': change.timestamp.timestamp(),
                                'title': 'タスクステータスの変更',
                                'description': f'タスク「{task.description[:30]}...」のステータスが\n{change.old_status} → {change.new_status}に変更されました',
                                'icon': 'fa-check-circle',
                                'metadata': {
                                    'task_id': task.id,
                                    'old_status': change.old_status,
                                    'new_status': change.new_status
                                }
                            })
            except Exception as e:
                current_app.logger.error(f"タスクデータの取得中にエラーが発生: {str(e)}")

            # スケジュールの取得と追加
            try:
                from models import Schedule
                schedules = Schedule.query.filter_by(lead_id=lead_id).all()
                for schedule in schedules:
                    # スケジュール作成イベント
                    timeline_events.append({
                        'type': 'schedule',
                        'date': schedule.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': schedule.start_time.timestamp(),
                        'title': 'スケジュールの作成',
                        'description': (
                            f'{schedule.title}\n'
                            f'開始: {schedule.start_time.strftime("%Y-%m-%d %H:%M")}\n'
                            f'終了: {schedule.end_time.strftime("%Y-%m-%d %H:%M") if schedule.end_time else "未設定"}'
                            + (f'\n{schedule.description[:100]}...' if schedule.description else '')
                        ),
                        'icon': 'fa-calendar',
                        'metadata': {
                            'id': schedule.id,
                            'title': schedule.title,
                            'start_time': schedule.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'end_time': schedule.end_time.strftime('%Y-%m-%d %H:%M:%S') if schedule.end_time else None,
                            'status': schedule.status if hasattr(schedule, 'status') else None,
                            'location': schedule.location if hasattr(schedule, 'location') else None
                        }
                    })
                    # スケジュールステータス変更イベント（もし存在する場合）
                    if hasattr(schedule, 'status_changes') and schedule.status_changes:
                        for change in schedule.status_changes:
                            timeline_events.append({
                                'type': 'schedule_status_change',
                                'date': change.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                'timestamp': change.timestamp.timestamp(),
                                'title': 'スケジュールステータスの変更',
                                'description': f'スケジュール「{schedule.title}」のステータスが\n{change.old_status} → {change.new_status}に変更されました',
                                'icon': 'fa-clock',
                                'metadata': {
                                    'schedule_id': schedule.id,
                                    'old_status': change.old_status,
                                    'new_status': change.new_status
                                }
                            })
            except Exception as e:
                current_app.logger.error(f"スケジュールデータの取得中にエラーが発生: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"メールデータの取得エラー: {str(e)}")
            
        try:
            # ステータス変更イベントの追加
            current_app.logger.info(f"リードID {lead_id} のステータス変更データ取得を開始")
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
            current_app.logger.info(f"リードID {lead_id} のスコア更新データ取得を開始")
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

@bp.route('/api/leads/<int:lead_id>/search')
@login_required
def search_history(lead_id):
    """履歴を検索"""
    try:
        # 検索パラメータの取得
        query = request.args.get('q', '')
        search_type = request.args.get('type', 'content')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        # リードの存在確認
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            return jsonify({
                'success': False,
                'error': 'リードが見つかりません',
                'code': 'LEAD_NOT_FOUND'
            }), 404

        # 検索クエリの構築
        emails_query = Email.query.filter_by(lead_id=lead_id)

        if search_type == 'content' and query:
            emails_query = emails_query.filter(Email.content.ilike(f'%{query}%'))
        elif search_type == 'sender' and query:
            emails_query = emails_query.filter(Email.sender.ilike(f'%{query}%'))
        elif search_type == 'date':
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