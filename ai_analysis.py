import anthropic
from flask import current_app
import logging

def analyze_email(subject, content):
    try:
        api_key = current_app.config['CLAUDE_API_KEY']
        if not api_key:
            current_app.logger.error("CLAUDE_API_KEY is not set in the configuration")
            return "Error: CLAUDE_API_KEY is not set"

        current_app.logger.info(f"Attempting to create Anthropic client with API key starting with: {api_key[:5]}...")
        client = anthropic.Client(api_key=api_key)
        current_app.logger.info("Anthropic client created successfully")

        prompt = f"""Analyze the following email and provide suggestions for opportunities, schedules, and tasks:

Subject: {subject}

Content: {content}

Please provide your analysis in the following format:
Opportunities:
1.
2.

Schedules:
1.
2.

Tasks:
1.
2."""

        current_app.logger.info("Sending request to Anthropic API")
        response = client.completions.create(
            prompt=prompt,
            model="claude-2",
            max_tokens_to_sample=300,
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
