from nicegui import ui
from datetime import datetime

from ccsa_auto.admin_v2.services.dashboard_service import DashboardService
from ccsa_auto.admin_v2.stores.admin_store import AdminStore
from ccsa_auto.admin_v2.components.ui.card import Card
from ccsa_auto.admin_v2.components.ui.button import Button
from ccsa_auto.utils.timezone import get_current_time


# Color scheme for statistics cards
STATS_COLORS = {
    "users": {"bg": "bg-blue-50", "icon": "text-blue-500", "icon_bg": "bg-blue-100"},
    "new_users": {
        "bg": "bg-green-50",
        "icon": "text-green-500",
        "icon_bg": "bg-green-100",
    },
    "active_tasks": {
        "bg": "bg-purple-50",
        "icon": "text-purple-500",
        "icon_bg": "bg-purple-100",
    },
    "completed": {
        "bg": "bg-emerald-50",
        "icon": "text-emerald-500",
        "icon_bg": "bg-emerald-100",
    },
    "failed": {"bg": "bg-red-50", "icon": "text-red-500", "icon_bg": "bg-red-100"},
    "announcements": {
        "bg": "bg-amber-50",
        "icon": "text-amber-500",
        "icon_bg": "bg-amber-100",
    },
}

# Icons (using emoji for simplicity - in production use proper icon library)
STATS_ICONS = {
    "users": "👥",
    "new_users": "➕",
    "active_tasks": "📋",
    "completed": "✅",
    "failed": "❌",
    "announcements": "📢",
}


def create_stat_card(title: str, value: int, icon_key: str, subtitle: str = "") -> None:
    """Create a statistics card"""
    colors = STATS_COLORS.get(icon_key, STATS_COLORS["users"])
    icon = STATS_ICONS.get(icon_key, "📊")

    with ui.card().classes("p-6 hover:shadow-lg transition-shadow duration-200"):
        with ui.row().classes("items-center justify-between w-full"):
            with ui.column().classes("gap-1"):
                ui.label(title).classes("text-sm text-gray-500")
                ui.label(str(value)).classes("text-3xl font-bold text-gray-800")
                if subtitle:
                    ui.label(subtitle).classes("text-xs text-gray-400")
            with ui.element("div").classes(
                f"w-14 h-14 rounded-full flex items-center justify-center {colors['icon_bg']}"
            ):
                ui.label(icon).classes("text-2xl")


def create_dashboard_page():
    """Create the dashboard page"""
    stats_data = {"users": {}, "tasks": {}, "announcements": {}}
    user_trend = []
    task_trend = []
    task_distribution = []
    user_distribution = []

    # Fetch data
    try:
        stats_result = DashboardService.get_statistics()
        if stats_result.get("success"):
            stats_data = stats_result.get("data", {})

        user_trend_result = DashboardService.get_user_trend(7)
        if user_trend_result.get("success"):
            user_trend = user_trend_result.get("data", [])

        task_trend_result = DashboardService.get_task_trend(7)
        if task_trend_result.get("success"):
            task_trend = task_trend_result.get("data", [])

        task_dist_result = DashboardService.get_task_status_distribution()
        if task_dist_result.get("success"):
            task_distribution = task_dist_result.get("data", [])

        user_dist_result = DashboardService.get_user_status_distribution()
        if user_dist_result.get("success"):
            user_distribution = user_dist_result.get("data", [])
    except Exception as e:
        ui.notify(f"加载数据失败: {str(e)}", type="negative")

    # Welcome section
    with ui.card().classes("p-6 mb-6"):
        with ui.row().classes("items-center justify-between w-full"):
            with ui.column().classes("gap-1"):
                admin_name = AdminStore.get_admin_username() or "管理员"
                current_time = get_current_time().strftime("%Y年%m月%d日 %H:%M")
                ui.label(f"欢迎回来，{admin_name}").classes("text-2xl font-bold")
                ui.label(f"今天是 {current_time}").classes("text-gray-500")
            with ui.row().classes("gap-2"):
                ui.button(
                    "刷新数据",
                    on_click=lambda: ui.navigate.to("/admin_v2/dashboard"),
                    icon="refresh",
                ).props("flat round")

    # Statistics cards
    users_data = stats_data.get("users", {})
    tasks_data = stats_data.get("tasks", {})
    announcements_data = stats_data.get("announcements", {})

    with ui.row().classes(
        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6"
    ):
        create_stat_card(
            "用户总数",
            users_data.get("total", 0),
            "users",
            f"今日新增 {users_data.get('new_today', 0)}",
        )
        create_stat_card(
            "今日新增",
            users_data.get("new_today", 0),
            "new_users",
            f"本周 {users_data.get('new_week', 0)}",
        )
        create_stat_card(
            "活跃任务",
            tasks_data.get("active", 0),
            "active_tasks",
            f"总计 {tasks_data.get('total', 0)}",
        )
        create_stat_card(
            "今日完成",
            tasks_data.get("completed_today", 0),
            "completed",
            f"成功率 {tasks_data.get('success_rate', 0)}%",
        )
        create_stat_card(
            "失败任务",
            tasks_data.get("failed_today", 0),
            "failed",
            f"总计 {tasks_data.get('failed', 0)}",
        )
        create_stat_card(
            "公告总数", announcements_data.get("total", 0), "announcements", ""
        )

    # Charts section
    with ui.row().classes("grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6"):
        # User trend chart
        with ui.card().classes("p-6"):
            ui.label("用户增长趋势 (近7天)").classes("text-lg font-semibold mb-4")
            if user_trend:
                # Simple bar representation using text
                max_count = (
                    max(item["count"] for item in user_trend) if user_trend else 1
                )
                with ui.column().classes("gap-2"):
                    for item in user_trend:
                        bar_width = (
                            int(item["count"] / max_count * 20) if max_count > 0 else 0
                        )
                        with ui.row().classes("items-center gap-2"):
                            ui.label(item["date"][-5:]).classes(
                                "text-xs text-gray-500 w-12"
                            )
                            with ui.element("div").classes("h-4 bg-blue-100 rounded"):
                                ui.element("div").classes(
                                    "h-full bg-blue-500 rounded"
                                ).style(f"width: {bar_width * 5}px")
                            ui.label(str(item["count"])).classes(
                                "text-xs text-gray-600 w-8"
                            )
            else:
                ui.label("暂无数据").classes("text-gray-400")

        # Task trend chart
        with ui.card().classes("p-6"):
            ui.label("任务执行趋势 (近7天)").classes("text-lg font-semibold mb-4")
            if task_trend:
                max_count = (
                    max(
                        max(item.get("completed", 0), item.get("failed", 0))
                        for item in task_trend
                    )
                    if task_trend
                    else 1
                )
                with ui.column().classes("gap-2"):
                    for item in task_trend:
                        completed_width = (
                            int(item.get("completed", 0) / max_count * 20)
                            if max_count > 0
                            else 0
                        )
                        failed_width = (
                            int(item.get("failed", 0) / max_count * 20)
                            if max_count > 0
                            else 0
                        )
                        with ui.row().classes("items-center gap-2"):
                            ui.label(item["date"][-5:]).classes(
                                "text-xs text-gray-500 w-12"
                            )
                            with ui.element("div").classes(
                                "h-4 bg-emerald-100 rounded flex-1"
                            ):
                                ui.element("div").classes(
                                    "h-full bg-emerald-500 rounded"
                                ).style(f"width: {completed_width * 5}px")
                            with ui.element("div").classes(
                                "h-4 bg-red-100 rounded flex-1"
                            ):
                                ui.element("div").classes(
                                    "h-full bg-red-500 rounded"
                                ).style(f"width: {failed_width * 5}px")
                    # Legend
                    with ui.row().classes("gap-4 mt-2"):
                        with ui.row().classes("items-center gap-1"):
                            ui.element("div").classes(
                                "w-3 h-3 bg-emerald-500 rounded-full"
                            )
                            ui.label("完成").classes("text-xs text-gray-500")
                        with ui.row().classes("items-center gap-1"):
                            ui.element("div").classes("w-3 h-3 bg-red-500 rounded-full")
                            ui.label("失败").classes("text-xs text-gray-500")
            else:
                ui.label("暂无数据").classes("text-gray-400")

    # Status distribution section
    with ui.row().classes("grid grid-cols-1 lg:grid-cols-2 gap-6"):
        # Task status distribution
        with ui.card().classes("p-6"):
            ui.label("任务状态分布").classes("text-lg font-semibold mb-4")
            if task_distribution:
                with ui.column().classes("gap-3"):
                    for item in task_distribution:
                        status_name = item.get("name", "unknown")
                        value = item.get("value", 0)
                        percentage = item.get("percentage", 0)
                        color_class = {
                            "pending": "bg-gray-400",
                            "running": "bg-yellow-400",
                            "completed": "bg-green-500",
                            "failed": "bg-red-500",
                        }.get(status_name, "bg-gray-400")

                        with ui.row().classes("items-center gap-3 w-full"):
                            ui.label(status_name).classes("text-sm w-16")
                            with ui.element("div").classes(
                                "flex-1 h-2 bg-gray-100 rounded-full overflow-hidden"
                            ):
                                ui.element("div").classes(
                                    f"h-full {color_class}"
                                ).style(f"width: {percentage}%")
                            ui.label(f"{value} ({percentage}%)").classes(
                                "text-xs text-gray-500 w-20"
                            )
            else:
                ui.label("暂无数据").classes("text-gray-400")

        # User status distribution
        with ui.card().classes("p-6"):
            ui.label("用户状态分布").classes("text-lg font-semibold mb-4")
            if user_distribution:
                with ui.column().classes("gap-3"):
                    for item in user_distribution:
                        status_name = item.get("name", "unknown")
                        value = item.get("value", 0)
                        percentage = item.get("percentage", 0)
                        color_class = (
                            "bg-green-500" if status_name == "正常" else "bg-red-500"
                        )

                        with ui.row().classes("items-center gap-3 w-full"):
                            ui.label(status_name).classes("text-sm w-16")
                            with ui.element("div").classes(
                                "flex-1 h-2 bg-gray-100 rounded-full overflow-hidden"
                            ):
                                ui.element("div").classes(
                                    f"h-full {color_class}"
                                ).style(f"width: {percentage}%")
                            ui.label(f"{value} ({percentage}%)").classes(
                                "text-xs text-gray-500 w-20"
                            )
            else:
                ui.label("暂无数据").classes("text-gray-400")


def render():
    """Render the dashboard page"""
    create_dashboard_page()
