from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from models import Lead, Email
from extensions import db
from sqlalchemy import desc

bp = Blueprint('history', __name__)

@bp.route('/history/<int:lead_id>')
@login_required
def show_history(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    return render_template('history.html', lead=lead)

@bp.route('/api/history/<int:lead_id>')
@login_required
def get_history(lead_id):
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    lead = Lead.query.get_or_404(lead_id)
    emails = Email.query.filter_by(
        lead_id=lead_id
    ).order_by(
        desc(Email.received_date)
    ).paginate(
        page=page, 
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'messages': [{
            'id': email.id,
            'sender': email.sender_name or email.sender,
            'content': email.content,
            'received_date': email.received_date.isoformat(),
            'is_from_lead': True  # メールは常にリードからの受信
        } for email in emails.items],
        'has_next': emails.has_next,
        'next_page': emails.next_num if emails.has_next else None,
        'total': emails.total
    })
