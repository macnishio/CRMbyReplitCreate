import json
from datetime import datetime, timedelta
from models import Opportunity, Schedule, Task
from extensions import db
from anthropic import Anthropic, APIError, APIConnectionError, AuthenticationError
from flask import current_app
from models import UserSettings
from flask_login import current_user

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

def analyze_tasks(tasks):
    """Analyze tasks using Claude AI"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'
            
        client = Anthropic(api_key=user_settings.claude_api_key)

        task_data = "\n".join([
            f"- タイトル: {task.title}, 期限: {task.due_date}, ステータス: {task.status}"
            for task in tasks
        ])

        if not tasks:
            return '<p>分析対象のタスクがありません。</p>'

        prompt = f"""以下のタスクデータを分析してください:\n{task_data}\n
        以下の項目について簡潔に分析してください:
        1. タスクの優先度と進捗状況
        2. リソース配分の提案
        3. 期限管理の改善点
        4. 効率化のための提案
        回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        if message and hasattr(message.content[0], 'text'):
            content = message.content[0].text
            if not content.startswith('<p>'):
                content = '<p>' + content.replace('\n\n', '</p><p>') + '</p>'
            return content
        return '<p>AI分析の結果を取得できませんでした。</p>'

    except Exception as e:
        return handle_ai_error("analyze_tasks", e)

def analyze_schedules(schedules):
    """Analyze schedules using Claude AI"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'
            
        client = Anthropic(api_key=user_settings.claude_api_key)

        schedule_data = "\n".join([
            f"- タイトル: {sch.title}, 開始: {sch.start_time}, 終了: {sch.end_time}"
            for sch in schedules
        ])

        if not schedules:
            return '<p>分析対象のスケジュールがありません。</p>'

        prompt = f"""以下のスケジュールデータを分析してください:\n{schedule_data}\n
        以下の項目について簡潔に分析してください:
        1. スケジュールの密度と時間配分
        2. 重要な予定の特定
        3. スケジュール管理の効率化
        4. バランス改善のための提案
        回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        if message and hasattr(message.content[0], 'text'):
            content = message.content[0].text
            if not content.startswith('<p>'):
                content = '<p>' + content.replace('\n\n', '</p><p>') + '</p>'
            return content
        return '<p>AI分析の結果を取得できませんでした。</p>'

    except Exception as e:
        return handle_ai_error("analyze_schedules", e)

def analyze_opportunities(opportunities):
    """Analyze opportunities using Claude AI"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'
            
        client = Anthropic(api_key=user_settings.claude_api_key)

        opp_data = "\n".join([
            f"- 名前: {opp.name}, ステージ: {opp.stage}, 金額: {opp.amount}, 完了予定: {opp.close_date}"
            for opp in opportunities
        ])

        if not opportunities:
            return '<p>分析対象の商談がありません。</p>'

        prompt = f"""以下の商談データを分析してください:\n{opp_data}\n
        以下の項目について簡潔に分析してください:
        1. 総パイプライン価値と分布
        2. ステージごとの進捗状況
        3. 重点的に取り組むべき商談
        4. 次のステップへの提案
        回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        if message and hasattr(message.content[0], 'text'):
            content = message.content[0].text
            if not content.startswith('<p>'):
                content = '<p>' + content.replace('\n\n', '</p><p>') + '</p>'
            return content
        return '<p>AI分析の結果を取得できませんでした。</p>'

    except Exception as e:
        return handle_ai_error("analyze_opportunities", e)

def analyze_leads(leads):
    """Analyze leads using Claude AI"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'
            
        client = Anthropic(api_key=user_settings.claude_api_key)

        lead_data = "\n".join([
            f"- 名前: {lead.name}, ステータス: {lead.status}, スコア: {lead.score}, 最終接触: {lead.last_contact}"
            for lead in leads
        ])

        if not leads:
            return '<p>分析対象のリードがありません。</p>'

        prompt = f"""以下のリードデータを分析してください:\n{lead_data}\n
        以下の項目について簡潔に分析してください:
        1. リードの品質とスコア分布
        2. フォローアップの優先順位
        3. 重点的に取り組むべきリード
        4. 次のステップへの提案
        回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        if message and hasattr(message.content[0], 'text'):
            content = message.content[0].text
            if not content.startswith('<p>'):
                content = '<p>' + content.replace('\n\n', '</p><p>') + '</p>'
            return content
        return '<p>AI分析の結果を取得できませんでした。</p>'

    except Exception as e:
        return handle_ai_error("analyze_leads", e)

def analyze_email(subject, content, user_id=None):
    """Analyze email content using Claude AI"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=user_id if user_id else current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return json.dumps({
                "Opportunities": [],
                "Schedules": [],
                "Tasks": []
            })

        client = Anthropic(api_key=user_settings.claude_api_key)

        prompt = f"""以下のメールを分析し、機会、スケジュール、タスクを簡潔にJSON形式で提案してください：

        Subject: {subject}
        Content: {content}

        フォーマット：
        {{
            "Opportunities": [
                "送信者名:機会の説明"
            ],
            "Schedules": [
                {{
                    "Description": "送信者名:予定の説明",
                    "Start Time": "YYYY-MM-DD HH:MM",
                    "End Time": "YYYY-MM-DD HH:MM"
                }}
            ],
            "Tasks": [
                {{
                    "Description": "送信者名:タスクの説明",
                    "Due Date": "YYYY-MM-DD"
                }}
            ]
        }}
        """

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        if message and hasattr(message.content[0], 'text'):
            content = message.content[0].text
            if content.startswith('{'):
                return content
            return json.dumps({
                "Opportunities": [],
                "Schedules": [],
                "Tasks": []
            })
        return json.dumps({
            "Opportunities": [],
            "Schedules": [],
            "Tasks": []
        })

    except Exception as e:
        current_app.logger.error(f"AI analysis error: {str(e)}")
        return json.dumps({
            "Opportunities": [],
            "Schedules": [],
            "Tasks": []
        })

def process_ai_response(response, lead, app):
    """Process AI analysis response and create corresponding records"""
    try:
        if isinstance(response, str) and response.startswith('{'):
            data = json.loads(response)
            
            if 'Opportunities' in data:
                create_opportunities_from_ai(data['Opportunities'], lead)
            
            if 'Schedules' in data:
                create_schedules_from_ai(data['Schedules'], lead)
            
            if 'Tasks' in data:
                create_tasks_from_ai(data['Tasks'], lead)
            
            # Commit changes to ensure relationships are saved
            db.session.commit()
                
    except Exception as e:
        app.logger.error(f"Error processing AI response: {str(e)}")
        db.session.rollback()

def create_opportunities_from_ai(opportunities, lead):
    """Create opportunities from AI analysis"""
    for opp_desc in opportunities:
        if ':' in opp_desc:
            _, desc = opp_desc.split(':', 1)
            opportunity = Opportunity(
                name=desc.strip(),
                stage='Initial Contact',
                user_id=lead.user_id,
                lead_id=lead.id
            )
            db.session.add(opportunity)
            db.session.flush()

def create_schedules_from_ai(schedules, lead):
    """Create schedules from AI analysis"""
    for schedule in schedules:
        if isinstance(schedule, dict) and ':' in schedule.get('Description', ''):
            _, desc = schedule['Description'].split(':', 1)
            try:
                start_time = datetime.strptime(schedule.get('Start Time', ''), '%Y-%m-%d %H:%M')
                end_time = datetime.strptime(schedule.get('End Time', ''), '%Y-%m-%d %H:%M')
            except ValueError:
                start_time = datetime.utcnow()
                end_time = start_time + timedelta(hours=1)
            
            schedule_record = Schedule(
                title=desc.strip(),
                description=desc.strip(),
                start_time=start_time,
                end_time=end_time,
                user_id=lead.user_id,
                lead_id=lead.id
            )
            db.session.add(schedule_record)
            db.session.flush()

def create_tasks_from_ai(tasks, lead):
    """Create tasks from AI analysis"""
    for task in tasks:
        if isinstance(task, dict) and ':' in task.get('Description', ''):
            _, desc = task['Description'].split(':', 1)
            try:
                due_date = datetime.strptime(task.get('Due Date', ''), '%Y-%m-%d')
            except ValueError:
                due_date = datetime.utcnow() + timedelta(days=7)
            
            task_record = Task(
                title=desc.strip(),
                description=desc.strip(),
                due_date=due_date,
                status='New',
                user_id=lead.user_id,
                lead_id=lead.id
            )
            db.session.add(task_record)
            db.session.flush()
