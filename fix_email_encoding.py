from app import create_app
from models import Email
from extensions import db
from email_encoding import convert_encoding, clean_email_content, analyze_iso2022jp_text
import logging
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

def fix_email_encoding():
    """Fix encoding of stored email content"""
    app = create_app()
    logger = logging.getLogger(__name__)
    
    with app.app_context():
        try:
            # Get all emails that potentially need fixing
            logger.info("Starting email encoding fix process")
            start_time = datetime.utcnow()
            
            # First check for emails with ISO-2022-JP markers
            emails = Email.query.filter(
                Email.content.isnot(None),
                Email.content != ''
            ).all()
            
            fixed_count = 0
            error_count = 0
            
            for email in emails:
                try:
                    if email.content is None:
                        continue
                    
                    content = email.content
                    if isinstance(content, str):
                        try:
                            content = content.encode('utf-8')
                        except UnicodeEncodeError:
                            content = content.encode('utf-8', errors='replace')
                    
                    # Check for ISO-2022-JP content first
                    if analyze_iso2022jp_text(content):
                        try:
                            logger.debug(f"Processing email {email.id} with ISO-2022-JP markers")
                            decoded_content = content.decode('iso-2022-jp')
                            cleaned_content = clean_email_content(decoded_content)
                            
                            if cleaned_content != email.content:
                                email.content = cleaned_content
                                fixed_count += 1
                                logger.info(f"Fixed encoding for email {email.id}")
                        except UnicodeDecodeError:
                            logger.warning(f"ISO-2022-JP decode failed for email {email.id}")
                    else:
                        # Try general encoding conversion
                        decoded_content, encoding = convert_encoding(content)
                        cleaned_content = clean_email_content(decoded_content)
                        
                        if cleaned_content != email.content:
                            email.content = cleaned_content
                            fixed_count += 1
                            logger.info(f"Fixed encoding for email {email.id} using {encoding}")
                    
                    # Commit every 100 records to avoid large transactions
                    if fixed_count % 100 == 0:
                        db.session.commit()
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing email {email.id}: {str(e)}")
                    db.session.rollback()
                    continue
            
            # Final commit for remaining changes
            if fixed_count > 0:
                db.session.commit()
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Encoding fix complete. Fixed: {fixed_count}, Errors: {error_count}")
            logger.info(f"Process took {duration:.2f} seconds")
            print(f"Encoding fix complete. Fixed: {fixed_count}, Errors: {error_count}")
            print(f"Process took {duration:.2f} seconds")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            db.session.rollback()
            print("Failed to fix email encoding")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            db.session.rollback()
            print("Failed to fix email encoding")
            raise

if __name__ == '__main__':
    fix_email_encoding()
