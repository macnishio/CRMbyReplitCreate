from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from models.system_changes import SystemChange, RollbackHistory
from services.ai_rollback import AIRollbackService
from models.user_settings import UserSettings
from extensions import db
from datetime import datetime
from typing import Dict, Any, Optional

bp = Blueprint('system_management', __name__)

def get_ai_rollback_service() -> Optional[AIRollbackService]:
    """ユーザー設定に基づいてAIロールバックサービスのインスタンスを取得"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if user_settings and user_settings.claude_api_key:
            return AIRollbackService(user_settings)
        return None
    except Exception as e:
        current_app.logger.error(f"AIロールバックサービスの初期化エラー: {str(e)}")
        return None

@bp.route('/api/system-changes', methods=['GET'])
@login_required
def list_system_changes():
    """システム変更履歴の一覧を取得"""
    changes = SystemChange.query.order_by(SystemChange.timestamp.desc()).all()
    return jsonify([{
        'id': change.id,
        'change_type': change.change_type,
        'description': change.description,
        'timestamp': change.timestamp.isoformat(),
        'is_risky': change.is_risky,
        'ai_analysis': change.ai_analysis
    } for change in changes])

@bp.route('/api/system-changes/<int:change_id>/analyze', methods=['POST'])
@login_required
def analyze_change(change_id):
    """特定の変更をAIで分析"""
    ai_service = get_ai_rollback_service()
    if not ai_service:
        return jsonify({
            'success': False,
            'error': 'AIサービスの初期化に失敗しました。API設定を確認してください。'
        }), 400

    try:
        change = SystemChange.query.get_or_404(change_id)
        analysis = ai_service.analyze_system_change(change)
        
        if isinstance(analysis, dict):
            change.ai_analysis = json.dumps(analysis, ensure_ascii=False)
        else:
            change.ai_analysis = analysis
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        current_app.logger.error(f"変更分析エラー: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/system-changes/<int:change_id>/rollback', methods=['POST'])
@login_required
def execute_rollback(change_id):
    """システム変更のロールバックを実行"""
    change = SystemChange.query.get_or_404(change_id)
    
    # AIによる分析と推奨事項の取得
    if not change.ai_analysis:
        change.ai_analysis = ai_rollback_service.analyze_system_change(change)
        db.session.commit()
    
    # ロールバックの実行
    success = ai_rollback_service.execute_rollback(change)
    
    return jsonify({
        'success': success,
        'message': '正常にロールバックが完了しました。' if success else 'ロールバック中にエラーが発生しました。'
    })

@bp.route('/api/rollback-history', methods=['GET'])
@login_required
def list_rollback_history():
    """ロールバック履歴の一覧を取得"""
    history = RollbackHistory.query.order_by(RollbackHistory.executed_at.desc()).all()
    return jsonify([{
        'id': entry.id,
        'system_change_id': entry.system_change_id,
        'executed_at': entry.executed_at.isoformat(),
        'success': entry.success,
        'error_message': entry.error_message,
        'ai_recommendation': entry.ai_recommendation
    } for entry in history])

@bp.route('/api/system-changes/track', methods=['POST'])
@login_required
def track_system_change():
    """新しいシステム変更を記録"""
    data = request.get_json()
    
    change = SystemChange(
        change_type=data['change_type'],
        description=data['description'],
        change_metadata=data.get('metadata'),
        is_risky=data.get('is_risky', False)
    )
    
    db.session.add(change)
    db.session.commit()
    
    # 必要に応じてAI分析を実行
    if data.get('analyze_immediately', False):
        change.ai_analysis = ai_rollback_service.analyze_system_change(change)
        db.session.commit()
    
    return jsonify({
        'success': True,
        'change_id': change.id
    })
