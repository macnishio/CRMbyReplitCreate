from flask import Flask
from models import Lead, db
from utils import decode_mime_words
import os

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:joi1vh0dIADb@[REDACTED]')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
    db.init_app(app)
    return app

def update_lead_names():
    leads = Lead.query.all()
    updated_count = 0
    for lead in leads:
        original_name = lead.name
        try:
            decoded_name = decode_mime_words(original_name)
            if decoded_name != original_name:
                lead.name = decoded_name
                updated_count += 1
                print(f"Updated: {original_name} -> {decoded_name}")
            else:
                print(f"Unchanged: {original_name}")
        except Exception as e:
            print(f"Error decoding: {original_name} - {str(e)}")
            continue  # エラーが発生しても次のリードの処理を続ける

    if updated_count > 0:
        try:
            db.session.commit()
            print(f"Updated {updated_count} lead names.")
        except Exception as e:
            print(f"Error committing changes to database: {str(e)}")
            db.session.rollback()
    else:
        print("No lead names needed updating.")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        update_lead_names()
    print("Lead name update process completed.")