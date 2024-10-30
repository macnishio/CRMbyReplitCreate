from app import create_app
from models import Email
from extensions import db
from email_encoding import convert_encoding, clean_email_content
import logging
from sqlalchemy.exc import SQLAlchemyError

def fix_email_encoding():
    """Fix encoding of stored email content"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get all emails
            emails = Email.query.all()
            fixed_count = 0
            error_count = 0
            
            for email in emails:
                try:
                    if email.content is None:
                        continue
                        
                    # Convert and clean content
                    decoded_content, encoding = convert_encoding(email.content)
                    cleaned_content = clean_email_content(decoded_content)
                    
                    # Only update if content changed
                    if cleaned_content != email.content:
                        email.content = cleaned_content
                        fixed_count += 1
                        
                except Exception as e:
                    logging.error(f"Error processing email {email.id}: {str(e)}")
                    error_count += 1
                    continue
            
            if fixed_count > 0:
                db.session.commit()
            
            print(f"Encoding fix complete. Fixed: {fixed_count}, Errors: {error_count}")
            
        except SQLAlchemyError as e:
            logging.error(f"Database error: {str(e)}")
            db.session.rollback()
            print("Failed to fix email encoding")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            db.session.rollback()
            print("Failed to fix email encoding")
            raise

if __name__ == '__main__':
    fix_email_encoding()
