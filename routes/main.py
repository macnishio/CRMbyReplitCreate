from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required
from email_receiver import fetch_emails

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('home.html')

@bp.route('/health')
def health_check():
    return jsonify({"status": "ok"}), 200

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@bp.route('/fetch-emails', methods=['POST'])
@login_required
def manual_fetch_emails():
    try:
        fetch_emails()
        flash('Emails fetched successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error fetching emails: {str(e)}")
        flash('An error occurred while fetching emails. Please try again.', 'error')
    return redirect(url_for('main.index'))

# Other routes are handled by their respective blueprints
