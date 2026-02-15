from nicegui import ui
from datetime import datetime

from ccsa_auto.admin_v2.services.dashboard_service import DashboardService
from ccsa_auto.admin_v2.stores.admin_store import AdminStore
from ccsa_auto.modules.auth.user_state import UserStateService
from ccsa_auto.utils.timezone import get_current_time


STATS_ICONS = {
    "users": "👥",
    "new_users": "➕",
    "active_tasks": "📋",
    "completed": "✅",
    "failed": "❌",
    "announcements": "📢",
}

STATS_COLORS = {
    "users": {"icon_bg": "bg-[#dbeafe]", "subtext": "text-[#10b981]"},
    "new_users": {"icon_bg": "bg-[#d1fae5]", "subtext": "text-[#10b981]"},
    "active_tasks": {"icon_bg": "bg-[#ede9fe]", "subtext": "text-[#8b5cf6]"},
    "completed": {"icon_bg": "bg-[#d1fae5]", "subtext": "text-[#10b981]"},
    "failed": {"icon_bg": "bg-[#fee2e2]", "subtext": "text-[#ef4444]"},
    "announcements": {"icon_bg": "bg-[#fef3c7]", "subtext": "text-[#6b7280]"},
}


def create_stat_card(title: str, value: int, icon_key: str, subtitle: str = ""):
    colors = STATS_COLORS.get(icon_key, STATS_COLORS["users"])
    icon = STATS_ICONS.get(icon_key, "📊")

    with ui.card().classes("rounded-2xl p-5 shadow-sm bg-white"):
        with ui.row().classes("items-center gap-4"):
            with ui.element("div").classes(
                f"w-14 h-14 rounded-xl flex items-center justify-center shrink-0 {colors['icon_bg']}"
            ):
                ui.label(icon).classes("text-2xl")
            with ui.column().classes("gap-1 flex-1"):
                ui.label(title).classes("text-sm text-[#6b7280]")
                ui.label(str(value)).classes("text-2xl font-semibold text-[#1f2937]")
                if subtitle:
                    ui.label(subtitle).classes(f"text-xs {colors['subtext']}")


def create_welcome_section():
    admin_name = AdminStore.get_admin_username() or "管理员"
    current_time = get_current_time().strftime("%Y年%m月%d日 %H:%M")

    def handle_logout():
        session_id = ui.context.client.id
        if session_id:
            UserStateService.clear_state(session_id)
        ui.notify("已安全退出登录", type="positive")
        ui.navigate.to("/login")

    with ui.card().classes("rounded-2xl p-6 shadow-sm bg-white"):
        with ui.row().classes("items-center justify-between w-full"):
            with ui.column().classes("gap-2"):
                ui.label(f"欢迎回来，{admin_name}").classes(
                    "text-2xl font-semibold text-[#1f2937]"
                )
                ui.label(f"今天是 {current_time}").classes("text-sm text-[#6b7280]")

            with ui.row().classes("items-center gap-3"):
                refresh_btn = (
                    ui.button()
                    .classes(
                        "bg-[#10b981] hover:bg-[#059669] text-white rounded-full px-5 py-2.5 "
                        "flex items-center gap-2 transition-colors"
                    )
                    .props("flat no-caps")
                )
                refresh_btn.on_click(lambda _: ui.navigate.to("/admin_v2/dashboard"))
                with refresh_btn:
                    ui.icon("refresh").classes("text-white text-lg")
                    ui.label("刷新数据").classes("text-sm font-medium text-white")

                logout_btn = (
                    ui.button()
                    .classes(
                        "bg-[#ef4444] hover:bg-[#dc2626] text-white rounded-full px-5 py-2.5 "
                        "flex items-center gap-2 transition-colors"
                    )
                    .props("flat no-caps")
                )
                logout_btn.on_click(lambda _: handle_logout())
                with logout_btn:
                    ui.icon("logout").classes("text-white text-lg")
                    ui.label("退出登录").classes("text-sm font-medium text-white")


def create_dashboard_page():
    stats_data = {"users": {}, "tasks": {}, "announcements": {}}
    user_trend = []
    task_trend = []
    task_distribution = []
    user_distribution = []

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

    create_welcome_section()

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

    with ui.row().classes("grid grid-cols-1 lg:grid-cols-2 gap-6"):
        with ui.card().classes("rounded-2xl p-6 shadow-sm bg-white"):
            ui.label("用户增长趋势 (近7天)").classes(
                "text-base font-semibold text-[#1f2937] mb-4"
            )
            if user_trend:
                max_count = (
                    max(item["count"] for item in user_trend) if user_trend else 1
                )
                with ui.element("div").classes(
                    "h-44 flex items-end justify-between gap-2"
                ):
                    for item in user_trend:
                        bar_height = (
                            int(item["count"] / max_count * 100) if max_count > 0 else 0
                        )
                        with ui.column().classes("items-center gap-2 flex-1"):
                            with (
                                ui.element("div")
                                .classes(
                                    "w-full bg-[#10b981] rounded-t-md transition-all"
                                )
                                .style(f"height: {max(bar_height, 10)}px")
                            ):
                                pass
                            ui.label(item["date"][-5:]).classes(
                                "text-xs text-[#9ca3af]"
                            )
            else:
                ui.label("暂无数据").classes("text-[#9ca3af] text-center py-8")

        with ui.card().classes("rounded-2xl p-6 shadow-sm bg-white"):
            with ui.row().classes("items-center justify-between mb-4"):
                ui.label("任务执行趋势 (近7天)").classes(
                    "text-base font-semibold text-[#1f2937]"
                )

            if task_trend:
                max_count = (
                    max(
                        max(item.get("completed", 0), item.get("failed", 0))
                        for item in task_trend
                    )
                    if task_trend
                    else 1
                )

                with ui.element("div").classes(
                    "h-44 flex items-end justify-between gap-2"
                ):
                    for item in task_trend:
                        completed_height = (
                            int(item.get("completed", 0) / max_count * 100)
                            if max_count > 0
                            else 0
                        )
                        failed_height = (
                            int(item.get("failed", 0) / max_count * 100)
                            if max_count > 0
                            else 0
                        )

                        with ui.column().classes("items-center gap-1 flex-1"):
                            with ui.row().classes(
                                "items-end gap-0.5 w-full justify-center"
                            ):
                                if completed_height > 0:
                                    with (
                                        ui.element("div")
                                        .classes("w-3 bg-[#22c55e] rounded-t")
                                        .style(f"height: {max(completed_height, 4)}px")
                                    ):
                                        pass
                                if failed_height > 0:
                                    with (
                                        ui.element("div")
                                        .classes("w-3 bg-[#ef4444] rounded-t")
                                        .style(f"height: {max(failed_height, 4)}px")
                                    ):
                                        pass
                            ui.label(item["date"][-5:]).classes(
                                "text-xs text-[#9ca3af]"
                            )

                with ui.row().classes("items-center justify-center gap-6 mt-4"):
                    with ui.row().classes("items-center gap-2"):
                        with ui.element("div").classes(
                            "w-3 h-3 bg-[#22c55e] rounded-sm"
                        ):
                            pass
                        ui.label("完成").classes("text-xs text-[#6b7280]")
                    with ui.row().classes("items-center gap-2"):
                        with ui.element("div").classes(
                            "w-3 h-3 bg-[#ef4444] rounded-sm"
                        ):
                            pass
                        ui.label("失败").classes("text-xs text-[#6b7280]")
            else:
                ui.label("暂无数据").classes("text-[#9ca3af] text-center py-8")

    task_colors = {
        "pending": "#f59e0b",
        "running": "#3b82f6",
        "completed": "#22c55e",
        "failed": "#ef4444",
    }

    task_labels = {
        "pending": "待处理",
        "running": "运行中",
        "completed": "已完成",
        "failed": "失败",
    }

    with ui.row().classes("grid grid-cols-1 lg:grid-cols-2 gap-6"):
        with ui.card().classes("rounded-2xl p-6 shadow-sm bg-white"):
            ui.label("任务状态分布").classes(
                "text-base font-semibold text-[#1f2937] mb-4"
            )

            if task_distribution:
                with ui.row().classes("items-center gap-6"):
                    with ui.element("div").classes("relative w-32 h-32 shrink-0"):
                        svg_parts = []
                        current_angle = 0

                        for item in task_distribution:
                            status = item.get("name", "unknown")
                            percentage = item.get("percentage", 0)
                            color = task_colors.get(status, "#9ca3af")

                            if percentage > 0:
                                angle = percentage * 3.6
                                svg_parts.append(
                                    f'<circle cx="64" cy="64" r="50" fill="none" '
                                    f'stroke="{color}" stroke-width="20" '
                                    f'stroke-dasharray="{angle} {360 - angle}" '
                                    f'transform="rotate({current_angle - 90} 64 64)"/>'
                                )
                                current_angle += angle

                        ui.html(
                            f'<svg viewBox="0 0 128 128" class="w-full h-full">{"".join(svg_parts)}</svg>',
                            sanitize=False,
                        )

                    with ui.column().classes("gap-3 flex-1"):
                        for item in task_distribution:
                            status = item.get("name", "unknown")
                            value = item.get("value", 0)
                            percentage = item.get("percentage", 0)
                            color = task_colors.get(status, "#9ca3af")
                            label = task_labels.get(status, status)

                            with ui.row().classes("items-center gap-3"):
                                with (
                                    ui.element("div")
                                    .classes("w-3 h-3 rounded-sm")
                                    .style(f"background-color: {color}")
                                ):
                                    pass
                                ui.label(f"{label} {value} ({percentage}%)").classes(
                                    "text-sm text-[#6b7280]"
                                )
            else:
                ui.label("暂无数据").classes("text-[#9ca3af] text-center py-8")

        with ui.card().classes("rounded-2xl p-6 shadow-sm bg-white"):
            ui.label("用户状态分布").classes(
                "text-base font-semibold text-[#1f2937] mb-4"
            )

            if user_distribution:
                normal_item = next(
                    (item for item in user_distribution if item.get("name") == "正常"),
                    None,
                )
                disabled_item = next(
                    (item for item in user_distribution if item.get("name") == "禁用"),
                    None,
                )

                normal_pct = normal_item.get("percentage", 85) if normal_item else 85

                with ui.row().classes("items-center gap-6"):
                    with ui.element("div").classes("relative w-28 h-28 shrink-0"):
                        ui.html(
                            f'<svg viewBox="0 0 100 100" class="w-full h-full -rotate-90">'
                            f'<circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" stroke-width="12"/>'
                            f'<circle cx="50" cy="50" r="40" fill="none" stroke="#22c55e" stroke-width="12" '
                            f'stroke-dasharray="{normal_pct * 2.51} 251" stroke-linecap="round"/>'
                            f"</svg>",
                            sanitize=False,
                        )

                    with ui.column().classes("gap-3 flex-1"):
                        if normal_item:
                            with ui.row().classes("items-center gap-3"):
                                with ui.element("div").classes(
                                    "w-3 h-3 rounded-sm bg-[#22c55e]"
                                ):
                                    pass
                                ui.label(
                                    f"正常 {normal_item.get('value', 0)} ({normal_item.get('percentage', 0)}%)"
                                ).classes("text-sm text-[#6b7280]")

                        if disabled_item:
                            with ui.row().classes("items-center gap-3"):
                                with ui.element("div").classes(
                                    "w-3 h-3 rounded-sm bg-[#9ca3af]"
                                ):
                                    pass
                                ui.label(
                                    f"禁用 {disabled_item.get('value', 0)} ({disabled_item.get('percentage', 0)}%)"
                                ).classes("text-sm text-[#6b7280]")
            else:
                ui.label("暂无数据").classes("text-[#9ca3af] text-center py-8")


def render():
    """Render the dashboard page"""
    create_dashboard_page()
