import anthropic
from flask import current_app

def analyze_email(subject, content):
    client = anthropic.Client(api_key=current_app.config['CLAUDE_API_KEY'])
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

    response = client.completions.create(
        prompt=prompt,
        model="claude-2",
        max_tokens_to_sample=300,
    )

    return response.completion

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
