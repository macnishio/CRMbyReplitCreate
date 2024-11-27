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
    from .user_settings import UserSettings
    from .subscription import SubscriptionPlan, Subscription
    from .email_fetch_tracker import EmailFetchTracker
    from .system_changes import SystemChange, RollbackHistory
    from .filter_preset import FilterPreset

from .system_changes import SystemChange, RollbackHistory
from .user import User
from .lead import Lead
from .email import Email
from .unknown_email import UnknownEmail
from .opportunity import Opportunity
from .account import Account
from .schedule import Schedule
from .task import Task
from .user_settings import UserSettings
from .subscription import SubscriptionPlan, Subscription
from .email_fetch_tracker import EmailFetchTracker
from .filter_preset import FilterPreset

__all__ = [
    'SystemChange', 'RollbackHistory',
    'User', 'Lead', 'Email', 'UnknownEmail',
    'Opportunity', 'Account', 'Schedule', 'Task',
    'UserSettings', 'SubscriptionPlan', 'Subscription',
    'EmailFetchTracker', 'FilterPreset'
]
