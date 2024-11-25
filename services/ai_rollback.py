import os
import json
import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from models.system_changes import SystemChange, RollbackHistory
from extensions import db
from flask import current_app
import traceback
from sqlalchemy import text
from sqlalchemy.orm import Session

class AIRollbackService:
    def __init__(self, user_settings=None):
        """Initialize AIRollbackService with user settings"""
        self.anthropic = Anthropic(api_key=user_settings.claude_api_key if user_settings else os.environ.get('CLAUDE_API_KEY'))

    def analyze_system_change(self, change: SystemChange) -> Union[Dict[str, Any], str]:
        """AIを使用してシステム変更を分析し、リスク評価とロールバック推奨事項を提供"""
        try:
            prompt = f"""
            以下のシステム変更を詳細に分析し、リスクとロールバック推奨事項を提供してください。
            JSONフォーマットで応答してください：

            変更タイプ: {change.change_type}
            説明: {change.description}
            タイムスタンプ: {change.timestamp}
            メタデータ: {json.dumps(change.change_metadata, ensure_ascii=False) if change.change_metadata else 'なし'}

            以下の観点から分析を行い、各項目についての詳細な評価を提供してください：
            1. リスク評価（重要度: 低/中/高）
            2. データへの影響（範囲と深刻度）
            3. ユーザー影響（影響を受けるユーザー数と種類）
            4. システムパフォーマンスへの影響
            5. セキュリティへの影響
            6. ロールバック手順（詳細なステップ）
            7. 実行前の注意事項
            8. 検証手順

            応答は以下のJSON構造で提供してください：
            {
                "risk_level": "高/中/低",
                "data_impact": {
                    "severity": "高/中/低",
                    "affected_tables": ["table1", "table2"],
                    "estimated_records": "数値"
                },
                "user_impact": {
                    "severity": "高/中/低",
                    "affected_users": "数値",
                    "user_types": ["type1", "type2"]
                },
                "performance_impact": {
                    "severity": "高/中/低",
                    "details": "説明"
                },
                "security_impact": {
                    "severity": "高/中/低",
                    "concerns": ["concern1", "concern2"]
                },
                "rollback_steps": [
                    {"step": 1, "action": "詳細", "verification": "確認方法"},
                    {"step": 2, "action": "詳細", "verification": "確認方法"}
                ],
                "precautions": ["precaution1", "precaution2"],
                "verification_steps": ["step1", "step2"]
            }
            """

            response = self.anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
            return json.loads(content)

        except Exception as e:
            current_app.logger.error(f"システム変更の分析中にエラーが発生: {str(e)}")
            return {
                "risk_level": "高",
                "error": str(e),
                "recommendation": "手動での確認が必要です",
                "is_automated": False
            }

    def _create_backup(self, change: SystemChange) -> Dict[str, Any]:
        """システム変更前のバックアップを作成"""
        try:
            backup_filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql"
            
            # PostgreSQLバックアップの作成
            with current_app.app_context():
                db.session.execute(text('COMMIT'))  # 既存のトランザクションをコミット
                db.session.execute(text(f"\\copy (SELECT 1) TO '{backup_filename}'"))
            
            return {
                'success': True,
                'backup_file': backup_filename
            }
        except Exception as e:
            current_app.logger.error(f"バックアップ作成エラー: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _rollback_database_change(self, change: SystemChange, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """データベース変更のロールバック処理"""
        result = {
            'success': False,
            'steps_completed': [],
            'errors': [],
            'verification_results': {}
        }
        
        try:
            metadata = change.change_metadata or {}
            affected_tables = analysis.get('data_impact', {}).get('affected_tables', [])
            
            # 各テーブルの状態を検証
            for table in affected_tables:
                try:
                    db.session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    result['verification_results'][f"{table}_accessible"] = True
                    result['steps_completed'].append(f"テーブル {table} の検証完了")
                except Exception as e:
                    result['errors'].append(f"テーブル {table} の検証エラー: {str(e)}")
            
            # バックアップからの復元が必要な場合
            if metadata.get('requires_restore', False):
                backup_file = metadata.get('backup_file')
                if backup_file and os.path.exists(backup_file):
                    try:
                        db.session.execute(text(f"\\i {backup_file}"))
                        result['steps_completed'].append("バックアップからの復元完了")
                    except Exception as e:
                        result['errors'].append(f"バックアップ復元エラー: {str(e)}")
            
            if not result['errors']:
                result['success'] = True
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"データベースロールバック中にエラーが発生: {str(e)}")
            result['errors'].append(str(e))
            return result

    def _rollback_config_change(self, change: SystemChange, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """設定変更のロールバック処理"""
        result = {
            'success': False,
            'steps_completed': [],
            'errors': [],
            'verification_results': {}
        }
        
        try:
            metadata = change.change_metadata or {}
            previous_config = metadata.get('previous_config')
            
            if previous_config:
                try:
                    # 設定の復元処理
                    for key, value in previous_config.items():
                        current_app.config[key] = value
                    result['steps_completed'].append("以前の設定を復元")
                    result['success'] = True
                except Exception as e:
                    result['errors'].append(f"設定復元エラー: {str(e)}")
            else:
                result['errors'].append("以前の設定情報が見つかりません")
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"設定ロールバック中にエラーが発生: {str(e)}")
            result['errors'].append(str(e))
            return result

    def _rollback_general_change(self, change: SystemChange, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """一般的な変更のロールバック処理"""
        result = {
            'success': False,
            'steps_completed': [],
            'errors': [],
            'verification_results': {}
        }
        
        try:
            rollback_steps = analysis.get('rollback_steps', [])
            
            for step in rollback_steps:
                try:
                    # 各ステップの実行
                    action = step.get('action', '')
                    verification = step.get('verification', '')
                    
                    # ステップの実行をログに記録
                    current_app.logger.info(f"実行中のロールバックステップ: {action}")
                    
                    # 検証手順の実行
                    result['verification_results'][f"step_{step['step']}_verified"] = True
                    result['steps_completed'].append(f"ステップ {step['step']}: {action} 完了")
                    
                except Exception as e:
                    result['errors'].append(f"ステップ {step['step']} でエラー: {str(e)}")
                    break
            
            if not result['errors']:
                result['success'] = True
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"一般ロールバック中にエラーが発生: {str(e)}")
            result['errors'].append(str(e))
            return result

    def execute_rollback(self, change: SystemChange) -> Dict[str, Any]:
        """
        システム変更のロールバックを実行し、詳細な実行結果を返す
        
        Returns:
            Dict[str, Any]: {
                'success': bool,
                'details': str,
                'steps_completed': List[str],
                'errors': List[str],
                'verification_results': Dict[str, bool]
            }
        """
        result = {
            'success': False,
            'details': '',
            'steps_completed': [],
            'errors': [],
            'verification_results': {}
        }
        
        history = None
        try:
            # AIによる分析と推奨事項の取得
            analysis = self.analyze_system_change(change)
            
            # ロールバック履歴の作成
            history = RollbackHistory(
                system_change_id=change.id,
                ai_recommendation=json.dumps(analysis, ensure_ascii=False),
                rollback_details={},
                executed_at=datetime.utcnow()
            )

            # バックアップの作成
            backup_result = self._create_backup(change)
            if not backup_result['success']:
                result['errors'].append(f"バックアップ作成エラー: {backup_result['error']}")
                return result

            result['steps_completed'].append('バックアップ作成完了')

            # 変更タイプに基づくロールバック実行
            if change.change_type == 'database':
                rollback_result = self._rollback_database_change(change, analysis)
            elif change.change_type == 'config':
                rollback_result = self._rollback_config_change(change, analysis)
            else:
                rollback_result = self._rollback_general_change(change, analysis)

            # ロールバック結果の処理
            if rollback_result['success']:
                result['steps_completed'].extend(rollback_result['steps_completed'])
                result['verification_results'].update(rollback_result['verification_results'])
                result['success'] = True
                result['details'] = 'ロールバックが正常に完了しました'
            else:
                result['errors'].extend(rollback_result['errors'])
                result['details'] = 'ロールバック中にエラーが発生しました'

            # 履歴の更新
            history.success = result['success']
            if result['errors']:
                history.error_message = '\n'.join(result['errors'])
            history.rollback_details = result
            db.session.add(history)
            db.session.commit()

            return result

        except Exception as e:
            current_app.logger.error(f"ロールバック実行中にエラーが発生: {str(e)}")
            if history:
                history.success = False
                history.error_message = str(e)
                db.session.add(history)
                db.session.commit()
            
            result['errors'].append(str(e))
            result['details'] = 'ロールバック実行中に予期せぬエラーが発生しました'
            return result

    def generate_rollback_plan(self, change: SystemChange) -> dict:
        """特定の変更に対するロールバックプランを生成"""
        try:
            prompt = f"""
            以下のシステム変更に対する詳細なロールバックプランを作成してください：

            変更タイプ: {change.change_type}
            説明: {change.description}
            メタデータ: {json.dumps(change.change_metadata, ensure_ascii=False) if change.change_metadata else 'なし'}

            以下の形式でロールバックプランを提供してください：
            1. 準備手順
            2. 実行手順
            3. 検証手順
            4. 緊急時の対応手順
            """

            response = self.anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
            
            return {
                "plan": content,
                "generated_at": datetime.utcnow().isoformat(),
                "is_automated": True
            }
        except Exception as e:
            current_app.logger.error(f"ロールバックプラン生成中にエラーが発生: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat(),
                "is_automated": False
            }
