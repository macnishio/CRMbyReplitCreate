from app import create_app, db
from models import User, Lead, Email, Task, Schedule, Opportunity, Account
from sqlalchemy.exc import SQLAlchemyError
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def verify_model_relationships():
    """データベースモデルの関係性を検証する"""
    try:
        app = create_app('development')
        with app.app_context():
            # 1. メールの重複チェック
            duplicate_emails = db.session.query(Email.message_id, 
                                             db.func.count(Email.message_id))\
                .group_by(Email.message_id)\
                .having(db.func.count(Email.message_id) > 1)\
                .all()

            if duplicate_emails:
                logger.warning(f"重複したメッセージID: {duplicate_emails}")

            # 2. リードと関連エンティティの整合性チェック
            leads = Lead.query.all()
            for lead in leads:
                # メールの存在確認
                emails = Email.query.filter_by(lead_id=lead.id).all()
                logger.info(f"Lead {lead.id}: {len(emails)} emails found")

                # タスクの存在確認
                tasks = Task.query.filter_by(lead_id=lead.id).all()
                logger.info(f"Lead {lead.id}: {len(tasks)} tasks found")

                # スケジュールの存在確認
                schedules = Schedule.query.filter_by(lead_id=lead.id).all()
                logger.info(f"Lead {lead.id}: {len(schedules)} schedules found")

            # 3. 必須フィールドの検証
            users = User.query.all()
            for user in users:
                if not user.email or not user.username:
                    logger.error(f"User {user.id}: Missing required fields")

            # 4. 外部キー制約の検証
            orphaned_emails = Email.query.filter(
                ~Email.lead_id.in_(db.session.query(Lead.id))
            ).all()

            if orphaned_emails:
                logger.error(f"Orphaned emails found: {len(orphaned_emails)}")

            # 5. データベースセッションの状態確認
            logger.info(f"Active database connections: {db.session.info}")

    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")
    finally:
        db.session.remove()

def verify_model_instances():
    """モデルインスタンスの作成と検証"""
    try:
        app = create_app('development')
        with app.app_context():
            # テストユーザーの作成
            test_user = User(
                username="test_user",
                email="test@example.com",
                role="user"
            )
            test_user.set_password("test_password")

            # テストリードの作成
            test_lead = Lead(
                name="Test Lead",
                email="lead@example.com",
                status="New",
                user_id=test_user.id
            )

            # テストメールの作成
            test_email = Email(
                message_id="test_message_id",
                sender="sender@example.com",
                subject="Test Subject",
                content="Test Content",
                lead_id=test_lead.id,
                user_id=test_user.id
            )

            # セッションへの追加とコミット
            db.session.add(test_user)
            db.session.add(test_lead)
            db.session.add(test_email)

            try:
                db.session.commit()
                logger.info("Test instances created successfully")
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Failed to create test instances: {str(e)}")

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
    finally:
        db.session.remove()

if __name__ == "__main__":
    logger.info("Starting database verification...")
    verify_model_relationships()
    verify_model_instances()
    logger.info("Database verification completed")