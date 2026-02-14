"""Admin V2 - Modern Admin Dashboard"""

# Page imports
from ccsa_auto.admin_v2.pages.dashboard import create_dashboard_page
from ccsa_auto.admin_v2.pages.users import create_users_page
from ccsa_auto.admin_v2.pages.tasks import create_tasks_page
from ccsa_auto.admin_v2.pages.announcements import create_announcements_page
from ccsa_auto.admin_v2.pages.logs import create_logs_page
from ccsa_auto.admin_v2.pages.settings import create_settings_page

# Service imports
from ccsa_auto.admin_v2.services.dashboard_service import DashboardService
from ccsa_auto.admin_v2.services.user_service import UserService
from ccsa_auto.admin_v2.services.task_service import TaskManagementService
from ccsa_auto.admin_v2.services.announcement_service import (
    AnnouncementManagementService,
)
from ccsa_auto.admin_v2.services.log_service import LogManagementService

# Store imports
from ccsa_auto.admin_v2.stores.admin_store import AdminStore, ADMIN_PERMISSIONS
from ccsa_auto.admin_v2.stores.ui_store import UIStore

__all__ = [
    # Pages
    "create_dashboard_page",
    "create_users_page",
    "create_tasks_page",
    "create_announcements_page",
    "create_logs_page",
    "create_settings_page",
    # Services
    "DashboardService",
    "UserService",
    "TaskManagementService",
    "AnnouncementManagementService",
    "LogManagementService",
    # Stores
    "AdminStore",
    "UIStore",
    "ADMIN_PERMISSIONS",
]
