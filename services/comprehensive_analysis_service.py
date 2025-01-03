from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import Counter
from models import Task, Opportunity, Schedule, Email
from models import UserSettings
from flask_login import current_user
from anthropic import Anthropic, APIError, APIConnectionError, AuthenticationError
from flask import current_app

class ComprehensiveAnalysisService:
    def __init__(self, user_settings=None):
        self.user_settings = user_settings
    def analyze_lead_data(self, lead_id: int) -> Dict[str, Any]:
        """リード固有のデータ分析"""
        # リードに関連するデータを取得
        tasks = Task.query.filter_by(lead_id=lead_id).all()
        opportunities = Opportunity.query.filter_by(lead_id=lead_id).all()
        schedules = Schedule.query.filter_by(lead_id=lead_id).all()
        emails = Email.query.filter_by(lead_id=lead_id).all()

        analysis_results = {
            "tasks": self._analyze_lead_tasks(tasks),
            "opportunities": self._analyze_lead_opportunities(opportunities),
            "schedules": self._analyze_lead_schedules(schedules),
            "communication": self._analyze_lead_communication(emails)
        }

        return analysis_results

    def analyze_lead_data_with_custom_prompt(self, lead_id: int, custom_prompt: str) -> Dict[str, Any]:
        """カスタムプロンプトを使用したリードデータの分析"""
        # リードに関連するデータを取得
        tasks = Task.query.filter_by(lead_id=lead_id).all()
        opportunities = Opportunity.query.filter_by(lead_id=lead_id).all()
        schedules = Schedule.query.filter_by(lead_id=lead_id).all()
        emails = Email.query.filter_by(lead_id=lead_id).all()

        # 基本的な分析結果を取得
        analysis_results = {
            "tasks": self._analyze_lead_tasks(tasks),
            "opportunities": self._analyze_lead_opportunities(opportunities),
            "schedules": self._analyze_lead_schedules(schedules),
            "communication": self._analyze_lead_communication(emails)
        }

        # カスタムプロンプトを使用した分析を追加
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=self.user_settings.claude_api_key)

            # データを文字列に変換
            data_str = f"""
            タスク情報:
            {', '.join(f'{t.title}（{t.status}）' for t in tasks)}
            
            商談情報:
            {', '.join(f'{o.name}（{o.stage}、¥{o.amount}）' for o in opportunities)}
            
            スケジュール情報:
            {', '.join(f'{s.title}（{s.start_time}～{s.end_time}）' for s in schedules)}
            
            コミュニケーション履歴:
            最近のメール数: {len(emails)}件
            """

            # カスタムプロンプトを使用してAI分析を実行
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{
                    "role": "user", 
                    "content": f"""以下のデータを分析し、{custom_prompt}について詳しく説明してください：\n\n{data_str}"""
                }]
            )

            if message and hasattr(message.content[0], 'text'):
                analysis_results["custom_analysis"] = message.content[0].text
            else:
                analysis_results["custom_analysis"] = "カスタム分析の実行中にエラーが発生しました。"

        except Exception as e:
            analysis_results["custom_analysis"] = f"分析中にエラーが発生しました: {str(e)}"

        return analysis_results

    def _analyze_with_custom_params(self, tasks, opportunities, schedules, emails, custom_params):
        """カスタムパラメータを使用した特定の分析を実行"""
        analysis_results = {}
        
        if "engagement" in custom_params:
            # エンゲージメント分析
            email_frequency = len(emails) / 30 if emails else 0  # 月平均
            response_rate = len([e for e in emails if e.is_reply]) / len(emails) if emails else 0
            analysis_results["engagement"] = {
                "email_frequency": email_frequency,
                "response_rate": response_rate
            }
            
        if "conversion" in custom_params:
            # コンバージョン可能性分析
            won_opps = len([o for o in opportunities if o.stage == "Won"])
            total_opps = len(opportunities)
            conversion_rate = won_opps / total_opps if total_opps > 0 else 0
            analysis_results["conversion"] = {
                "conversion_rate": conversion_rate,
                "total_opportunities": total_opps
            }
            
        if "timing" in custom_params:
            # 最適アプローチタイミング分析
            if emails:
                response_times = []
                for i in range(1, len(emails)):
                    if emails[i].is_reply and emails[i-1].received_date:
                        time_diff = emails[i].received_date - emails[i-1].received_date
                        response_times.append(time_diff.total_seconds() / 3600)  # 時間単位
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                analysis_results["timing"] = {
                    "average_response_time": avg_response_time
                }
                
        if "channel" in custom_params:
            # コミュニケーションチャネル分析
            email_count = len(emails)
            meeting_count = len([s for s in schedules if "meeting" in s.title.lower()])
            analysis_results["channel"] = {
                "email_count": email_count,
                "meeting_count": meeting_count
            }
            
        return analysis_results

    def _analyze_lead_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """リードに関連するタスクの分析"""
        if not tasks:
            return {"status": "no_data", "message": "タスクデータがありません"}

        completed_tasks = len([t for t in tasks if t.completed])
        total_tasks = len(tasks)
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # タスクのステータス分布を集計
        status_distribution = Counter(t.status for t in tasks)

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate,
            "status_distribution": dict(status_distribution)
        }

    def _analyze_lead_opportunities(self, opportunities: List[Opportunity]) -> Dict[str, Any]:
        """リードに関連する商談の分析"""
        if not opportunities:
            return {"status": "no_data", "message": "商談データがありません"}

        total_amount = sum(o.amount for o in opportunities if o.amount)
        stages = Counter(o.stage for o in opportunities)

        return {
            "total_opportunities": len(opportunities),
            "total_amount": total_amount,
            "stage_distribution": dict(stages),
            "average_amount": total_amount / len(opportunities) if opportunities else 0
        }

    def _analyze_lead_schedules(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """リードに関連するスケジュールの分析"""
        if not schedules:
            return {"status": "no_data", "message": "スケジュールデータがありません"}

        # スケジュールのステータス分布
        status_distribution = Counter(s.status for s in schedules)

        # 最近のスケジュール
        recent_schedules = [s for s in schedules if s.start_time >= datetime.now() - timedelta(days=30)]

        # 時間帯別の分布
        time_slots = {
            "morning": 0,   # 6-12
            "afternoon": 0, # 12-18
            "evening": 0,   # 18-24
            "night": 0      # 0-6
        }

        for schedule in schedules:
            hour = schedule.start_time.hour
            if 6 <= hour < 12:
                time_slots["morning"] += 1
            elif 12 <= hour < 18:
                time_slots["afternoon"] += 1
            elif 18 <= hour < 24:
                time_slots["evening"] += 1
            else:
                time_slots["night"] += 1

        return {
            "total_schedules": len(schedules),
            "recent_schedules": len(recent_schedules),
            "status_distribution": dict(status_distribution),
            "time_distribution": time_slots,
            "upcoming_schedules": len([s for s in schedules if s.start_time > datetime.now()])
        }

    def _analyze_lead_communication(self, emails: List[Email]) -> Dict[str, Any]:
        """リードとのコミュニケーション分析"""
        if not emails:
            return {"status": "no_data", "message": "メールデータがありません"}

        # メールの総数
        total_emails = len(emails)

        # 送受信の判定（送信者がユーザーかリードかで判断）
        sent_emails = len([e for e in emails if e.user_id])
        received_emails = total_emails - sent_emails

        # 最後のコンタクト日時
        last_contact = max(e.received_date for e in emails) if emails else None

        return {
            "total_emails": total_emails,
            "sent_emails": sent_emails,
            "received_emails": received_emails,
            "last_contact": last_contact
        }

    def generate_lead_analysis(self, lead_id: int) -> Dict[str, Any]:
        """リードの包括的な分析を生成"""
        analysis_data = self.analyze_lead_data(lead_id)

        prompt = f"""
        以下のリードデータに基づいて、包括的な分析とインサイトを提供してください。
        JSONフォーマットで応答してください。

        分析データ:
        {json.dumps(analysis_data, indent=2, ensure_ascii=False)}

        以下の観点から分析を行ってください：
        1. エンゲージメント状況
        2. 商談の可能性
        3. コミュニケーションパターン
        4. 改善のための推奨事項
        5. リスクと機会の特定
        """

        try:
            response = self.anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            ai_analysis = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])

            return {
                "raw_data": analysis_data,
                "ai_insights": ai_analysis
            }
        except Exception as e:
            return {
                "raw_data": analysis_data,
                "error": f"AI分析の生成中にエラーが発生しました: {str(e)}"
            }

def analyze_custom_prompt(custom_prompt):
    """ユーザーのカスタムプロンプトをAIに渡して分析結果を取得します"""
    try:
        # ユーザー設定の取得
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'

        # Anthropicクライアントの初期化
        client = Anthropic(api_key=user_settings.claude_api_key)

        # ユーザーのカスタムプロンプトをそのまま使用
        prompt = custom_prompt

        # APIリクエストの送信
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        # AIからの応答を取得
        if message and hasattr(message.content[0], 'text'):
            content = message.content[0].text
            # 必要に応じてHTMLフォーマットを適用
            if not content.startswith('<p>'):
                content = '<p>' + content.replace('\n\n', '</p><p>') + '</p>'
            return content
        else:
            return '<p>AI分析の結果を取得できませんでした。</p>'

    except Exception as e:
        return handle_ai_error("analyze_custom_prompt", e)

def handle_ai_error(func_name, error):
    """Handle AI analysis errors with proper logging and localized messages"""
    error_msg = None
    if isinstance(error, AuthenticationError):
        error_msg = "APIキーが無効です。システム管理者に連絡してください。"
        current_app.logger.error(f"{func_name}: Invalid API key - {str(error)}")
    elif isinstance(error, APIConnectionError):
        error_msg = "AI分析サービスに接続できません。しばらく待ってから再試行してください。"
        current_app.logger.error(f"{func_name}: Connection error - {str(error)}")
    elif isinstance(error, APIError):
        error_msg = "AI分析中にエラーが発生しました。しばらく待ってから再試行してください。"
        current_app.logger.error(f"{func_name}: API error - {str(error)}")
    else:
        error_msg = "予期せぬエラーが発生しました。システム管理者に連絡してください。"
        current_app.logger.error(f"{func_name}: Unexpected error - {str(error)}")
    return f'<p class="error-message">{error_msg}</p>'
