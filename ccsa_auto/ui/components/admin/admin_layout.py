from nicegui import ui
from typing import Callable, Dict, Tuple
from ccsa_auto.utils.timezone import get_current_time


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
        "color": "text-emerald-600",
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
        "w-full items-center justify-between px-6 py-4 bg-white border-b "
        "border-gray-200 shadow-sm sticky top-0 z-50 backdrop-blur-sm bg-white/95"
    ):
        with ui.row().classes("items-center gap-4"):
            with ui.row().classes(
                "w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 "
                "flex items-center justify-center shadow-lg shadow-blue-500/20"
            ):
                ui.icon("admin_panel_settings").classes("w-6 h-6 text-white")
            ui.label("管理后台").classes(
                "text-2xl font-bold text-gray-800 tracking-tight"
            )

        with ui.row().classes("items-center gap-4"):
            if show_time:
                time_label = ui.label().classes(
                    "text-base font-mono text-gray-600 bg-gray-50 px-4 py-2 "
                    "rounded-lg border border-gray-200 font-medium"
                )

                def update_time():
                    current_time = get_current_time()
                    time_label.text = current_time.strftime("%Y-%m-%d %H:%M:%S")

                update_time()
                ui.timer(1.0, update_time)

            with ui.row().classes("items-center gap-2"):
                ui.button(icon="refresh", on_click=lambda: None).classes(
                    "p-2.5 rounded-xl hover:bg-gray-100 text-gray-500 hover:text-blue-600 "
                    "transition-all duration-200 hover:shadow-md"
                ).props("flat round")
                ui.button(icon="notifications", on_click=lambda: None).classes(
                    "p-2.5 rounded-xl hover:bg-gray-100 text-gray-500 hover:text-blue-600 "
                    "transition-all duration-200 hover:shadow-md"
                ).props("flat round")
                ui.separator().classes("h-8 w-px bg-gray-200 mx-2")
                with (
                    ui.button()
                    .classes(
                        "items-center gap-3 px-4 py-2 rounded-xl hover:bg-gray-100 "
                        "transition-all duration-200 border-2 border-transparent hover:border-gray-200"
                    )
                    .props("flat")
                ):
                    with ui.row().classes(
                        "w-10 h-10 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 "
                        "flex items-center justify-center"
                    ):
                        ui.icon("account_circle").classes("w-6 h-6 text-gray-600")
                    with ui.column().classes("items-start"):
                        ui.label("管理员").classes(
                            "text-base font-semibold text-gray-700"
                        )
                        ui.label("超级管理员").classes("text-sm text-gray-400")


def create_sidebar(current_tab: str, on_tab_change: Callable):
    """创建现代化侧边栏"""
    with ui.column().classes("flex-1 overflow-auto p-4 gap-1"):
        with ui.row().classes(
            "items-center gap-2 px-3 py-3 mb-2 border-b border-gray-200"
        ):
            ui.icon("menu").classes("w-5 h-5 text-gray-400")
            ui.label("功能菜单").classes(
                "text-xs font-bold text-gray-400 uppercase tracking-wider"
            )

        for tab in ADMIN_TABS:
            is_active = current_tab == tab["id"]
            if is_active:
                active_classes = (
                    "bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 shadow-sm "
                    "border-l-4 border-blue-600 pl-3"
                )
                icon_color = "text-blue-600"
            else:
                active_classes = "hover:bg-gray-100 text-gray-600 pl-4"
                icon_color = "text-gray-400"

            with (
                ui.row()
                .classes(
                    f"w-full items-center gap-3 px-4 py-3.5 rounded-xl transition-all "
                    f"duration-200 cursor-pointer {active_classes}"
                )
                .on(
                    "click",
                    lambda tab_id=tab["id"]: on_tab_change(tab_id)
                    if tab_id != current_tab
                    else None,
                )
            ):
                ui.icon(tab["icon"]).classes(f"w-5 h-5 {icon_color}")
                ui.label(tab["label"]).classes("text-base font-medium")
                if is_active:
                    ui.icon("chevron_right").classes("w-5 h-5 ml-auto text-blue-600")

        ui.separator().classes("my-4 border-gray-200")
        with ui.row().classes(
            "items-center gap-3 px-4 py-3 rounded-xl cursor-pointer "
            "hover:bg-gray-100 text-gray-500 hover:text-blue-600 transition-all duration-200"
        ):
            ui.icon("help_outline").classes("w-5 h-5")
            ui.label("帮助文档").classes("text-base font-medium")
        with ui.row().classes(
            "items-center gap-3 px-4 py-3 rounded-xl cursor-pointer "
            "hover:bg-red-50 text-gray-500 hover:text-red-600 hover:shadow-sm "
            "transition-all duration-200"
        ):
            ui.icon("logout").classes("w-5 h-5")
            ui.label("退出登录").classes("text-base font-medium")


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
                "flex-1 overflow-auto p-8 bg-gray-50"
            )
            with content_container:
                render_content(current_tab)
    return sidebar_container, content_container
