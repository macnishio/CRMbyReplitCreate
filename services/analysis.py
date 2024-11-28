from datetime import datetime, timedelta
import json
from flask import current_app
from anthropic import Anthropic
from models import Lead, Email, Opportunity, Task, Schedule
from extensions import db
import re

class LeadAnalysisService:
    def __init__(self):
        self.claude = Anthropic(api_key=current_app.config['CLAUDE_API_KEY'])

    def analyze_lead(self, lead_id: int, custom_prompt: str = '', 
                    analyze_engagement: bool = True, 
                    analyze_conversion: bool = True) -> dict:
        """リードの包括的な分析を実行"""
        try:
            lead = Lead.query.get(lead_id)
            if not lead:
                return None

            # 基本データの収集
            analysis_data = self._collect_lead_data(lead)

            # カスタムプロンプトの準備
            prompt = self._prepare_analysis_prompt(
                analysis_data, 
                custom_prompt,
                analyze_engagement,
                analyze_conversion
            )

            # Claude APIによる分析
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            if not response.content:
                return None

            # 分析結果の処理
            analysis_result = self._process_analysis_response(response.content[0].text)
            
            # 分析結果の保存
            self._save_analysis_results(lead, analysis_result)
            
            return analysis_result

        except Exception as e:
            current_app.logger.error(f"Lead analysis error: {str(e)}", exc_info=True)
            return None

    def _collect_lead_data(self, lead) -> dict:
        """リードの関連データを収集"""
        now = datetime.utcnow()
        last_month = now - timedelta(days=30)

        # メールの統計
        emails = Email.query.filter_by(lead_id=lead.id).all()
        email_count = len(emails)
        recent_emails = len([e for e in emails if e.created_at > last_month])

        # 商談データ
        opportunities = Opportunity.query.filter_by(lead_id=lead.id).all()
        total_opportunity_value = sum(o.amount or 0 for o in opportunities)
        active_opportunities = len([o for o in opportunities if o.stage != 'Closed Lost'])

        # タスクとスケジュール
        tasks = Task.query.filter_by(lead_id=lead.id).all()
        schedules = Schedule.query.filter_by(lead_id=lead.id).all()
        completed_tasks = len([t for t in tasks if t.completed])

        return {
            'lead_info': {
                'name': lead.name,
                'email': lead.email,
                'status': lead.status,
                'score': lead.score,
                'created_at': lead.created_at.isoformat(),
                'last_contact': lead.last_contact.isoformat() if lead.last_contact else None
            },
            'engagement_metrics': {
                'total_emails': email_count,
                'recent_emails': recent_emails,
                'completed_tasks': completed_tasks,
                'total_tasks': len(tasks),
                'scheduled_meetings': len(schedules)
            },
            'opportunity_data': {
                'total_opportunities': len(opportunities),
                'active_opportunities': active_opportunities,
                'total_value': total_opportunity_value
            }
        }

    def _prepare_analysis_prompt(self, data: dict, custom_prompt: str,
                               analyze_engagement: bool,
                               analyze_conversion: bool) -> str:
        """分析プロンプトを生成"""
        base_prompt = f"""
以下のリードデータを分析し、ビジネス価値の高いインサイトを提供してください：

リード基本情報：
- 名前: {data['lead_info']['name']}
- ステータス: {data['lead_info']['status']}
- スコア: {data['lead_info']['score']}
- 作成日: {data['lead_info']['created_at']}
- 最終接触: {data['lead_info']['last_contact']}

エンゲージメント指標：
- 総メール数: {data['engagement_metrics']['total_emails']}
- 直近30日のメール数: {data['engagement_metrics']['recent_emails']}
- タスク完了率: {data['engagement_metrics']['completed_tasks']}/{data['engagement_metrics']['total_tasks']}
- スケジュール済みミーティング: {data['engagement_metrics']['scheduled_meetings']}

商談データ：
- 総商談数: {data['opportunity_data']['total_opportunities']}
- アクティブな商談: {data['opportunity_data']['active_opportunities']}
- 総商談金額: ¥{data['opportunity_data']['total_value']:,}

分析の観点：
1. エンゲージメントの質と傾向
2. 商談成約の可能性
3. 推奨アクションプラン

カスタムリクエスト：
{custom_prompt if custom_prompt else 'なし'}

以下の形式で分析結果を提供してください：
1. エンゲージメント状況の要約（エンゲージメントの質、頻度、トレンド）
2. 商談プロセスの効率性（進捗状況、課題、機会）
3. コミュニケーションパターンの分析
4. 具体的な推奨アクション（優先順位付き）

結果はJSON形式で返してください。
"""
        return base_prompt

    def _process_analysis_response(self, response: str) -> dict:
        """分析レスポンスを処理"""
        try:
            # レスポンスからJSONを抽出
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                return self._create_default_response()

            analysis_json = response[json_start:json_end]
            return json.loads(analysis_json)
        except Exception:
            return self._create_default_response()

    def _create_default_response(self) -> dict:
        """デフォルトの分析レスポンスを生成"""
        return {
            'engagement_status': '分析を完了できませんでした。',
            'process_efficiency': '詳細な分析が必要です。',
            'communication_patterns': '通信パターンの分析に失敗しました。',
            'recommendations': [
                'より詳細なデータ収集が必要です。',
                '手動での評価を検討してください。'
            ]
        }

    def _save_analysis_results(self, lead: Lead, analysis_result: dict) -> None:
        """分析結果をデータベースに保存"""
        try:
            # スコアの更新（オプション）
            if 'score' in analysis_result:
                lead.score = analysis_result['score']
            
            # 最終分析日時の更新
            lead.last_analysis = datetime.utcnow()
            
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error saving analysis results: {str(e)}")
            db.session.rollback()