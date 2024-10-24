# db_reset_sql.py

from extensions import db
from flask import current_app
from sqlalchemy import text

def reset_database():
    """Reset database using raw SQL commands"""
    with current_app.app_context():
        try:
            # Drop all tables and recreate schema
            sql = text("""
                DROP SCHEMA public CASCADE;
                CREATE SCHEMA public;
                GRANT ALL ON SCHEMA public TO neondb_owner;
                GRANT ALL ON SCHEMA public TO public;
            """)

            current_app.logger.info("Resetting database schema...")
            db.session.execute(sql)
            db.session.commit()

            # Create all tables
            current_app.logger.info("Creating tables...")
            db.create_all()
            db.session.commit()

            current_app.logger.info("Database reset successful")
            return True

        except Exception as e:
            current_app.logger.error(f"Error resetting database: {str(e)}")
            db.session.rollback()
            raise
        finally:
            db.session.close()