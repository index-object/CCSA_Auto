"""主页面模块 - 基于app.storage.user的会话隔离版本"""

from nicegui import ui, app
from ccsa_auto.ui.components.announcement_section import create_announcement_section
from ccsa_auto.ui.components.profile_section import create_profile_section
from ccsa_auto.ui.components.task_section import create_task_section
from ccsa_auto.ui.pages.three_one_page import create_three_one_page
from ccsa_auto.ui.utils.loading_utils import create_loading_button
from ccsa_auto.utils.timezone import get_current_time, format_datetime_for_display


def create_main_page(navigate_to):
    """创建主页面

    Args:
        navigate_to: 导航函数，用于页面跳转
    """
    # 获取用户信息
    user_info = app.storage.user.get("user_info", {})
    username = user_info.get("username", "用户")

    # 主内容区域 - 使用响应式网格布局
    # 宽屏（lg以上）：两列布局（1:2比例）
    # 窄屏（md以下）：单列垂直布局
    with ui.grid().classes("w-full gap-6 grid-cols-1 lg:grid-cols-3"):
        # 左侧区域 - 在宽屏占1列，在窄屏为全宽
        with ui.column().classes("gap-6 lg:col-span-1"):
            create_announcement_section()
            create_profile_section()

        # 右侧区域 - 在宽屏占2列，在窄屏为全宽
        with ui.column().classes("gap-6 lg:col-span-2"):
            create_three_one_page()
            create_task_section()

    # 底部区域
    with ui.card().classes(
        "w-full mt-8 text-center text-gray-600 text-sm bg-gray-50 p-4 rounded-lg shadow-sm"
    ):
        ui.label(
            "陕西精益化工有限公司 用户答题托管平台 © 2026 | 数据更新时间: "
            + format_datetime_for_display(get_current_time(), "%Y-%m-%d %H:%M")
        )

    # 保留管理员入口按钮（针对管理员用户）
    if user_info.get("username") == "admin":
        with ui.row().classes("w-full justify-center mt-6"):

            def navigate_to_admin():
                navigate_to("admin")

            create_loading_button(
                "管理后台", on_click=navigate_to_admin, icon="admin_panel_settings"
            ).classes(
                "bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg shadow-lg"
            )
