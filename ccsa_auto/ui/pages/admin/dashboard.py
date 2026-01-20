from nicegui import ui
from ccsa_auto.ui.components.admin import (
    admin_sidebar,
    stat_card,
    chart_card,
    breadcrumb,
)


@ui.page("/admin/dashboard")
def admin_dashboard():
    def refresh_data():
        ui.notify("数据已刷新", type="positive")

    with ui.row().classes("w-full h-screen bg-slate-900 overflow-hidden"):
        admin_sidebar("/admin/dashboard")

        with ui.column().classes("flex-1 h-full"):
            with ui.row().classes(
                "items-center justify-between px-8 py-6 border-b border-slate-700 bg-slate-900 flex-shrink-0"
            ):
                with ui.column():
                    breadcrumb(
                        [
                            {"label": "首页", "route": "/admin"},
                            {"label": "仪表盘", "route": "/admin/dashboard"},
                        ]
                    )
                    ui.label("数据概览").classes("text-2xl font-bold text-white mt-2")

                with ui.row().classes("items-center gap-3"):
                    ui.button(icon="refresh", on_click=refresh_data).classes(
                        "bg-slate-700 text-slate-300 hover:text-white "
                        "hover:bg-slate-600 p-2 rounded-lg"
                    )
                    ui.button("导出报表", icon="download").classes(
                        "bg-blue-600 text-white"
                    )

            with ui.column().classes("flex-1 overflow-y-auto"):
                with ui.column().classes("w-full p-6"):
                    stat_cards = [
                        {
                            "title": "用户总数",
                            "value": "1,234",
                            "change": "+12.5%",
                            "change_type": "up",
                            "icon": "people",
                            "icon_color": "blue",
                            "subtitle": "本月新增 89 人",
                        },
                        {
                            "title": "活跃用户",
                            "value": "856",
                            "change": "+8.3%",
                            "change_type": "up",
                            "icon": "trending_up",
                            "icon_color": "green",
                            "subtitle": "今日在线 234 人",
                        },
                        {
                            "title": "今日任务",
                            "value": "89",
                            "change": "+5.2%",
                            "change_type": "up",
                            "icon": "task_alt",
                            "icon_color": "amber",
                            "subtitle": "已完成 82 个",
                        },
                        {
                            "title": "任务成功率",
                            "value": "94.5%",
                            "change": "+2.1%",
                            "change_type": "up",
                            "icon": "verified",
                            "icon_color": "cyan",
                            "subtitle": "较昨日",
                        },
                    ]

                with ui.row().classes(
                    "w-full grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"
                ):
                    for card in stat_cards:
                        stat_card(
                            title=card["title"],
                            value=card["value"],
                            change=card["change"],
                            change_type=card["change_type"],
                            icon=card["icon"],
                            icon_color=card["icon_color"],
                            subtitle=card["subtitle"],
                        )

                with ui.row().classes("w-full grid gap-6 grid-cols-1 lg:grid-cols-2"):
                    chart_card(
                        title="用户增长趋势",
                        chart_id="user-growth-chart",
                        subtitle="近7天用户增长情况",
                    )

                    chart_card(
                        title="任务状态分布",
                        chart_id="task-distribution-chart",
                        subtitle="当前任务执行状态",
                    )

                with ui.row().classes("w-full"):
                    recent_activities = [
                        {
                            "time": "10:23",
                            "type": "success",
                            "icon": "check_circle",
                            "message": "用户 [张三] 登录成功",
                            "user": "admin",
                        },
                        {
                            "time": "10:15",
                            "type": "warning",
                            "icon": "warning",
                            "message": "任务 [每日一题] 执行超时",
                            "user": "system",
                        },
                        {
                            "time": "09:45",
                            "type": "info",
                            "icon": "info",
                            "message": "系统配置已更新",
                            "user": "admin",
                        },
                        {
                            "time": "09:30",
                            "type": "success",
                            "icon": "campaign",
                            "message": "公告 [关于清明节放假通知] 已发布",
                            "user": "admin",
                        },
                        {
                            "time": "09:00",
                            "type": "info",
                            "icon": "autorenew",
                            "message": "每日一题任务自动执行完成",
                            "user": "system",
                        },
                    ]

                    with ui.card().classes(
                        "bg-slate-800 rounded-xl border border-slate-700 "
                        "w-full hover:border-slate-600 transition-all duration-300"
                    ):
                        with ui.row().classes(
                            "items-center justify-between px-6 py-4 border-b border-slate-700"
                        ):
                            ui.label("近期动态").classes(
                                "text-white text-lg font-semibold"
                            )
                            ui.button("查看全部", icon="arrow_forward").classes(
                                "text-blue-400 hover:text-blue-300 text-sm bg-transparent p-0"
                            )

                        with ui.column().classes("p-4 gap-3"):
                            for activity in recent_activities:
                                type_colors = {
                                    "success": "text-green-400",
                                    "warning": "text-amber-400",
                                    "danger": "text-red-400",
                                    "info": "text-blue-400",
                                }
                                icon_class = type_colors.get(
                                    activity["type"], "text-blue-400"
                                )

                                with ui.row().classes(
                                    "items-center gap-4 p-3 rounded-lg "
                                    "hover:bg-slate-700/50 transition-colors cursor-pointer"
                                ):
                                    ui.icon(activity["icon"]).classes(
                                        f"w-5 h-5 {icon_class}"
                                    )
                                    with ui.column().classes("flex-1"):
                                        ui.label(activity["message"]).classes(
                                            "text-white text-sm"
                                        )
                                        ui.label(f"操作者: {activity['user']}").classes(
                                            "text-slate-500 text-xs"
                                        )
                                    ui.label(activity["time"]).classes(
                                        "text-slate-500 text-xs"
                                    )
