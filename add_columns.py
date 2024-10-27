from app import create_app, db

def add_google_columns():
    app = create_app()
    with app.app_context():
        # Add columns using raw SQL
        with db.engine.connect() as conn:
            try:
                conn.execute(db.text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS google_calendar_id VARCHAR(255),
                    ADD COLUMN IF NOT EXISTS google_service_account_file VARCHAR(255)
                """))
                conn.commit()
                print("Columns added successfully")
            except Exception as e:
                print(f"Error adding columns: {e}")

if __name__ == "__main__":
    add_google_columns()