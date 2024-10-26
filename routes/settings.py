from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import UserSettings
from extensions import db
from forms import SettingsForm
import os

bp = Blueprint('settings', __name__)

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()

    if form.validate_on_submit():
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)

        settings.claude_api_key = form.claude_api_key.data
        settings.mail_server = form.mail_server.data
        settings.mail_port = form.mail_port.data
        settings.mail_use_tls = form.mail_use_tls.data
        settings.mail_username = form.mail_username.data
        if form.mail_password.data:  # Only update if new password provided
            settings.mail_password = form.mail_password.data

        try:
            db.session.commit()
            flash('設定を更新しました。', 'success')
            return redirect(url_for('settings.settings'))
        except Exception as e:
            db.session.rollback()
            flash('設定の更新に失敗しました。', 'error')

    elif settings:
        form.claude_api_key.data = settings.claude_api_key
        form.mail_server.data = settings.mail_server
        form.mail_port.data = settings.mail_port
        form.mail_use_tls.data = settings.mail_use_tls
        form.mail_username.data = settings.mail_username

    return render_template('settings/settings.html', form=form)
