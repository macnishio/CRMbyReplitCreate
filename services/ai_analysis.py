from anthropic import Anthropic
from models import Lead, Email, SystemChange, BehaviorPattern
from datetime import datetime
import json
import logging
from sqlalchemy import desc
from typing import Dict, Any, List, Optional
from extensions import db

class AIAnalysisService:
    def __init__(self, user_settings=None):
        self.logger = logging.getLogger(__name__)
        self.user_settings = user_settings
        if user_settings and user_settings.claude_api_key:
            try:
                self.anthropic = Anthropic(api_key=user_settings.claude_api_key)
                self.logger.info("AIAnalysisService initialized successfully with Claude API")
            except Exception as e:
                self.anthropic = None
                self.logger.error(f"Failed to initialize Anthropic client: {str(e)}")
        else:
            self.anthropic = None
            self.logger.warning("AIAnalysisService initialized without valid Claude API key")
        self.MAX_EMAILS_FULL_CONTENT = 20
        self.MAX_EMAILS_SUMMARY = 100
        self.MAX_CONTENT_LENGTH = 500

    def _truncate_content(self, content: str, max_length: int = 500) -> str:
        """コンテンツを指定された長さに制限"""
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."

    def _prepare_email_history(self, emails: List[Email], lead_email: str) -> tuple[List[Dict], List[Dict]]:
        """分析用のメール履歴を準備"""
        detailed_history = []
        summary_history = []

        for email in emails[:self.MAX_EMAILS_FULL_CONTENT]:
            detailed_history.append({
                "date": email.received_date.isoformat(),
                "is_from_lead": email.sender == lead_email,
                "content": self._truncate_content(email.content),
                "subject": email.subject if hasattr(email, 'subject') else None
            })

        for email in emails[self.MAX_EMAILS_FULL_CONTENT:self.MAX_EMAILS_SUMMARY]:
            summary_history.append({
                "date": email.received_date.isoformat(),
                "is_from_lead": email.sender == lead_email
            })

        return detailed_history, summary_history

    def _build_analysis_prompt(self, lead: Lead, emails: List[Email]) -> str:
        """分析用のプロンプトを構築"""
        detailed_history, summary_history = self._prepare_email_history(emails, lead.email)

        total_emails = len(emails)
        leads_emails = sum(1 for e in emails if e.sender == lead.email)
        system_emails = total_emails - leads_emails

        prompt = f"""
リードの行動パターンを分析し、以下の形式でJSONレスポンスを生成してください：

基本情報：
- 名前: {lead.name}
- メール: {lead.email}
- ステータス: {lead.status}
- 総メール数: {total_emails}件（リードから: {leads_emails}件、システムから: {system_emails}件）
- 期間: {emails[0].received_date.strftime('%Y-%m-%d')}から{emails[-1].received_date.strftime('%Y-%m-%d')}

詳細なメール履歴（直近{len(detailed_history)}件）：
{json.dumps(detailed_history, ensure_ascii=False, indent=2)}

追加の履歴概要（次の{len(summary_history)}件の送受信情報）：
{json.dumps(summary_history, ensure_ascii=False, indent=2)}

全期間の通信パターンを分析し、以下の形式でJSONレスポンスを生成してください：
{{
    "communication_pattern": {{
        "frequency": "選択：高/中/低",
        "response_time": "平均応答時間の推定",
        "preferred_time": "連絡の多い時間帯",
        "communication_style": "コミュニケーションスタイルの特徴"
    }},
    "engagement_level": {{
        "score": "1-10の数値で評価",
        "trend": "選択：上昇/横ばい/下降",
        "key_factors": ["主な要因を2-3項目"]
    }},
    "interests": {{
        "primary": ["主要な関心事を2-3項目"],
        "secondary": ["副次的な関心事を1-2項目"]
    }},
    "pain_points": {{
        "identified": ["確認された課題を2-3項目"],
        "potential": ["潜在的な課題を1-2項目"]
    }},
    "recommendations": {{
        "next_actions": ["具体的な行動提案を2-3項目"],
        "timing": "次のアクションの推奨タイミング",
        "approach": "推奨されるアプローチ方法の説明"
    }},
    "response_patterns": {{
        "weekday_preference": "平日/週末の傾向",
        "time_zone_pattern": "時間帯の傾向",
        "response_consistency": "応答の一貫性（高/中/低）"
    }}
}}

分析の注意点：
- 全期間のコミュニケーションパターンを考慮してください
- 最新の{len(detailed_history)}件の詳細内容と、追加の{len(summary_history)}件の送受信パターンを総合的に分析してください
- トレンドの変化や長期的なパターンに注目してください
- 具体的で実用的な提案を心がけてください
- 時間帯や曜日のパターンも考慮してください
"""
        return prompt

    def analyze_lead_behavior(self, lead_id: int) -> Dict[str, Any]:
        """リードの行動パターンを分析"""
        try:
            lead = Lead.query.get(lead_id)
            if not lead:
                return {
                    "error": "指定されたリードが見つかりません",
                    "success": False
                }

            emails = Email.query.filter_by(lead_id=lead_id).order_by(desc(Email.received_date)).all()
            
            if not emails:
                return {
                    "error": "分析するメール履歴がありません",
                    "success": False
                }

            if not self.anthropic:
                self.logger.error("Cannot analyze lead behavior: Anthropic client not initialized")
                return {
                    "error": "AI分析を実行するにはAPIキーの設定が必要です",
                    "success": False,
                    "details": "Claude API key is not configured or invalid"
                }

            prompt = self._build_analysis_prompt(lead, emails)

            try:
                response = self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4000,
                    temperature=0,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            except Exception as api_error:
                self.logger.error(f"Claude API error: {str(api_error)}")
                return {
                    "error": "AI分析中にエラーが発生しました",
                    "details": str(api_error),
                    "success": False
                }

            content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("JSON形式の応答が見つかりません")

            json_content = content[json_start:json_end]
            analysis_result = json.loads(json_content)

            self._save_analysis_result(lead_id, analysis_result)
            self._update_behavior_patterns(lead, analysis_result)

            formatted_result = {
                'success': True,
                'data': {
                    'communication_patterns': {
                        'frequency': analysis_result['communication_pattern']['frequency'],
                        'preferred_time': analysis_result['communication_pattern']['preferred_time'],
                        'response_time': analysis_result['communication_pattern']['response_time'],
                        'engagement_level': str(analysis_result['engagement_level']['score']) + '/10'
                    },
                    'interests': analysis_result['interests']['primary'] + analysis_result['interests']['secondary'],
                    'key_points': [
                        *analysis_result['communication_pattern']['communication_style'].split(', '),
                        f"エンゲージメント傾向: {analysis_result['engagement_level']['trend']}"
                    ],
                    'risk_factors': analysis_result['pain_points']['identified'] + analysis_result['pain_points']['potential'],
                    'recommended_actions': analysis_result['recommendations']['next_actions'],
                    'analysis_summary': f"推奨アプローチ: {analysis_result['recommendations']['approach']}\n"
                                    f"最適なタイミング: {analysis_result['recommendations']['timing']}"
                }
            }

            return formatted_result

        except Exception as e:
            self.logger.error(f"行動パターン分析中にエラーが発生: {str(e)}")
            return {
                "error": "分析中にエラーが発生しました",
                "details": str(e),
                "success": False
            }

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
            db.session.add(system_change)
            db.session.commit()
        except Exception as e:
            self.logger.error(f"分析結果の保存中にエラーが発生: {str(e)}")
            db.session.rollback()

    def _update_behavior_patterns(self, lead: Lead, analysis_result: Dict[str, Any]) -> None:
        """行動パターンの更新"""
        try:
            BehaviorPattern.query.filter_by(lead_id=lead.id).delete()

            patterns = [
                ('communication_frequency', analysis_result['communication_pattern']['frequency']),
                ('response_time', analysis_result['communication_pattern']['response_time']),
                ('preferred_time', analysis_result['communication_pattern']['preferred_time']),
                ('engagement_trend', analysis_result['engagement_level']['trend']),
                ('response_consistency', analysis_result['response_patterns']['response_consistency']),
                ('weekday_preference', analysis_result['response_patterns']['weekday_preference']),
                ('time_zone_pattern', analysis_result['response_patterns']['time_zone_pattern'])
            ]

            for pattern_type, value in patterns:
                pattern = BehaviorPattern(
                    lead_id=lead.id,
                    pattern_type=f"{pattern_type}:{value}"
                )
                db.session.add(pattern)

            for interest in analysis_result['interests']['primary']:
                pattern = BehaviorPattern(
                    lead_id=lead.id,
                    pattern_type=f"primary_interest:{interest}"
                )
                db.session.add(pattern)

            for interest in analysis_result['interests']['secondary']:
                pattern = BehaviorPattern(
                    lead_id=lead.id,
                    pattern_type=f"secondary_interest:{interest}"
                )
                db.session.add(pattern)

            db.session.commit()
        except Exception as e:
            self.logger.error(f"行動パターンの更新中にエラーが発生: {str(e)}")
            db.session.rollback()
