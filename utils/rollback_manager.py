from datetime import datetime
from typing import Optional, Dict, Any
from flask import current_app
from models import SystemChange, RollbackHistory, db
from anthropic import Anthropic
from models import UserSettings
import json
import logging

class RollbackManager:
    def __init__(self, user_settings: UserSettings):
        self.user_settings = user_settings
        self._setup_logging()

    def _setup_logging(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def _get_ai_recommendation(self, system_change: SystemChange) -> Optional[str]:
        """AIを使用してロールバックの推奨事項を取得"""
        try:
            if not self.user_settings.claude_api_key:
                return "AI分析を実行するにはClaude APIキーが必要です。"

            client = Anthropic(api_key=self.user_settings.claude_api_key)
            
            prompt = f"""
            以下のシステム変更に対するロールバックの推奨事項を分析してください:
            
            変更タイプ: {system_change.change_type}
            説明: {system_change.description}
            タイムスタンプ: {system_change.timestamp}
            メタデータ: {json.dumps(system_change.change_metadata, ensure_ascii=False) if system_change.change_metadata else 'なし'}
            
            以下の点について分析してください：
            1. ロールバックのリスク評価
            2. 推奨されるロールバック手順
            3. 注意点と事前準備事項
            """

            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text if message and hasattr(message.content[0], 'text') else None

        except Exception as e:
            self.logger.error(f"AI recommendation error: {str(e)}")
            return None

    def record_system_change(
        self,
        change_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        is_risky: bool = False
    ) -> SystemChange:
        """システム変更を記録"""
        try:
            system_change = SystemChange(
                change_type=change_type,
                description=description,
                change_metadata=metadata,
                is_risky=is_risky
            )
            
            # AI分析を実行
            ai_analysis = self._get_ai_recommendation(system_change)
            if ai_analysis:
                system_change.ai_analysis = ai_analysis

            db.session.add(system_change)
            db.session.commit()
            
            self.logger.info(f"System change recorded: {description}")
            return system_change

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error recording system change: {str(e)}")
            raise

    def execute_rollback(self, system_change_id: int) -> RollbackHistory:
        """システム変更のロールバックを実行"""
        try:
            system_change = SystemChange.query.get(system_change_id)
            if not system_change:
                raise ValueError("指定されたシステム変更が見つかりません。")

            # ロールバック履歴を作成
            rollback_history = RollbackHistory(
                system_change_id=system_change_id,
                executed_at=datetime.utcnow()
            )

            try:
                # AIによる推奨事項を取得
                ai_recommendation = self._get_ai_recommendation(system_change)
                rollback_history.ai_recommendation = ai_recommendation

                # ここでロールバックの具体的な処理を実装
                # 例: データベースの変更を元に戻す、設定を戻すなど
                if system_change.change_type == 'database':
                    self._rollback_database_change(system_change)
                elif system_change.change_type == 'config':
                    self._rollback_config_change(system_change)
                elif system_change.change_type == 'code':
                    self._rollback_code_change(system_change)

                rollback_history.success = True
                self.logger.info(f"Rollback successful for change ID: {system_change_id}")

            except Exception as e:
                rollback_history.success = False
                rollback_history.error_message = str(e)
                self.logger.error(f"Rollback failed for change ID: {system_change_id}: {str(e)}")

            db.session.add(rollback_history)
            db.session.commit()
            return rollback_history

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error executing rollback: {str(e)}")
            raise

    def _rollback_database_change(self, system_change: SystemChange):
        """データベース変更のロールバック処理"""
        if not system_change.change_metadata:
            raise ValueError("ロールバックに必要なメタデータがありません。")

        try:
            # メタデータから必要な情報を取得
            table_name = system_change.change_metadata.get('table_name')
            operation = system_change.change_metadata.get('operation')
            backup_data = system_change.change_metadata.get('backup_data')

            if not all([table_name, operation, backup_data]):
                raise ValueError("必要なメタデータが不足しています。")

            # ロールバック処理の実装
            # 注意: 直接的なSQLの実行は避け、ORMを使用
            if operation == 'update':
                self._restore_from_backup(table_name, backup_data)
            elif operation == 'schema_change':
                self._reverse_schema_change(table_name, backup_data)

        except Exception as e:
            raise Exception(f"データベースのロールバック中にエラーが発生しました: {str(e)}")

    def _rollback_config_change(self, system_change: SystemChange):
        """設定変更のロールバック処理"""
        if not system_change.change_metadata:
            raise ValueError("ロールバックに必要なメタデータがありません。")

        try:
            # メタデータから以前の設定を復元
            previous_config = system_change.change_metadata.get('previous_config')
            config_path = system_change.change_metadata.get('config_path')

            if not all([previous_config, config_path]):
                raise ValueError("必要なメタデータが不足しています。")

            # 設定ファイルを以前の状態に復元
            with open(config_path, 'w') as f:
                json.dump(previous_config, f, indent=4, ensure_ascii=False)

        except Exception as e:
            raise Exception(f"設定のロールバック中にエラーが発生しました: {str(e)}")

    def _rollback_code_change(self, system_change: SystemChange):
        """コード変更のロールバック処理"""
        if not system_change.change_metadata:
            raise ValueError("ロールバックに必要なメタデータがありません。")

        try:
            # メタデータからコードの変更情報を取得
            file_path = system_change.change_metadata.get('file_path')
            previous_content = system_change.change_metadata.get('previous_content')

            if not all([file_path, previous_content]):
                raise ValueError("必要なメタデータが不足しています。")

            # ファイルを以前の状態に復元
            with open(file_path, 'w') as f:
                f.write(previous_content)

        except Exception as e:
            raise Exception(f"コードのロールバック中にエラーが発生しました: {str(e)}")

    def _restore_from_backup(self, table_name: str, backup_data: dict):
        """バックアップデータからのリストア処理"""
        # ORMを使用してデータを復元
        model = db.Model._decl_class_registry.get(table_name)
        if not model:
            raise ValueError(f"テーブル {table_name} のモデルが見つかりません。")

        try:
            for record in backup_data:
                instance = model(**record)
                db.session.merge(instance)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"バックアップからのリストア中にエラーが発生しました: {str(e)}")

    def _reverse_schema_change(self, table_name: str, schema_info: dict):
        """スキーマ変更の巻き戻し処理"""
        # マイグレーションツールを使用してスキーマを元に戻す
        try:
            # スキーマの変更を元に戻すマイグレーションを生成
            from flask_migrate import migrate
            migrate(message=f"Rollback schema changes for {table_name}")
        except Exception as e:
            raise Exception(f"スキーマ変更の巻き戻し中にエラーが発生しました: {str(e)}")
