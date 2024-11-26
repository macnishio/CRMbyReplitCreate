from anthropic import Anthropic
from models import Lead, Email, SystemChange
from datetime import datetime
import json
import logging
from sqlalchemy import desc
from typing import Dict, Any, List, Optional

class AIAnalysisService:
    def __init__(self, user_settings=None):
        self.anthropic = Anthropic(api_key=user_settings.claude_api_key if user_settings else None)
        self.logger = logging.getLogger(__name__)

    def analyze_lead_behavior(self, lead_id: int) -> Dict[str, Any]:
        """リードの行動パターンを分析"""
        try:
            # リードの基本情報を取得
            lead = Lead.query.get(lead_id)
            if not lead:
                return {"error": "リードが見つかりません"}

            # メール履歴を取得
            emails = Email.query.filter_by(lead_id=lead_id).order_by(desc(Email.received_date)).all()
            
            if not emails:
                return {"error": "分析するメール履歴がありません"}

            # 分析用のプロンプトを構築
            prompt = self._build_analysis_prompt(lead, emails)

            # Claude APIを使用して分析
            response = self.anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # レスポンスをパース
            content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
            analysis_result = json.loads(content)

            # 分析結果を保存
            self._save_analysis_result(lead_id, analysis_result)

            return analysis_result

        except Exception as e:
            self.logger.error(f"行動パターン分析中にエラーが発生: {str(e)}")
            return {
                "error": "分析中にエラーが発生しました",
                "details": str(e)
            }

    def _build_analysis_prompt(self, lead: Lead, emails: List[Email]) -> str:
        """分析用のプロンプトを構築"""
        email_history = [
            {
                "date": email.received_date.isoformat(),
                "is_from_lead": email.sender == lead.email,
                "content": email.content
            }
            for email in emails
        ]

        return f"""
        以下のリードの行動パターンを分析し、JSONフォーマットで詳細な分析結果を提供してください：

        リード情報：
        - 名前: {lead.name}
        - メール: {lead.email}
        - ステータス: {lead.status}
        - スコア: {lead.score}
        - 作成日: {lead.created_at.isoformat() if lead.created_at else 'N/A'}
        - 最終接触: {lead.last_contact.isoformat() if lead.last_contact else 'N/A'}

        コミュニケーション履歴：
        {json.dumps(email_history, ensure_ascii=False, indent=2)}

        以下の観点から分析を行い、JSON形式で応答してください：
        {
            "communication_pattern": {
                "frequency": "高/中/低",
                "response_time": "平均応答時間（時間）",
                "preferred_time": "よく連絡を取る時間帯",
                "communication_style": "コミュニケーションスタイルの特徴"
            },
            "engagement_level": {
                "score": 1-10,
                "trend": "上昇/横ばい/下降",
                "key_factors": ["要因1", "要因2"]
            },
            "interests": {
                "primary": ["主要な関心事1", "主要な関心事2"],
                "secondary": ["副次的な関心事1", "副次的な関心事2"]
            },
            "pain_points": {
                "identified": ["課題1", "課題2"],
                "potential": ["潜在的な課題1", "潜在的な課題2"]
            },
            "recommendations": {
                "next_actions": ["推奨アクション1", "推奨アクション2"],
                "timing": "最適なフォローアップのタイミング",
                "approach": "推奨されるアプローチ方法"
            }
        }
        """

    def _save_analysis_result(self, lead_id: int, analysis_result: Dict[str, Any]) -> None:
        """分析結果をシステム変更として保存"""
        try:
            system_change = SystemChange(
                change_type='ai_analysis',
                description=f'Lead {lead_id} behavior analysis',
                change_metadata={
                    'lead_id': lead_id,
                    'analysis_result': analysis_result,
                    'analyzed_at': datetime.utcnow().isoformat()
                }
            )
            from extensions import db
            db.session.add(system_change)
            db.session.commit()
        except Exception as e:
            self.logger.error(f"分析結果の保存中にエラーが発生: {str(e)}")
