import os
from anthropic import Anthropic
from flask import current_app
from models import Opportunity, Schedule
from datetime import datetime, timedelta

def analyze_email(subject, content, user_id=None):
    """Analyze email content using Claude AI"""
    try:
        api_key = os.environ.get('CLAUDE_API_KEY')
        if not api_key:
            current_app.logger.error("CLAUDE_API_KEY is missing from environment variables")
            return "Error: No Claude API key available"

        client = Anthropic(api_key=api_key)
        current_app.logger.info("Anthropic client created successfully")

        system_message = "You are an AI assistant that analyzes emails and provides suggestions for opportunities, schedules, and tasks."

        prompt = f"\n\nHuman: 回答はすべて日本語でお願いします。Analyze the following email and provide suggestions for opportunities, schedules, and tasks:\n\nSubject: {subject}\n\nContent: {content}\n\nPlease provide your analysis in the following format:\nOpportunities:\n1.\n2.\n\nSchedules:\n1.\n2.\n\nTasks:\n1.\n2.\n\nAssistant:"

        response = client.messages.create(
            messages=[{"role": "user", "content": system_message + prompt}],
            model="claude-2",
            max_tokens=4000,
        )
        return response.content
    except Exception as e:
        current_app.logger.error(f"Error in analyze_email: {str(e)}")
        return f"Error: {str(e)}"

def parse_ai_response(response):
    """Parse AI response into opportunities, schedules, and tasks"""
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

def analyze_opportunities(opportunities):
    """Analyze opportunities using Claude AI"""
    try:
        api_key = os.environ.get('CLAUDE_API_KEY')
        if not api_key:
            current_app.logger.error("CLAUDE_API_KEY is missing from environment variables")
            return None
            
        client = Anthropic(api_key=api_key)
        current_app.logger.info("Anthropic client created successfully")

        # Prepare opportunity data for analysis
        opp_data = "\n".join([
            f"- Name: {opp.name}, Stage: {opp.stage}, Amount: {opp.amount}, Close Date: {opp.close_date}"
            for opp in opportunities
        ])

        prompt = f"""Given these opportunities:\n{opp_data}\n
        Provide a brief analysis including:
        1. Total pipeline value
        2. Distribution across stages
        3. Key opportunities to focus on
        4. Recommendations for next steps
        Format the response in simple HTML paragraphs."""

        response = client.messages.create(
            messages=[{"role": "user", "content": prompt}],
            model="claude-2",
            max_tokens=500,
        )
        return response.content
    except Exception as e:
        current_app.logger.error(f"Error in analyze_opportunities: {str(e)}")
        return None

def analyze_schedules(schedules):
    """Analyze schedules using Claude AI"""
    try:
        api_key = os.environ.get('CLAUDE_API_KEY')
        if not api_key:
            current_app.logger.error("CLAUDE_API_KEY is missing from environment variables")
            return None
            
        client = Anthropic(api_key=api_key)
        current_app.logger.info("Anthropic client created successfully")

        # Prepare schedule data for analysis
        schedule_data = "\n".join([
            f"- Title: {sch.title}, Start: {sch.start_time}, End: {sch.end_time}"
            for sch in schedules
        ])

        prompt = f"""Given these schedules:\n{schedule_data}\n
        Provide a brief analysis including:
        1. Schedule density and busy periods
        2. Time allocation patterns
        3. Upcoming important events
        4. Scheduling recommendations
        Format the response in simple HTML paragraphs."""

        response = client.messages.create(
            messages=[{"role": "user", "content": prompt}],
            model="claude-2",
            max_tokens=500,
        )
        return response.content
    except Exception as e:
        current_app.logger.error(f"Error in analyze_schedules: {str(e)}")
        return None
