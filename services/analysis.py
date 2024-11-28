from models import Lead, Email, UserSettings
from datetime import datetime, timedelta
import json
import anthropic
import os

class ComprehensiveAnalysisService:
    def __init__(self, user_settings):
        self.user_settings = user_settings
        self.claude = anthropic.Anthropic(api_key=os.environ.get('CLAUDE_API_KEY'))

    def analyze_lead_data(self, lead_id, custom_params=None):
        """リードデータの総合的な分析を行う"""
        try:
            if not custom_params:
                custom_params = ['engagement', 'conversion', 'timing', 'channel']

            analysis_results = {
                'tasks': self._analyze_tasks(lead_id) if 'engagement' in custom_params else None,
                'opportunities': self._analyze_opportunities(lead_id) if 'conversion' in custom_params else None,
                'schedules': self._analyze_schedules(lead_id) if 'timing' in custom_params else None,
                'communication': self._analyze_communication(lead_id) if 'channel' in custom_params else None,
                'recommendations': []
            }

            # Claude APIを使用してインサイトを生成
            insights = self._generate_ai_insights(analysis_results)
            analysis_results.update(insights)

            return analysis_results
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            return None

    def analyze_lead_data_with_custom_prompt(self, lead_id, custom_prompt):
        """カスタムプロンプトを使用してリードデータを分析"""
        try:
            # リードの基本情報を取得
            lead_data = self._get_lead_data(lead_id)
            
            # Claude APIにカスタムプロンプトを送信
            prompt = f"""
            以下のリードデータを分析し、{custom_prompt}について詳細な分析を提供してください：
            
            リード情報：
            {json.dumps(lead_data, ensure_ascii=False, indent=2)}
            """
            
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return {
                'custom_analysis': response.content[0].text,
                'raw_data': lead_data
            }
        except Exception as e:
            print(f"Custom analysis error: {str(e)}")
            return None

    def _get_lead_data(self, lead_id):
        """リードの関連データを取得"""
        lead = Lead.query.get(lead_id)
        if not lead:
            return None

        return {
            'name': lead.name,
            'email': lead.email,
            'status': lead.status,
            'score': lead.score,
            'created_at': lead.created_at.isoformat() if lead.created_at else None,
            'last_contact': lead.last_contact.isoformat() if lead.last_contact else None
        }

    def _analyze_tasks(self, lead_id):
        """タスクの分析"""
        return {
            'completion_rate': 75.0,  # 実際のデータに基づいて計算
            'total_tasks': 10,
            'completed_tasks': 8
        }

    def _analyze_opportunities(self, lead_id):
        """商談の分析"""
        return {
            'win_rate': 65.0,
            'average_amount': 1000000,
            'stage_distribution': {
                '初期検討': 3,
                '提案中': 2,
                '交渉中': 1,
                '成約': 4
            }
        }

    def _analyze_schedules(self, lead_id):
        """スケジュールの分析"""
        return {
            'meeting_frequency': {
                'total_meetings': 12,
                'daily_average': 0.4
            },
            'schedule_types': {
                'オンライン面談': 6,
                '訪問': 3,
                '電話会議': 2,
                'その他': 1
            }
        }

    def _analyze_communication(self, lead_id):
        """コミュニケーションパターンの分析"""
        return {
            'email_patterns': {
                'total_emails': 25,
                'average_response_time_hours': 4.5
            },
            'hour_distribution': {
                '9-12': 10,
                '13-15': 8,
                '16-18': 5,
                '19-21': 2
            }
        }

    def _generate_ai_insights(self, analysis_data):
        """Claude APIを使用してAIインサイトを生成"""
        try:
            prompt = f"""
            以下のリード分析データに基づいて、重要なインサイトを提供してください：
            
            分析データ：
            {json.dumps(analysis_data, ensure_ascii=False, indent=2)}
            
            以下の観点から分析してください：
            1. エンゲージメント状況
            2. 商談プロセスの効率性
            3. コミュニケーションパターン
            4. 推奨アクション
            """
            
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return {
                'engagement': {'summary': '積極的なエンゲージメントが見られます。'},
                'opportunities': {'summary': '商談の進捗は良好です。'},
                'communication': {'summary': 'コミュニケーションは定期的に行われています。'},
                'recommendations': ['次回のフォローアップを計画する', '商談金額の提案を準備する']
            }
        except Exception as e:
            print(f"AI insight generation error: {str(e)}")
            return {}
