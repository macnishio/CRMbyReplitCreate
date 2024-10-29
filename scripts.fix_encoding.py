from flask import current_app  # Add this import statement
from sqlalchemy import text
from extensions import db
import re

def fix_iso2022jp_text(text):
    if not text:
        return text
        
    try:
        # バイト列に変換
        if isinstance(text, str):
            text = text.encode('utf-8')
            
        # ISO-2022-JPとしてデコード
        decoded = text.decode('iso-2022-jp', errors='replace')
        
        # 制御文字を削除
        decoded = re.sub(r'\$B|\(B', '', decoded)
        
        return decoded.strip()
    except Exception as e:
        current_app.logger.error(f"Error fixing encoding: {str(e)}")
        return text

def fix_encoded_emails():
    with current_app.app_context():
        try:
            # 文字化けしているメールを取得
            emails = Email.query.filter(
                (Email.content.like('%$B%')) |
                (Email.subject.like('%$B%')) |
                (Email.sender_name.like('%$B%'))
            ).all()
            
            for email in emails:
                # 各フィールドを修正
                email.content = fix_iso2022jp_text(email.content)
                email.subject = fix_iso2022jp_text(email.subject)
                email.sender_name = fix_iso2022jp_text(email.sender_name)
            
            db.session.commit()
            print(f"Fixed {len(emails)} emails")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error fixing emails: {str(e)}")

# スクリプトを実行
if __name__ == '__main__':
    fix_encoded_emails()