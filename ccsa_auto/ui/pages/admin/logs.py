from nicegui import ui
from ccsa_auto.ui.components.admin import (
    admin_sidebar,
    breadcrumb,
    AdminButton,
    AdminInput,
    AdminSelect,
)


@ui.page("/admin/logs")
def admin_logs():
    def export_logs():
        ui.notify("正在导出日志...", type="info")

    def show_log_detail(log_id: int):
        ui.notify(f"查看日志详情: {log_id}", type="info")

    def refresh_logs():
        ui.notify("日志已刷新", type="positive")

    logs_data = [
        {
            "id": 1,
            "time": "10:23:45",
            "type": "success",
            "level": "INFO",
            "module": "认证",
            "message": "用户 [admin] 登录成功",
            "ip": "192.168.1.100",
        },
        {
            "id": 2,
            "time": "10:15:32",
            "type": "warning",
            "level": "WARNING",
            "module": "任务",
            "message": "任务 [每日一题] 执行超时，已重试",
            "ip": "system",
        },
        {
            "id": 3,
            "time": "09:45:18",
            "type": "info",
            "level": "INFO",
            "module": "配置",
            "message": "系统配置已更新，更新者: admin",
            "ip": "192.168.1.100",
        },
        {
            "id": 4,
            "time": "09:30:00",
            "type": "success",
            "level": "INFO",
            "module": "公告",
            "message": "公告 [关于清明节放假通知] 已发布",
            "ip": "192.168.1.100",
        },
        {
            "id": 5,
            "time": "09:00:00",
            "type": "info",
            "level": "INFO",
            "module": "任务",
            "message": "每日一题任务自动执行完成，成功率 95.5%",
            "ip": "system",
        },
        {
            "id": 6,
            "time": "08:45:22",
            "type": "error",
            "level": "ERROR",
            "module": "系统",
            "message": "数据库连接超时，3秒后重连成功",
            "ip": "system",
        },
        {
            "id": 7,
            "time": "08:30:10",
            "type": "success",
            "level": "INFO",
            "module": "用户",
            "message": "用户 [zhangsan] 账户状态更新: 正常 → 封禁",
            "ip": "192.168.1.101",
        },
    ]

    def get_level_style(level: str):
        styles = {
            "INFO": ("blue", "bg-blue-500/20 text-blue-400"),
            "WARNING": ("amber", "bg-amber-500/20 text-amber-400"),
            "ERROR": ("red", "bg-red-500/20 text-red-400"),
            "DEBUG": ("gray", "bg-slate-500/20 text-slate-400"),
        }
        return styles.get(level, ("gray", "bg-slate-500/20 text-slate-400"))

    columns = [
        {"name": "time", "label": "时间", "field": "time", "align": "center"},
        {"name": "level", "label": "级别", "field": "level", "align": "center"},
        {"name": "module", "label": "模块", "field": "module", "align": "center"},
        {"name": "message", "label": "消息", "field": "message"},
        {"name": "ip", "label": "IP", "field": "ip", "align": "center"},
    ]

    with ui.row().classes("w-full h-screen bg-slate-900 overflow-hidden"):
        admin_sidebar("/admin/logs")

        with ui.column().classes("flex-1 h-full"):
            with ui.row().classes(
                "items-center justify-between px-8 py-6 border-b border-slate-700 bg-slate-900 flex-shrink-0"
            ):
                with ui.column():
                    breadcrumb(
                        [
                            {"label": "首页", "route": "/admin"},
                            {"label": "操作日志"},
                        ]
                    )
                    ui.label("操作日志").classes("text-2xl font-bold text-white mt-2")

                from ccsa_auto.ui.components.admin.toolbar import toolbar

                toolbar(
                    search_placeholder="搜索日志...",
                    filters=["全部类型", "INFO", "WARNING", "ERROR"],
                    actions=[
                        {
                            "icon": "refresh",
                            "on_click": refresh_logs,
                            "style": "secondary",
                        },
                        {
                            "icon": "download",
                            "text": "导出",
                            "on_click": export_logs,
                            "style": "secondary",
                        },
                    ],
                ).render()

            with ui.column().classes("flex-1 overflow-y-auto"):
                with ui.column().classes("w-full p-6"):
                    with ui.card().classes(
                        "w-full bg-slate-800 rounded-xl border border-slate-700 "
                        "hover:border-slate-600 transition-all duration-300"
                    ):
                        with ui.row().classes(
                            "px-6 py-3 border-b border-slate-700 "
                            "items-center gap-4 text-slate-400 text-sm font-medium flex-wrap"
                        ):
                            ui.label("时间").classes("w-24")
                            ui.label("级别").classes("w-20")
                            ui.label("模块").classes("w-20")
                            ui.label("消息").classes("flex-1")
                            ui.label("IP").classes("w-32")
                            ui.label("操作").classes("w-20")

                        with ui.column().classes("divide-y divide-slate-700"):
                            for log in logs_data:
                                color, badge_class = get_level_style(log["level"])

                                with ui.row().classes(
                                    "px-6 py-3 items-center gap-4 "
                                    "hover:bg-slate-700/50 transition-colors cursor-pointer flex-wrap"
                                ) as log_row:

                                    def handle_click(l=log):
                                        show_log_detail(l["id"])

                                    log_row.on("click", handle_click)
                                    ui.label(log["time"]).classes(
                                        "w-24 text-slate-300 text-sm font-mono"
                                    )
                                    ui.label(log["level"]).classes(
                                        f"w-20 px-2 py-0.5 rounded text-xs font-medium text-center {badge_class}"
                                    )
                                    ui.label(log["module"]).classes(
                                        "w-20 text-slate-300 text-sm text-center"
                                    )
                                    ui.label(log["message"]).classes(
                                        "flex-1 text-slate-300 text-sm truncate"
                                    )
                                    ui.label(log["ip"]).classes(
                                        "w-32 text-slate-500 text-sm font-mono text-center"
                                    )
                                    AdminButton.icon_sm(
                                        "visibility",
                                        on_click=lambda l=log: show_log_detail(l["id"]),
                                    ).classes("p-1")

                        with ui.row().classes(
                            "items-center justify-between px-6 py-4 border-t border-slate-700 flex-wrap gap-4"
                        ):
                            ui.label(f"共 {len(logs_data)} 条记录").classes(
                                "text-slate-400 text-sm"
                            )
                            with ui.row().classes("items-center gap-2"):
                                ui.button("上一页").classes(
                                    "bg-slate-700 text-white text-sm px-3 py-1.5 rounded-lg"
                                )
                                ui.label("1 / 5").classes("text-white text-sm")
                                ui.button("下一页").classes(
                                    "bg-slate-700 text-white text-sm px-3 py-1.5 rounded-lg"
                                )
