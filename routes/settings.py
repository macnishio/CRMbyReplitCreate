from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import UserSettings
from extensions import db
from werkzeug.security import generate_password_hash
import os

bp = Blueprint('settings', __name__)

@bp.route('/settings')
@login_required
def settings():
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    return render_template('settings/settings.html', settings=user_settings)

@bp.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.session.add(user_settings)

    user_settings.mail_server = request.form.get('mail_server')
    user_settings.mail_port = int(request.form.get('mail_port', 587))
    user_settings.mail_use_tls = request.form.get('mail_use_tls') == 'true'
    user_settings.mail_username = request.form.get('mail_username')
    
    # Only update passwords/keys if they are provided
    if request.form.get('mail_password'):
        user_settings.mail_password = request.form.get('mail_password')
    if request.form.get('claude_api_key'):
        user_settings.claude_api_key = request.form.get('claude_api_key')
    if request.form.get('clearbit_api_key'):
        user_settings.clearbit_api_key = request.form.get('clearbit_api_key')

    try:
        db.session.commit()
        flash('設定が正常に更新されました。', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating settings: {str(e)}")
        flash('設定の更新中にエラーが発生しました。', 'error')

    return redirect(url_for('settings.settings'))
