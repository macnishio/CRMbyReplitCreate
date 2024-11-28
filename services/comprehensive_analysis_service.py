from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import Counter
from models import Task, Opportunity, Schedule, Email
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