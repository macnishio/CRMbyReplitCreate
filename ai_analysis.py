import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from models import Opportunity, Schedule, Task, Lead, UserSettings
from extensions import db
from anthropic import Anthropic, APIError, APIConnectionError, AuthenticationError
from flask import current_app
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

# 現在の日時を日本時間で取得
jst_datetime = datetime.now(ZoneInfo("Asia/Tokyo"))

# 日付をフォーマット
formatted_date = jst_datetime.strftime("%Y-%m-%d")


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


def analyze_data(data_type: str, data: str) -> str:
    """Analyze data using Claude AI"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'

        client = Anthropic(api_key=user_settings.claude_api_key)
        prompt = f"""今は日本時間の{formatted_date}です。以下の{data_type}データを分析してください:\n{data}\n
以下の項目について簡潔に分析してください:
1. 進捗状況と全体的な傾向
2. 重要なポイントの特定
3. 改善点や提案
4. 次のステップへの推奨事項
回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        if message and message.content and len(message.content) > 0:
            content = message.content[0].text
            if not content.startswith('<p>'):
                content = '<p>' + content.replace('\n\n', '</p><p>') + '</p>'
            return content
        return '<p>AI分析の結果を取得できませんでした。</p>'
    except APIError as e:
        current_app.logger.error(f"Claude API error: {str(e)}")
        return '<p>API処理中にエラーが発生しました。</p>'
    except Exception as e:
        return handle_ai_error(f"analyze_{data_type}", e)


def summarize_email_content(subject: str, content: str, user_id=None):
    """Summarize email content using Claude AI"""
    try:
        user_id = user_id if user_id else current_user.id
        user_settings = UserSettings.query.filter_by(user_id=user_id).first()
        if not user_settings or not user_settings.claude_api_key:
            current_app.logger.error("APIキーが設定されていません")
            return None  # Return None if API key is missing

        client = Anthropic(api_key=user_settings.claude_api_key)
        prompt = f"""今は日本時間の{formatted_date}です。以下のメールを要約してください。要点を簡潔にまとめ、重要な情報を漏らさないようにしてください。
件名: {subject}
本文:
{content}
以下の点に注意して要約してください：
1. 主要なポイントを箇条書きでまとめる
2. アクションアイテムがあれば明確に示す
3. 締切や重要な日付があれば強調する
4. 返信が必要かどうかを示す
HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        # Call the AI API
        message = client.completions.create(
            model="claude-2",
            max_tokens_to_sample=2000,
            prompt=prompt,
            stop_sequences=["</html>"],
        )

        # Process the response
        if message and message.completion:
            response_text = message.completion.strip()
            # Ensure the response is properly formatted
            if not response_text.startswith('<p>'):
                response_text = '<p>' + response_text.replace('\n\n', '</p><p>') + '</p>'
            return response_text
        else:
            current_app.logger.error("AI APIから有効な応答を受信できませんでした")
            return None

    except Exception as e:
        current_app.logger.error(f"summarize_email_content関数内でエラーが発生しました: {str(e)}")
        return None



def analyze_email(subject, content, user_id=None):
    """Analyze email content using Claude AI"""
    empty_response = json.dumps({
        "Opportunities": [],
        "Schedules": [],
        "Tasks": []
    })

    try:
        user_settings = UserSettings.query.filter_by(user_id=user_id if user_id else current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return empty_response
        client = Anthropic(api_key=user_settings.claude_api_key)
        system_message = """
You are an AI assistant that analyzes emails and provides suggestions for opportunities, schedules, and tasks.
Be concise and direct in your responses.
"""
        prompt = f"""
今は日本時間の{formatted_date}です。以下のメールを分析し、機会、スケジュール、タスクを簡潔にJSON形式で提案してください。
Subject: {subject}
Content: {content}
- 具体的な日時は「YYYY-MM-DD HH:MM」形式か「現在時刻」で記載
- 推測は避け、メールに明示されている情報のみを使用
フォーマット:
{{
  "Opportunities": [
    "送信者名:機会の説明"
  ],
  "Schedules": [{{
    "Description": "送信元名:説明",
    "Start Time": "YYYY-MM-DD HH:MM" または"Start Time": "{formatted_date}",
    "End Time": "YYYY-MM-DD HH:MM" または"End Time": "{formatted_date}"
  }}],
  "Tasks": [{{
    "Description": "送信元名:説明",
    "Due Date": "YYYY-MM-DD" または"Due Date": "{formatted_date}"
  }}]
}}
"""
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        if message and hasattr(message, 'content') and isinstance(message.content, list) and len(message.content) > 0:
            try:
                response_text = message.content[0].text.strip()
                if response_text:
                    normalized_response = normalize_json_response(response_text)
                    if normalized_response:
                        return normalized_response
            except Exception as e:
                current_app.logger.error(f"JSON normalization error: {str(e)}")
        return empty_response
    except APIError as e:
        current_app.logger.error(f"Claude API error in analyze_email: {str(e)}")
        return empty_response
    except Exception as e:
        current_app.logger.error(f"Error in analyze_email: {str(e)}")
        return empty_response


def create_or_get_lead(email_data, user_id):
    """Create a new lead if it doesn't exist or get existing lead"""
    try:
        # メールアドレスでリードを検索
        lead = Lead.query.filter_by(email=email_data.sender).first()

        if not lead:
            # リードが存在しない場合は新規作成
            lead = Lead(
                name=email_data.sender_name or email_data.sender.split('@')[0],
                email=email_data.sender,
                user_id=user_id,
                status='New',
                score=0.0
            )
            db.session.add(lead)
            db.session.commit()
            current_app.logger.info(f"Created new lead: {lead.id}")
        return lead
    except Exception as e:
        current_app.logger.error(f"Error creating/getting lead: {str(e)}")
        db.session.rollback()
        return None


def create_opportunities_from_ai(opportunities, lead):
    """Create opportunities from AI analysis"""
    try:
        # leadが存在することを確認
        if not Lead.query.get(lead.id):
            current_app.logger.error(f"Lead ID {lead.id} not found")
            return

        for opp_desc in opportunities:
            if ':' in opp_desc:
                _, desc = opp_desc.split(':', 1)
                try:
                    opportunity = Opportunity(
                        name=desc.strip(),
                        stage='Initial Contact',
                        user_id=lead.user_id,
                        lead_id=lead.id,
                        is_ai_generated=True  # is_ai_generated を追加
                    )
                    db.session.add(opportunity)
                    db.session.flush()  # エラーを早期に検出するためにflush
                except SQLAlchemyError as e:
                    current_app.logger.error(f"Error creating opportunity: {str(e)}")
                    db.session.rollback()
                    continue
    except Exception as e:
        current_app.logger.error(f"Error in create_opportunities_from_ai: {str(e)}")
        db.session.rollback()
        raise


def create_schedules_from_ai(schedules, lead):
    """Create schedules from AI analysis"""
    try:
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
                    lead_id=lead.id,
                    is_ai_generated=True  # is_ai_generated を追加
                )
                db.session.add(schedule_record)
                db.session.flush()
    except Exception as e:
        current_app.logger.error(f"Error in create_schedules_from_ai: {str(e)}")
        db.session.rollback()
        raise


def create_tasks_from_ai(tasks, lead):
    """Create tasks from AI analysis"""
    try:
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
                    lead_id=lead.id,
                    is_ai_generated=True  # is_ai_generated を追加
                )
                db.session.add(task_record)
                db.session.flush()
    except Exception as e:
        current_app.logger.error(f"Error in create_tasks_from_ai: {str(e)}")
        db.session.rollback()
        raise


def normalize_json_response(response_text):
    """AIレスポンスのJSON形式を正規化する"""
    try:
        # デバッグログ追加
        current_app.logger.debug(f"Raw AI response: {response_text}")

        # 余分な空白や改行を削除
        response_text = response_text.strip()
        # JSON部分を抽出
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start == -1 or end == 0:
            current_app.logger.error("No valid JSON found in response")
            return None
        json_text = response_text[start:end]
        # デバッグログ追加
        current_app.logger.debug(f"Extracted JSON: {json_text}")
        # JSONをパースしてバリデーション
        data = json.loads(json_text)
        # 正規化されたデータ構造
        normalized = {
            "Opportunities": [],
            "Schedules": [],
            "Tasks": []
        }
        # Opportunities
        if "Opportunities" in data and isinstance(data["Opportunities"], list):
            normalized["Opportunities"] = [
                opp.strip() for opp in data["Opportunities"] if isinstance(opp, str)
            ]
        # Schedules
        if "Schedules" in data and isinstance(data["Schedules"], list):
            for schedule in data["Schedules"]:
                if isinstance(schedule, dict):
                    normalized_schedule = {
                        "Description": str(schedule.get("Description", "")),
                        "Start Time": str(schedule.get("Start Time", formatted_date)),
                        "End Time": str(schedule.get("End Time", formatted_date))
                    }
                    normalized["Schedules"].append(normalized_schedule)
        # Tasks
        if "Tasks" in data and isinstance(data["Tasks"], list):
            for task in data["Tasks"]:
                if isinstance(task, dict):
                    normalized_task = {
                        "Description": str(task.get("Description", "")),
                        "Due Date": str(task.get("Due Date", formatted_date))
                    }
                    normalized["Tasks"].append(normalized_task)
        # 正規化されたJSONを文字列に変換
        result = json.dumps(normalized, ensure_ascii=False)
        current_app.logger.debug(f"Normalized JSON: {result}")
        return result
    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON parse error: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error normalizing JSON response: {str(e)}")
        return None


def process_ai_response(response, email_data, app):
    """Process AI analysis response and create corresponding records"""
    try:
        if not isinstance(response, str):
            app.logger.error("Invalid response type")
            return

        normalized_response = normalize_json_response(response)
        if not normalized_response:
            app.logger.error("Failed to normalize AI response")
            return
        data = json.loads(normalized_response)
        # Create opportunities
        if data.get('Opportunities'):
            try:
                create_opportunities_from_ai(data['Opportunities'], email_data.lead)
            except Exception as e:
                app.logger.error(f"Error creating opportunities: {str(e)}")
        # Create schedules
        if data.get('Schedules'):
            try:
                create_schedules_from_ai(data['Schedules'], email_data.lead)
            except Exception as e:
                app.logger.error(f"Error creating schedules: {str(e)}")
        # Create tasks
        if data.get('Tasks'):
            try:
                create_tasks_from_ai(data['Tasks'], email_data.lead)
            except Exception as e:
                app.logger.error(f"Error creating tasks: {str(e)}")
        # Commit all changes
        try:
            db.session.commit()
            app.logger.info(f"Successfully processed AI response for email {email_data.id}")
        except SQLAlchemyError as e:
            app.logger.error(f"Error committing changes: {str(e)}")
            db.session.rollback()
    except Exception as e:
        app.logger.error(f"Error processing AI response: {str(e)}")
        db.session.rollback()


def analyze_tasks(tasks):
    """Analyze tasks using Claude AI"""
    task_data = "\n".join([
        f"- タイトル: {task.title}, 期限: {task.due_date}, ステータス: {task.status}"
        for task in tasks
    ])
    return analyze_data("タスク", task_data)


def analyze_schedules(schedules):
    """Analyze schedules using Claude AI"""
    schedule_data = "\n".join([
        f"- タイトル: {sch.title}, 開始: {sch.start_time}, 終了: {sch.end_time}"
        for sch in schedules
    ])
    return analyze_data("スケジュール", schedule_data)


def analyze_opportunities(opportunities):
    """Analyze opportunities using Claude AI"""
    opp_data = "\n".join([
        f"- 名前: {opp.name}, ステージ: {opp.stage}, 金額: {opp.amount}, 完了予定: {opp.close_date}"
        for opp in opportunities
    ])
    return analyze_data("商談", opp_data)


def analyze_leads(leads):
    """Analyze leads using Claude AI"""
    lead_data = "\n".join([
        f"- 名前: {lead.name}, ステータス: {lead.status}, スコア: {lead.score}, 最終接触: {lead.last_contact}"
        for lead in leads
    ])
    return analyze_data("リード", lead_data)
