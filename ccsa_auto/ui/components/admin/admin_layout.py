from nicegui import ui
from typing import Callable, Dict, Tuple


ADMIN_TABS = [
    {"id": "users", "label": "用户管理", "icon": "people"},
    {"id": "tasks", "label": "任务管理", "icon": "task_alt"},
    {"id": "announcements", "label": "公告管理", "icon": "campaign"},
    {"id": "logs", "label": "操作日志", "icon": "receipt_long"},
    {"id": "config", "label": "系统配置", "icon": "settings"},
    {"id": "statistics", "label": "数据统计", "icon": "insights"},
]

TAB_LABELS: Dict[str, str] = {tab["id"]: tab["label"] for tab in ADMIN_TABS}


def create_header():
    with ui.row().classes(
        "w-full items-center justify-between px-6 py-4 bg-white border-b border-gray-200 shadow-sm"
    ):
        with ui.row().classes("items-center gap-3"):
            ui.icon("admin_panel_settings").classes("w-7 h-7 text-blue-600")
            ui.label("管理后台").classes("text-xl font-bold text-gray-800")

        with ui.row().classes("items-center gap-4"):
            ui.icon("account_circle").classes("w-6 h-6 text-gray-500")
            ui.label("管理员").classes("text-gray-600 text-sm")


def create_sidebar(current_tab: str, on_tab_change: Callable):
    with ui.column().classes("flex-1 overflow-auto p-3 gap-1"):
        for tab in ADMIN_TABS:
            is_active = current_tab == tab["id"]
            bg_class = "bg-white shadow-sm" if is_active else ""
            hover_class = "hover:bg-gray-200" if not is_active else ""
            text_class = "text-blue-600 font-medium" if is_active else "text-gray-600"
            cursor_class = "cursor-pointer" if not is_active else ""

            with (
                ui.row()
                .classes(
                    f"w-full items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 "
                    f"{bg_class} {hover_class} {cursor_class}"
                )
                .on(
                    "click",
                    lambda tab_id=tab["id"], active=is_active: on_tab_change(tab_id)
                    if not active
                    else None,
                )
            ):
                ui.icon(tab["icon"]).classes(f"w-5 h-5 {text_class}")
                ui.label(tab["label"]).classes(
                    f"text-sm {text_class} transition-colors"
                )


def create_admin_layout(
    current_tab: str, on_tab_change: Callable, render_content: Callable
) -> Tuple[ui.column, ui.column]:
    with ui.column().classes("w-full h-screen bg-gray-50"):
        create_header()
        with ui.row().classes("flex-1 overflow-hidden"):
            sidebar_container = ui.column().classes(
                "w-64 h-full bg-gray-100 border-r border-gray-200 flex flex-col"
            )
            with sidebar_container:
                create_sidebar(current_tab, on_tab_change)
            content_container = ui.column().classes("flex-1 overflow-auto p-6 bg-white")
            with content_container:
                render_content(current_tab)
    return sidebar_container, content_container
