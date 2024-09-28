from flask import Blueprint, render_template, current_app, jsonify
from flask_login import login_required
from ai_analysis import analyze_email
import os

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html', title='Transform Your Sales Process | Salesforce-inspired CRM')

@bp.route('/dashboard')
@login_required
def dashboard():
    return 'Dashboard'

@bp.route('/test-ai-analysis')
def test_ai_analysis():
    current_app.logger.info("Testing AI analysis function")
    
    # Check if CLAUDE_API_KEY is set in the environment
    claude_api_key = os.environ.get('CLAUDE_API_KEY')
    if claude_api_key:
        current_app.logger.info("CLAUDE_API_KEY is set in environment variables")
        current_app.logger.debug(f"CLAUDE_API_KEY starts with: {claude_api_key[:5]}...")
    else:
        current_app.logger.error("CLAUDE_API_KEY is not set in environment variables")
        return jsonify({"error": "CLAUDE_API_KEY is not set"}), 500

    # Test the AI analysis function
    test_subject = "Test Subject"
    test_body = "This is a test email body for AI analysis."
    
    try:
        ai_response = analyze_email(test_subject, test_body)
        current_app.logger.info(f"AI analysis response: {ai_response[:100]}...")
        return jsonify({"success": True, "ai_response": ai_response})
    except Exception as e:
        current_app.logger.error(f"Error in AI analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500
