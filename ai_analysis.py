from anthropic import Anthropic, APIError, APIConnectionError, AuthenticationError
from flask import current_app
from models import Opportunity, Schedule, UserSettings
from datetime import datetime, timedelta
import logging
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

def analyze_email(subject, content, user_id=None):
    """Analyze email content using Claude AI with improved error handling"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=user_id if user_id else current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'

        client = Anthropic(api_key=user_settings.claude_api_key)

        prompt = f"""以下のメールを分析し、商談、スケジュール、タスクの提案をしてください:
        件名: {subject}
        本文: {content}

        以下の形式で回答してください:
        商談:
        1. [提案1]
        2. [提案2]

        スケジュール:
        1. [予定1]
        2. [予定2]

        タスク:
        1. [タスク1]
        2. [タスク2]

        回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        if message.content:
            return message.content[0].text
        return '<p>AI分析の結果を取得できませんでした。</p>'

    except Exception as e:
        return handle_ai_error("analyze_email", e)

def parse_ai_response(response):
    """Parse AI response into opportunities, schedules, and tasks"""
    if not response or isinstance(response, str) and response.startswith('<p class="error-message"'):
        return [], [], []

    opportunities = []
    schedules = []
    tasks = []
    current_section = None

    for line in response.split('\n'):
        line = line.strip()
        if '商談:' in line:
            current_section = opportunities
        elif 'スケジュール:' in line:
            current_section = schedules
        elif 'タスク:' in line:
            current_section = tasks
        elif line.startswith('1.') or line.startswith('2.'):
            if current_section is not None and line[2:].strip():
                current_section.append(line[2:].strip())

    return opportunities, schedules, tasks

def analyze_tasks(tasks):
    """Analyze tasks using Claude AI with improved error handling"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'
            
        client = Anthropic(api_key=user_settings.claude_api_key)

        task_data = "\n".join([
            f"- タイトル: {task.title}, 期限: {task.due_date}, ステータス: {task.status}, 完了: {'完了' if task.completed else '未完了'}"
            for task in tasks
        ])

        if not tasks:
            return '<p>分析対象のタスクがありません。</p>'

        prompt = f"""以下のタスクデータを分析してください:\n{task_data}\n
        以下の項目について簡潔に分析してください:
        1. タスクの優先度と期限
        2. 進捗状況の分析
        3. リソース配分の提案
        4. 効率化のための提案
        回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        if message.content:
            content = message.content[0].text
            return content if isinstance(content, str) else '<p>AI分析の結果を取得できませんでした。</p>'
        return '<p>AI分析の結果を取得できませんでした。</p>'

    except Exception as e:
        return handle_ai_error("analyze_tasks", e)

def analyze_opportunities(opportunities):
    """Analyze opportunities using Claude AI with improved error handling"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'
            
        client = Anthropic(api_key=user_settings.claude_api_key)
        
        opp_data = "\n".join([
            f"- 名前: {opp.name}, ステージ: {opp.stage}, 金額: {opp.amount}, 完了予定日: {opp.close_date}"
            for opp in opportunities
        ])
        
        if not opportunities:
            return '<p>分析対象の商談がありません。</p>'

        prompt = f"""以下の商談データを分析してください:\n{opp_data}\n
        以下の項目について簡潔に分析してください:
        1. 総パイプライン価値
        2. ステージごとの分布
        3. 重点的に取り組むべき商談
        4. 次のステップへの提案
        回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        if message.content:
            content = message.content[0].text
            return content if isinstance(content, str) else '<p>AI分析の結果を取得できませんでした。</p>'
        return '<p>AI分析の結果を取得できませんでした。</p>'

    except Exception as e:
        return handle_ai_error("analyze_opportunities", e)

def analyze_schedules(schedules):
    """Analyze schedules using Claude AI with improved error handling"""
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
        1. スケジュールの密度と繁忙期
        2. 時間配分のパターン
        3. 重要な予定
        4. スケジュール管理の提案
        回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        if message.content:
            content = message.content[0].text
            return content if isinstance(content, str) else '<p>AI分析の結果を取得できませんでした。</p>'
        return '<p>AI分析の結果を取得できませんでした。</p>'

    except Exception as e:
        return handle_ai_error("analyze_schedules", e)
