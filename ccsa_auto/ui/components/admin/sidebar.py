from nicegui import ui
from typing import Callable, Optional


NAV_ITEMS = [
    {"label": "仪表盘", "icon": "dashboard", "route": "/admin/dashboard"},
    {"label": "用户管理", "icon": "people", "route": "/admin/users"},
    {"label": "任务管理", "icon": "task_alt", "route": "/admin/tasks"},
    {"label": "公告管理", "icon": "campaign", "route": "/admin/announcements"},
    {"label": "操作日志", "icon": "receipt_long", "route": "/admin/logs"},
    {"label": "系统配置", "icon": "settings", "route": "/admin/config"},
]


def nav_item_row(
    label: str,
    icon: str,
    route: str,
    active: bool = False,
    danger: bool = False,
):
    """创建导航项"""
    bg_class = (
        "bg-slate-700/50 border-l-2 border-blue-500" if active and not danger else ""
    )
    hover_class = "hover:bg-red-500/10" if danger else "hover:bg-slate-700/50"
    text_class = (
        "text-blue-400"
        if active and not danger
        else ("text-red-400" if danger else "text-slate-400")
    )
    label_class = (
        "text-white" if active else ("text-red-400" if danger else "text-slate-300")
    )

    with ui.row().classes(
        f"w-full items-center gap-3 px-4 py-3 rounded-lg cursor-pointer "
        f"{hover_class} {bg_class} transition-all duration-200"
    ) as row:
        ui.icon(icon).classes(f"w-5 h-5 {text_class}")
        ui.label(label).classes(
            f"text-sm font-medium {label_class} hover:text-white transition-colors"
        )

    def handle_click():
        target_route = f"{route}?session_id=" + "{session_id}"
        ui.run_javascript(f"""
            (function() {{
                var url = new URL(window.location.href);
                var sessionId = url.searchParams.get('session_id');
                var targetUrl = '{target_route}'.replace('{{session_id}}', sessionId || '');
                if (sessionId) {{
                    window.location.href = targetUrl;
                }} else {{
                    window.location.href = '{route}';
                }}
            }})();
        """)

    row.on("click", handle_click)


def admin_sidebar(current_route: str = "/admin/dashboard", expanded: bool = True):
    """创建管理员侧边栏"""

    sidebar_classes = (
        "h-screen bg-slate-800 border-r border-slate-700 flex flex-col "
        "transition-all duration-300"
    )

    with ui.column().classes(sidebar_classes):
        with ui.row().classes("items-center gap-3 p-4 border-b border-slate-700"):
            ui.icon("admin_panel_settings").classes("w-8 h-8 text-blue-500")
            ui.label("CCSA Auto").classes("text-lg font-bold text-white tracking-wide")

        with ui.column().classes("flex-1 overflow-auto p-3 gap-1"):
            for item in NAV_ITEMS:
                is_active = current_route == item["route"]
                nav_item_row(item["label"], item["icon"], item["route"], is_active)

        with ui.column().classes("p-3 border-t border-slate-700 gap-1"):
            nav_item_row(
                "帮助文档",
                "help_outline",
                "/admin/help",
                current_route == "/admin/help",
            )

            nav_item_row(
                "退出登录",
                "logout",
                "/admin/logout",
                danger=True,
            )


@ui.page("/admin/sidebar-demo")
def sidebar_demo():
    with ui.row().classes("w-full h-screen"):
        admin_sidebar("/admin/dashboard")
        with ui.column().classes("flex-1 bg-slate-900 p-8"):
            ui.label("侧边栏示例").classes("text-2xl font-bold text-white")
