import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from models import Opportunity, Schedule, Task, Lead
from extensions import db
from anthropic import Anthropic, APIError, APIConnectionError, AuthenticationError
from flask import current_app
from models import UserSettings
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

def summarize_email_content(subject: str, content: str, user_id=None):
    """Summarize email content using Claude AI"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=user_id if user_id else current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p>要約を生成するにはAPIキーの設定が必要です。</p>'

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
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        if message and hasattr(message, 'content') and isinstance(message.content, list) and len(message.content) > 0:
            try:
                response_text = message.content[0].text
                if not response_text.startswith('<p>'):
                    response_text = '<p>' + response_text.replace('\n\n', '</p><p>') + '</p>'
                return response_text
            except AttributeError:
                current_app.logger.error("Failed to access message content text")
                return '<p>要約の生成中にエラーが発生しました。</p>'
        return '<p>要約の生成に失敗しました。</p>'
    except APIError as e:
        current_app.logger.error(f"Claude API error: {str(e)}")
        return '<p>API処理中にエラーが発生しました。</p>'
    except Exception as e:
        current_app.logger.error(f"Email summarization error: {str(e)}")
        return '<p>要約の生成中にエラーが発生しました。</p>'

def analyze_data(data_type, data):
    """Analyze data using Claude AI"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'

        client = Anthropic(api_key=user_settings.claude_api_key)

        prompt = f"""今は日本時間の{formatted_date}です。以下の{data_type}データを分析してください:\n{data}\n
        以下の項目について簡潔に分析してください:
        1. {data_type}の全体的な状況
        2. 重要な要素の特定
        3. {data_type}管理の改善点
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
        return handle_ai_error(f"analyze_{data_type}", e)

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

def analyze_leads(leads, custom_params=None):
    """Analyze leads using Claude AI with custom parameters"""
    lead_data = "\n".join([
        f"- 名前: {lead.name}, ステータス: {lead.status}, スコア: {lead.score}, 最終接触: {lead.last_contact}"
        for lead in leads
    ])
    
    if custom_params:
        analysis_prompt = f"""今は日本時間の{formatted_date}です。以下のリードデータを分析してください:\n{lead_data}\n
        以下の観点を重点的に分析してください:
        """
        for param in custom_params:
            if param == "engagement":
                analysis_prompt += "\n- エンゲージメント分析（接触頻度、反応率、コミュニケーションパターン）"
            elif param == "conversion":
                analysis_prompt += "\n- コンバージョン可能性（過去の行動パターン、類似リードとの比較）"
            elif param == "timing":
                analysis_prompt += "\n- 最適なアプローチタイミング（過去の反応時間、業界特性）"
            elif param == "channel":
                analysis_prompt += "\n- 効果的なコミュニケーションチャネル（メール反応率、ミーティング設定率）"
        
        try:
            user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
            if not user_settings or not user_settings.claude_api_key:
                return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'

            client = Anthropic(api_key=user_settings.claude_api_key)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                messages=[{"role": "user", "content": analysis_prompt}]
            )

            if message and hasattr(message.content[0], 'text'):
                content = message.content[0].text
                if not content.startswith('<p>'):
                    content = '<p>' + content.replace('\n\n', '</p><p>') + '</p>'
                return content
            return '<p>カスタムAI分析の結果を取得できませんでした。</p>'

        except Exception as e:
            return handle_ai_error("analyze_leads_custom", e)
            
    return analyze_data("リード", lead_data)
def analyze_lead_custom(lead_id, prompt):
    """
    カスタムプロンプトを使用してリードを分析
    """
    try:
        # リードデータの取得
        lead = Lead.query.get(lead_id)
        if not lead:
            return '<p class="error-message">指定されたリードが見つかりません。</p>'

        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings or not user_settings.claude_api_key:
            return '<p class="error-message">AI分析を実行するにはAPIキーの設定が必要です。</p>'

        # リードの基本情報を収集
        lead_info = f"""
        リード名: {lead.name}
        ステータス: {lead.status}
        スコア: {lead.score}
        最終接触: {lead.last_contact}
        作成日: {lead.created_at}
        """

        # 関連データの収集
        tasks = Task.query.filter_by(lead_id=lead.id).all()
        opportunities = Opportunity.query.filter_by(lead_id=lead.id).all()
        schedules = Schedule.query.filter_by(lead_id=lead.id).all()

        related_data = f"""
        関連タスク数: {len(tasks)}
        関連商談数: {len(opportunities)}
        関連スケジュール数: {len(schedules)}

        タスク状況:
        {', '.join(f"{task.title} ({task.status})" for task in tasks[:5])}

        商談状況:
        {', '.join(f"{opp.name} ({opp.stage})" for opp in opportunities[:5])}

        直近のスケジュール:
        {', '.join(f"{sch.title} ({sch.start_time.strftime('%Y-%m-%d')})" for sch in schedules[:5])}
        """

        # ClaudeにAPIリクエストを送信
        client = Anthropic(api_key=user_settings.claude_api_key)
        analysis_prompt = f"""今は日本時間の{formatted_date}です。
        以下のリードデータを分析し、ユーザーの要望に基づいて分析を行ってください：

        === リード基本情報 ===
        {lead_info}

        === 関連データ ===
        {related_data}

        === ユーザーからの分析要望 ===
        {prompt}

        以下の点に注意して分析を行ってください：
        1. データに基づく具体的な分析
        2. 実用的な提案や示唆
        3. 数値やデータを活用した根拠の提示
        4. 業界特性を考慮した分析

        HTMLの段落タグ（<p>）とヘッダータグ（<h4>）を使用して、読みやすく構造化された分析結果を提供してください。
        """

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": analysis_prompt}]
        )

        if message and hasattr(message.content[0], 'text'):
            content = message.content[0].text
            if not content.startswith('<'):
                content = f'<div class="analysis-result">{content}</div>'
            return content

        return '<p class="error-message">分析結果の生成に失敗しました。</p>'

    except Exception as e:
        return handle_ai_error("analyze_lead_custom", e)

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
            "Start Time": "YYYY-MM-DD HH:MM" または"Start Time": {formatted_date},
            "End Time": "YYYY-MM-DD HH:MM" または"End Time": {formatted_date}"
          }}],
          "Tasks": [{{
            "Description": "送信元名:説明",
            "Due Date": "YYYY-MM-DD" または"Due Date": {formatted_date}"
          }}]
        }}
        """

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            temperature=0.7,
            system=system_message,
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
                lead_id=lead.id,
                is_ai_generated=True  # is_ai_generated を追加
            )
            db.session.add(task_record)
            db.session.flush()

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
                        "Start Time": str(schedule.get("Start Time", "2024-10-29")),
                        "End Time": str(schedule.get("End Time", "2024-10-29"))
                    }
                    normalized["Schedules"].append(normalized_schedule)

        # Tasks
        if "Tasks" in data and isinstance(data["Tasks"], list):
            for task in data["Tasks"]:
                if isinstance(task, dict):
                    normalized_task = {
                        "Description": str(task.get("Description", "")),
                        "Due Date": str(task.get("Due Date", "2024-10-29"))
                    }
                    normalized["Tasks"].append(normalized_task)

        # 正規化されたJSONを文字列に変換
        result = json.dumps(normalized, ensure_ascii=False)
        current_app.logger.debug(f"Normalized JSON: {result}")
        return result

    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON parse error: {str(e)}")
        return '<p class="error-message">AI分析の結果を取得できませんでした。</p>'
    except Exception as e:
        current_app.logger.error(f"Error normalizing JSON response: {str(e)}")
        return '<p class="error-message">AI分析の結果を取得できませんでした。</p>'

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