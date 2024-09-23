from flask import Blueprint, jsonify

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return "Welcome to the CRM Application"

@bp.route('/health')
def health_check():
    return jsonify({"status": "ok"}), 200

# Add other existing routes here
