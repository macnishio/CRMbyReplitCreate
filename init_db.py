from app import create_app, db
from models import User

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    
    # Create test user if it doesn't exist
    if not User.query.filter_by(email='test@example.com').first():
        user = User(email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        print("Test user created successfully!")
    else:
        print("Test user already exists!")
