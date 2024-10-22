from anthropic import Anthropic
from flask import current_app
import logging
from models import UserSettings

def get_user_settings(user_id):
    return UserSettings.query.filter_by(user_id=user_id).first()

def analyze_email(subject, content, user_id=None):
    try:
        api_key = None
        if user_id:
            user_settings = get_user_settings(user_id)
            if user_settings:
                api_key = user_settings.claude_api_key

        # Fallback to environment variable if no user settings
        if not api_key:
            api_key = current_app.config['CLAUDE_API_KEY']

        if not api_key:
            current_app.logger.error("No Claude API key available")
            return "Error: No Claude API key available"

        current_app.logger.info(
            f"Attempting to create Anthropic client with API key starting with: {api_key[:5]}..."
        )
        client = Anthropic(api_key=api_key)
        current_app.logger.info("Anthropic client created successfully")

        system_message = "You are an AI assistant that analyzes emails and provides suggestions for opportunities, schedules, and tasks."

        prompt = f"\n\nHuman: 回答はすべて日本語でお願いします。Analyze the following email and provide suggestions for opportunities, schedules, and tasks:\n\nSubject: {subject}\n\nContent: {content}\n\nPlease provide your analysis in the following format:\nOpportunities:\n1.\n2.\n\nSchedules:\n1.\n2.\n\nTasks:\n1.\n2.\n\nAssistant:"

        current_app.logger.info("Sending request to Anthropic API")
        response = client.completions.create(
            prompt=system_message + prompt,
            model="claude-2",
            max_tokens_to_sample=4000,
            temperature=0.7,
        )
        current_app.logger.info("Received response from Anthropic API")

        return response.completion

    except Exception as e:
        current_app.logger.error(f"Error in analyze_email: {str(e)}")
        return f"Error: {str(e)}"

def parse_ai_response(response):
    opportunities = []
    schedules = []
    tasks = []
    current_section = None

    for line in response.split('\n'):
        if line.startswith('Opportunities:'):
            current_section = opportunities
        elif line.startswith('Schedules:'):
            current_section = schedules
        elif line.startswith('Tasks:'):
            current_section = tasks
        elif line.strip().startswith('1.') or line.strip().startswith('2.'):
            if current_section is not None:
                current_section.append(line.strip()[3:])

    return opportunities, schedules, tasks
