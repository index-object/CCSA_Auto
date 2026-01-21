"""管理后台页面模块 - 模块化重构版本"""

from nicegui import ui

from ccsa_auto.ui.components.admin.admin_layout import (
    create_admin_layout,
    create_sidebar,
    TAB_LABELS,
)
from ccsa_auto.ui.components.admin.user_management import create_user_management
from ccsa_auto.ui.components.admin.task_management import create_task_management
from ccsa_auto.ui.components.admin.announcement_management import (
    create_announcement_management,
)
from ccsa_auto.ui.components.admin.log_management import create_log_management
from ccsa_auto.ui.components.admin.system_config import create_system_config
from ccsa_auto.ui.components.admin.statistics import create_statistics


MODULE_MAP = {
    "users": create_user_management,
    "tasks": create_task_management,
    "announcements": create_announcement_management,
    "logs": create_log_management,
    "config": create_system_config,
    "statistics": create_statistics,
}


def create_admin_page():
    current_tab = ui.context.client.storage.get("admin_tab", "users")

    def render_content(tab_id: str):
        ui.label(TAB_LABELS.get(tab_id, "")).classes(
            "text-2xl font-bold text-gray-800 mb-6"
        )
        module = MODULE_MAP.get(tab_id)
        if module:
            module()

    def on_tab_change(tab_id: str):
        ui.context.client.storage["admin_tab"] = tab_id
        sidebar_container.clear()
        with sidebar_container:
            create_sidebar(tab_id, on_tab_change)
        content_container.clear()
        with content_container:
            render_content(tab_id)

    sidebar_container, content_container = create_admin_layout(
        current_tab, on_tab_change, render_content
    )
