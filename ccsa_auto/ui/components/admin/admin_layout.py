from nicegui import ui
from typing import Callable, Dict, Tuple
from datetime import datetime
from ccsa_auto.utils.timezone import get_current_time, SHANGHAI_TZ


ADMIN_TABS = [
    {"id": "users", "label": "用户管理", "icon": "people", "color": "text-blue-600"},
    {
        "id": "tasks",
        "label": "任务管理",
        "icon": "task_alt",
        "color": "text-purple-600",
    },
    {
        "id": "announcements",
        "label": "公告管理",
        "icon": "campaign",
        "color": "text-green-600",
    },
    {
        "id": "logs",
        "label": "操作日志",
        "icon": "receipt_long",
        "color": "text-amber-600",
    },
    {"id": "config", "label": "系统配置", "icon": "settings", "color": "text-gray-600"},
    {
        "id": "statistics",
        "label": "数据统计",
        "icon": "insights",
        "color": "text-cyan-600",
    },
]

TAB_LABELS: Dict[str, str] = {tab["id"]: tab["label"] for tab in ADMIN_TABS}
TAB_ICONS: Dict[str, str] = {tab["id"]: tab["icon"] for tab in ADMIN_TABS}
TAB_COLORS: Dict[str, str] = {tab["id"]: tab["color"] for tab in ADMIN_TABS}


def create_header(show_time: bool = True):
    """创建带时间和快捷操作的头部"""
    with ui.row().classes(
        "w-full items-center justify-between px-6 py-3 bg-white border-b "
        "border-gray-200 shadow-sm sticky top-0 z-50"
    ):
        with ui.row().classes("items-center gap-4"):
            ui.icon("admin_panel_settings").classes("w-8 h-8 text-blue-600")
            ui.label("管理后台").classes("text-xl font-bold text-gray-800")
            with ui.row().classes("items-center gap-2 ml-4"):
                ui.icon("chevron_right").classes("w-4 h-4 text-gray-400")
                ui.label("首页").classes(
                    "text-sm text-gray-500 cursor-pointer hover:text-blue-600"
                )
                ui.icon("chevron_right").classes("w-4 h-4 text-gray-400")

        with ui.row().classes("items-center gap-6"):
            if show_time:
                time_label = ui.label().classes("text-sm font-mono text-gray-500")

                def update_time():
                    current_time = get_current_time()
                    time_label.text = current_time.strftime("%Y-%m-%d %H:%M:%S")

                update_time()
                ui.timer(1.0, update_time)
                ui.separator().classes("h-6 w-px bg-gray-300")

            with ui.row().classes("items-center gap-2"):
                ui.button(icon="refresh", on_click=lambda: None).classes(
                    "p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
                ).props("flat round")
                ui.button(icon="notifications", on_click=lambda: None).classes(
                    "p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
                ).props("flat round")
                with ui.row().classes(
                    "items-center gap-2 ml-2 pl-4 border-l border-gray-200"
                ):
                    ui.icon("account_circle").classes("w-8 h-8 text-gray-400")
                    with ui.column().classes("items-start"):
                        ui.label("管理员").classes("text-sm font-medium text-gray-700")
                        ui.label("超级管理员").classes("text-xs text-gray-400")


def create_sidebar(current_tab: str, on_tab_change: Callable):
    """创建现代化侧边栏"""
    with ui.column().classes("flex-1 overflow-auto p-2 gap-1"):
        # 侧边栏标题
        with ui.row().classes(
            "items-center gap-2 px-3 py-3 mb-2 border-b border-gray-200"
        ):
            ui.icon("dashboard").classes("w-5 h-5 text-gray-500")
            ui.label("功能菜单").classes(
                "text-xs font-semibold text-gray-400 uppercase tracking-wider"
            )

        for tab in ADMIN_TABS:
            is_active = current_tab == tab["id"]
            bg_class = "bg-blue-50" if is_active else "hover:bg-gray-100"
            text_class = tab["color"] if is_active else "text-gray-600"
            border_class = "border-l-4 border-blue-600 pl-3" if is_active else "pl-4"

            with (
                ui.row()
                .classes(
                    f"w-full items-center gap-3 px-3 py-2.5 rounded-lg transition-all "
                    f"duration-200 cursor-pointer {bg_class}"
                )
                .on(
                    "click",
                    lambda tab_id=tab["id"]: on_tab_change(tab_id)
                    if tab_id != current_tab
                    else None,
                )
            ):
                ui.icon(tab["icon"]).classes(f"w-5 h-5 {text_class}")
                ui.label(tab["label"]).classes(f"text-sm font-medium {text_class}")
                # 右侧徽章（如果有）
                if is_active:
                    ui.icon("chevron_right").classes("w-4 h-4 ml-auto text-blue-600")

        # 侧边栏底部
        ui.separator().classes("my-2")
        with ui.row().classes(
            "items-center gap-3 px-3 py-2 rounded-lg cursor-pointer "
            "hover:bg-gray-100 text-gray-500 transition-colors"
        ):
            ui.icon("help_outline").classes("w-5 h-5")
            ui.label("帮助文档").classes("text-sm")
        with ui.row().classes(
            "items-center gap-3 px-3 py-2 rounded-lg cursor-pointer "
            "hover:bg-red-50 text-gray-500 hover:text-red-600 transition-colors"
        ):
            ui.icon("logout").classes("w-5 h-5")
            ui.label("退出登录").classes("text-sm")


def create_admin_layout(
    current_tab: str, on_tab_change: Callable, render_content: Callable
) -> Tuple[ui.column, ui.column]:
    """创建现代化管理后台布局"""
    with ui.column().classes("w-full h-screen bg-gray-50"):
        create_header(show_time=True)
        with ui.row().classes("flex-1 overflow-hidden"):
            sidebar_container = ui.column().classes(
                "w-64 h-full bg-white border-r border-gray-200 flex flex-col shadow-sm"
            )
            with sidebar_container:
                create_sidebar(current_tab, on_tab_change)
            content_container = ui.column().classes(
                "flex-1 overflow-auto p-6 bg-gray-50"
            )
            with content_container:
                render_content(current_tab)
    return sidebar_container, content_container
