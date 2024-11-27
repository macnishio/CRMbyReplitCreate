import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import func
from models import Task, Opportunity, Schedule, Email, Lead
from extensions import db
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

class ComprehensiveAnalysisService:
    def __init__(self, user_settings=None):
        """Initialize ComprehensiveAnalysisService with user settings"""
        self.anthropic = Anthropic(api_key=user_settings.claude_api_key if user_settings else os.environ.get('CLAUDE_API_KEY'))

    def analyze_tasks(self, user_id: int) -> Dict[str, Any]:
        """タスクデータの分析"""
        tasks = Task.query.filter_by(user_id=user_id).all()
        total_tasks = len(tasks)
        if not total_tasks:
            return {"error": "タスクデータが見つかりません"}

        completed_tasks = len([t for t in tasks if t.completed])
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        # タスク種類別の集計
        task_types = db.session.query(
            Task.task_type,
            func.count(Task.id)
        ).filter_by(user_id=user_id).group_by(Task.task_type).all()

        # 優先度分布
        priority_distribution = db.session.query(
            Task.priority,
            func.count(Task.id)
        ).filter_by(user_id=user_id).group_by(Task.priority).all()

        return {
            "completion_rate": completion_rate,
            "task_types": dict(task_types),
            "priority_distribution": dict(priority_distribution),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks
        }

    def analyze_opportunities(self, user_id: int) -> Dict[str, Any]:
        """商談データの分析"""
        opportunities = Opportunity.query.filter_by(user_id=user_id).all()
        if not opportunities:
            return {"error": "商談データが見つかりません"}

        # ステージ分布
        stage_distribution = db.session.query(
            Opportunity.stage,
            func.count(Opportunity.id)
        ).filter_by(user_id=user_id).group_by(Opportunity.stage).all()

        # 成約率の計算
        total_opps = len(opportunities)
        closed_won = len([o for o in opportunities if o.stage == 'Closed Won'])
        win_rate = (closed_won / total_opps) * 100 if total_opps > 0 else 0

        # 金額分析
        total_amount = sum(o.amount for o in opportunities if o.amount)
        avg_amount = total_amount / total_opps if total_opps > 0 else 0
        
        # ステージ別の合計金額
        amount_by_stage = db.session.query(
            Opportunity.stage,
            func.sum(Opportunity.amount)
        ).filter_by(user_id=user_id).group_by(Opportunity.stage).all()

        return {
            "stage_distribution": dict(stage_distribution),
            "win_rate": win_rate,
            "total_opportunities": total_opps,
            "total_amount": total_amount,
            "average_amount": avg_amount,
            "amount_by_stage": dict(amount_by_stage)
        }

    def analyze_schedules(self, user_id: int) -> Dict[str, Any]:
        """スケジュールデータの分析"""
        now = datetime.utcnow()
        last_month = now - timedelta(days=30)
        
        schedules = Schedule.query.filter(
            Schedule.user_id == user_id,
            Schedule.start_time >= last_month
        ).all()

        if not schedules:
            return {"error": "スケジュールデータが見つかりません"}

        # ミーティング頻度（過去30日間）
        meeting_count = len(schedules)
        daily_avg = meeting_count / 30

        # スケジュール種類別の分布
        schedule_types = db.session.query(
            Schedule.schedule_type,
            func.count(Schedule.id)
        ).filter_by(user_id=user_id).group_by(Schedule.schedule_type).all()

        # 顧客別のコンタクト頻度
        contact_frequency = db.session.query(
            Schedule.lead_id,
            func.count(Schedule.id)
        ).filter(
            Schedule.user_id == user_id,
            Schedule.lead_id.isnot(None)
        ).group_by(Schedule.lead_id).all()

        return {
            "meeting_frequency": {
                "total_meetings": meeting_count,
                "daily_average": daily_avg
            },
            "schedule_types": dict(schedule_types),
            "contact_frequency": dict(contact_frequency)
        }

    def analyze_communication_patterns(self, user_id: int) -> Dict[str, Any]:
        """メールとコミュニケーションパターンの分析"""
        emails = Email.query.filter_by(user_id=user_id).all()
        if not emails:
            return {"error": "メールデータが見つかりません"}

        # メールの送受信パターン分析
        total_emails = len(emails)
        sent_emails = len([e for e in emails if e.is_sent])
        received_emails = total_emails - sent_emails

        # 応答時間の分析
        response_times = []
        for email in emails:
            if email.response_to_id:
                original_email = Email.query.get(email.response_to_id)
                if original_email:
                    response_time = (email.timestamp - original_email.timestamp).total_seconds() / 3600
                    response_times.append(response_time)

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # 時間帯別のメール頻度
        hour_distribution = db.session.query(
            func.extract('hour', Email.timestamp),
            func.count(Email.id)
        ).filter_by(user_id=user_id).group_by(
            func.extract('hour', Email.timestamp)
        ).all()

        return {
            "email_patterns": {
                "total_emails": total_emails,
                "sent_emails": sent_emails,
                "received_emails": received_emails,
                "average_response_time_hours": avg_response_time
            },
            "hour_distribution": dict(hour_distribution)
        }

    def generate_comprehensive_analysis(self, user_id: int) -> Dict[str, Any]:
        """包括的な顧客行動分析を生成"""
        task_analysis = self.analyze_tasks(user_id)
        opportunity_analysis = self.analyze_opportunities(user_id)
        schedule_analysis = self.analyze_schedules(user_id)
        communication_analysis = self.analyze_communication_patterns(user_id)

        # AIによる総合分析
        analysis_data = {
            "tasks": task_analysis,
            "opportunities": opportunity_analysis,
            "schedules": schedule_analysis,
            "communication": communication_analysis
        }

        prompt = f"""
        以下のデータに基づいて、包括的な顧客行動分析とビジネスインサイトを提供してください。
        JSONフォーマットで応答してください。

        タスクデータ:
        - 完了率: {task_analysis.get('completion_rate')}%
        - タスク種類別傾向: {task_analysis.get('task_types')}
        - 優先度分布: {task_analysis.get('priority_distribution')}

        商談データ:
        - ステージ分布: {opportunity_analysis.get('stage_distribution')}
        - 成約率: {opportunity_analysis.get('win_rate')}%
        - 平均商談金額: {opportunity_analysis.get('average_amount')}

        スケジュールデータ:
        - ミーティング頻度: {schedule_analysis.get('meeting_frequency')}
        - スケジュール種類: {schedule_analysis.get('schedule_types')}

        コミュニケーションデータ:
        - メール総数: {communication_analysis.get('email_patterns', {}).get('total_emails')}
        - 平均応答時間: {communication_analysis.get('email_patterns', {}).get('average_response_time_hours')}時間

        以下の観点から分析を行ってください：
        1. 全体的な顧客エンゲージメント状況
        2. 商談プロセスの効率性
        3. コミュニケーションパターンの特徴
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
                "ai_insights": str(e),
                "error": "AI分析の生成中にエラーが発生しました"
            }
