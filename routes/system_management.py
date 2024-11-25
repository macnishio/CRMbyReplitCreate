from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from models.system_changes import SystemChange, RollbackHistory
from services.ai_rollback import AIRollbackService
from extensions import db
from datetime import datetime

bp = Blueprint('system_management', __name__)
ai_rollback_service = AIRollbackService()

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
    change = SystemChange.query.get_or_404(change_id)
    analysis = ai_rollback_service.analyze_system_change(change)
    
    change.ai_analysis = analysis
    db.session.commit()
    
    return jsonify({
        'success': True,
        'analysis': analysis
    })

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
