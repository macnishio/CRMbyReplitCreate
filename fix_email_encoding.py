from app import create_app
from models import Email
from extensions import db
from email_receiver import clean_string
import logging

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
                    content = email.content
                    
                    # Skip if content is None
                    if content is None:
                        continue
                        
                    # Handle bytes content
                    if isinstance(content, bytes):
                        # Check for $B marker which indicates iso-2022-jp encoding
                        if b'$B' in content:
                            try:
                                decoded = content.decode('iso-2022-jp')
                                if decoded and not all(c == '?' for c in decoded):
                                    email.content = clean_string(decoded)
                                    fixed_count += 1
                                    continue
                            except UnicodeDecodeError:
                                pass

                        # Try different encodings in order of likelihood for Japanese content
                        encodings = [
                            'iso-2022-jp',
                            'shift_jis',
                            'euc_jp',
                            'utf-8',
                            'cp932'
                        ]
                        
                        decoded = None
                        for encoding in encodings:
                            try:
                                decoded = content.decode(encoding)
                                if decoded and not all(c == '?' for c in decoded):
                                    email.content = clean_string(decoded)
                                    fixed_count += 1
                                    break
                            except (UnicodeDecodeError, LookupError):
                                continue
                                
                        if not decoded:
                            # Use utf-8 with error handling as last resort
                            email.content = clean_string(content.decode('utf-8', errors='replace'))
                            error_count += 1
                            
                    elif isinstance(content, str):
                        # Clean existing string content
                        email.content = clean_string(content)
                        fixed_count += 1
                        
                except Exception as e:
                    logging.error(f"Error processing email {email.id}: {str(e)}")
                    error_count += 1
                    continue
            
            # Commit changes
            db.session.commit()
            print(f"Encoding fix complete. Fixed: {fixed_count}, Errors: {error_count}")
            
        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            db.session.rollback()
            print("Failed to fix email encoding")
            raise

if __name__ == '__main__':
    fix_email_encoding()
