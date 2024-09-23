from flask import Blueprint, jsonify, render_template
from flask_login import login_required

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return "Welcome to the CRM Application"

@bp.route('/health')
def health_check():
    return jsonify({"status": "ok"}), 200

@bp.route('/dashboard')
@login_required
def dashboard():
    # Add any necessary dashboard logic here
    return render_template('dashboard.html')

# Add other existing routes here
