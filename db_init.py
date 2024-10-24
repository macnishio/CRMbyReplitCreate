from app import create_app
from extensions import db
from models import User, UserSettings, Task, Lead, Opportunity, Account, Schedule
from datetime import datetime, timedelta
import os
from sqlalchemy import inspect

def init_db():
    """Initialize database with sample data if tables don't exist"""
    app = create_app()
    with app.app_context():
        try:
            # Check if tables exist
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables:
                # Create all tables
                db.create_all()
                
                # Create admin user
                admin = User(username='admin', email='admin@example.com')
                admin.set_password('admin')
                db.session.add(admin)
                db.session.flush()
                
                # Create user settings with environment variables
                settings = UserSettings(
                    user_id=admin.id,
                    mail_server=os.environ.get('MAIL_SERVER'),
                    mail_port=int(os.environ.get('MAIL_PORT', 587)),
                    mail_use_tls=os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
                    mail_username=os.environ.get('MAIL_USERNAME'),
                    mail_password=os.environ.get('MAIL_PASSWORD'),
                    claude_api_key=os.environ.get('CLAUDE_API_KEY'),
                    clearbit_api_key=os.environ.get('CLEARBIT_API_KEY')
                )
                db.session.add(settings)
                
                # Create sample lead
                lead = Lead(
                    name='Test Lead',
                    email='lead@example.com',
                    status='New',
                    score=0.0,
                    user_id=admin.id
                )
                db.session.add(lead)
                db.session.flush()

                # Create sample account
                account = Account(
                    name='Test Account',
                    industry='Technology',
                    website='www.example.com',
                    user_id=admin.id
                )
                db.session.add(account)
                db.session.flush()

                # Create sample opportunity
                opportunity = Opportunity(
                    name='Test Opportunity',
                    stage='New',
                    amount=1000.0,
                    close_date=datetime.now() + timedelta(days=30),
                    user_id=admin.id,
                    lead_id=lead.id
                )
                db.session.add(opportunity)

                # Create sample tasks
                tasks = [
                    Task(
                        title='提案内容を確認し、営業組織の現状と課題を把握する。',
                        description='営業戦略の改善点を特定するため、現状分析を行う',
                        due_date=datetime.now() + timedelta(days=7),
                        status='New',
                        completed=False,
                        user_id=admin.id,
                        lead_id=lead.id
                    ),
                    Task(
                        title='営業改革の必要性とメリットを判断し、コンサルティングサービスの利用有無を検討する。',
                        description='コスト対効果を含めた総合的な判断を行う',
                        due_date=datetime.now() + timedelta(days=7),
                        status='In Progress',
                        completed=False,
                        user_id=admin.id,
                        lead_id=lead.id
                    )
                ]
                db.session.add_all(tasks)

                # Create sample schedule
                schedule = Schedule(
                    title='営業ミーティング',
                    description='営業戦略についての打ち合わせ',
                    start_time=datetime.now() + timedelta(days=1),
                    end_time=datetime.now() + timedelta(days=1, hours=1),
                    user_id=admin.id,
                    lead_id=lead.id
                )
                db.session.add(schedule)

                db.session.commit()
                print('Database initialized successfully with sample data')
                return True
            else:
                print('Database tables already exist, skipping initialization')
                return True
                
        except Exception as e:
            print(f'Error initializing database: {str(e)}')
            db.session.rollback()
            return False

if __name__ == '__main__':
    init_db()
