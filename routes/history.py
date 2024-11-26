from flask import Blueprint, render_template, jsonify, request, current_app, abort
from flask_login import login_required, current_user
from models import Lead, Email
from extensions import db
from sqlalchemy import desc
from datetime import datetime
import traceback

bp = Blueprint('history', __name__)
@bp.route('/')
@login_required
def list_history():
    try:
        leads = Lead.query.filter_by(user_id=current_user.id).all()

        # JSON シリアライズ可能なデータに変換
        leads_data = [{
            'id': lead.id,
            'name': lead.name,
            'email': lead.email,
            'status': lead.status,
            'last_contact': lead.last_contact.isoformat() if lead.last_contact else None,
            'phone': getattr(lead, 'phone', None),
            'cc': getattr(lead, 'cc', None),
            'bcc': getattr(lead, 'bcc', None)
        } for lead in leads]

        return render_template('history/index.html', 
                             leads=leads,          # テンプレートでの表示用
                             leads_json=leads_data # JavaScript用のJSONデータ
        )

    except Exception as e:
        current_app.logger.error("Error in list_history:", exc_info=True)
        return render_template('error.html', 
                             message="履歴の取得中にエラーが発生しました"), 500

@bp.route('/leads/<int:lead_id>')
@login_required
def show_history(lead_id):
    try:
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            abort(404)
        return render_template('history.html', lead=lead)
    except Exception as e:
        current_app.logger.error(f"Error in show_history: {str(e)}")
        return render_template('error.html', message="リード履歴の取得中にエラーが発生しました"), 500

@bp.route('/api/leads/<int:lead_id>/messages')
@login_required
def get_history(lead_id):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search_query = request.args.get('query', '')
        search_type = request.args.get('type', 'content')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
        if not lead:
            return jsonify({'error': '指定されたリードは存在しないか、アクセス権限がありません'}), 404

        query = Email.query.filter_by(lead_id=lead_id)

        # 検索条件の適用
        if search_query:
            if search_type == 'content':
                query = query.filter(Email.content.ilike(f'%{search_query}%'))
            elif search_type == 'sender':
                query = query.filter(
                    (Email.sender_name.ilike(f'%{search_query}%')) |
                    (Email.sender.ilike(f'%{search_query}%'))
                )

        # 日付範囲検索
        if date_from:
            query = query.filter(Email.received_date >= date_from)
        if date_to:
            query = query.filter(Email.received_date <= date_to)

        emails = query.order_by(
            desc(Email.received_date)
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

        messages = [{
            'id': email.id,
            'sender': email.sender_name or email.sender,
            'content': email.content[:997] + '...' if len(email.content) > 1000 else email.content,
            'received_date': email.received_date.isoformat() if email.received_date else None,
            'is_from_lead': True,
            'type': 'email',
            'read_status': True,
            'metadata': {
                'email_type': getattr(email, 'email_type', 'regular'),
                'has_attachments': bool(getattr(email, 'attachments', False))
            }
        } for email in emails.items]

        return jsonify({
            'messages': messages,
            'has_next': emails.has_next,
            'next_page': emails.next_num if emails.has_next else None,
            'total': emails.total,
            'lead': {
                'id': lead.id,
                'name': lead.name,
                'email': lead.email,
                'status': lead.status,
                'last_contact': lead.last_contact.isoformat() if lead.last_contact else None
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error in get_history: {str(e)}")
        return jsonify({'error': 'データの取得中にエラーが発生しました'}), 500