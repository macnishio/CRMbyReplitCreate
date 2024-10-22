from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
import os

bp = Blueprint('settings', __name__)

@bp.route('/settings')
@login_required
def settings():
    # Get all available environment variables that we want to expose
    settings = {
        'MAIL_SERVER': os.environ.get('MAIL_SERVER', ''),
        'MAIL_PORT': os.environ.get('MAIL_PORT', ''),
        'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', ''),
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', ''),
        'CLAUDE_API_KEY': bool(os.environ.get('CLAUDE_API_KEY')),
        'CLEARBIT_API_KEY': bool(os.environ.get('CLEARBIT_API_KEY')),
    }
    
    return render_template('settings/settings.html', settings=settings)

@bp.route('/settings/configure', methods=['POST'])
@login_required
def configure_settings():
    # This endpoint will only show which settings need to be configured
    # The actual configuration must be done through Replit's Secrets UI
    missing_settings = []
    
    if not os.environ.get('MAIL_SERVER'):
        missing_settings.append('MAIL_SERVER')
    if not os.environ.get('MAIL_PORT'):
        missing_settings.append('MAIL_PORT')
    if not os.environ.get('MAIL_USERNAME'):
        missing_settings.append('MAIL_USERNAME')
    if not os.environ.get('MAIL_PASSWORD'):
        missing_settings.append('MAIL_PASSWORD')
    if not os.environ.get('CLAUDE_API_KEY'):
        missing_settings.append('CLAUDE_API_KEY')
    if not os.environ.get('CLEARBIT_API_KEY'):
        missing_settings.append('CLEARBIT_API_KEY')
        
    if missing_settings:
        flash('以下の設定を Replit の Secrets で構成する必要があります: ' + ', '.join(missing_settings), 'warning')
    else:
        flash('すべての必要な設定が構成されています', 'success')
    
    return redirect(url_for('settings.settings'))
