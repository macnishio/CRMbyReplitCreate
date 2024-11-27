from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .lead import Lead
    from .email import Email
    from .unknown_email import UnknownEmail
    from .opportunity import Opportunity
    from .account import Account
    from .schedule import Schedule
    from .task import Task
    from .task_status_change import TaskStatusChange
    from .user_settings import UserSettings
    from .subscription import SubscriptionPlan, Subscription
    from .email_fetch_tracker import EmailFetchTracker
    from .system_changes import SystemChange, RollbackHistory

# システム変更とロールバック履歴
from .system_changes import SystemChange, RollbackHistory

# ユーザー関連
from .user import User
from .user_settings import UserSettings

# サブスクリプション関連
from .subscription import SubscriptionPlan, Subscription

# メイン機能
from .lead import Lead
from .email import Email
from .unknown_email import UnknownEmail
from .opportunity import Opportunity
from .account import Account
from .schedule import Schedule

# タスク関連
from .task_status_change import TaskStatusChange
from .task import Task

# その他
from .email_fetch_tracker import EmailFetchTracker

__all__ = [
    'SystemChange', 'RollbackHistory',
    'User', 'Lead', 'Email', 'UnknownEmail',
    'Opportunity', 'Account', 'Schedule', 'Task',
    'TaskStatusChange', 'UserSettings', 
    'SubscriptionPlan', 'Subscription',
    'EmailFetchTracker'
]
