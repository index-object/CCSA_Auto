from nicegui import ui
from ccsa_auto.ui.components.admin import (
    admin_sidebar,
    breadcrumb,
    AdminButton,
    AdminSelect,
    AdminInput,
    stat_card,
)


@ui.page("/admin/tasks")
def admin_tasks():
    def toggle_task(task_id: int, task_name: str, enabled: bool):
        status = "启用" if enabled else "停用"
        ui.notify(f"任务 [{task_name}] 已{status}", type="positive")

    def execute_task(task_id: int, task_name: str):
        ui.notify(f"正在执行任务 [{task_name}]...", type="info")

    def show_task_detail(task_id: int):
        ui.notify(f"查看任务详情: {task_id}", type="info")

    def refresh_tasks():
        ui.notify("任务列表已刷新", type="positive")

    def create_task():
        ui.notify("新建任务", type="info")

    tasks_data = [
        {
            "id": 1,
            "name": "每日一题",
            "type": "daily",
            "enabled": True,
            "schedule": "每天 09:00-18:00",
            "last_run": "2024-01-17 09:00",
            "next_run": "2024-01-18 09:00",
            "success_rate": 95.5,
        },
        {
            "id": 2,
            "name": "每周一课",
            "type": "weekly",
            "enabled": True,
            "schedule": "周一 10:00",
            "last_run": "2024-01-15 10:00",
            "next_run": "2024-01-22 10:00",
            "success_rate": 92.0,
        },
        {
            "id": 3,
            "name": "每月一考",
            "type": "monthly",
            "enabled": False,
            "schedule": "每月1号 09:00",
            "last_run": "2024-01-01 09:00",
            "next_run": "2024-02-01 09:00",
            "success_rate": 88.5,
        },
        {
            "id": 4,
            "name": "数据同步",
            "type": "custom",
            "enabled": True,
            "schedule": "每小时",
            "last_run": "2024-01-17 10:00",
            "next_run": "2024-01-17 11:00",
            "success_rate": 99.0,
        },
    ]

    with ui.row().classes("w-full h-screen bg-slate-900 overflow-hidden"):
        admin_sidebar("/admin/tasks")

        with ui.column().classes("flex-1 h-full"):
            with ui.row().classes(
                "items-center justify-between px-8 py-6 border-b border-slate-700 bg-slate-900 flex-shrink-0"
            ):
                with ui.column():
                    breadcrumb(
                        [
                            {"label": "首页", "route": "/admin"},
                            {"label": "任务管理"},
                        ]
                    )
                    ui.label("任务管理").classes("text-2xl font-bold text-white mt-2")

                from ccsa_auto.ui.components.admin.toolbar import toolbar

                toolbar(
                    search_placeholder="搜索任务...",
                    filters=[
                        "全部任务",
                        "每日一题",
                        "每周一课",
                        "每月一考",
                        "自定义",
                    ],
                    actions=[
                        {
                            "icon": "refresh",
                            "on_click": refresh_tasks,
                            "style": "secondary",
                        },
                        {
                            "icon": "add",
                            "text": "新建任务",
                            "on_click": create_task,
                            "primary": True,
                        },
                    ],
                ).render()

            with ui.column().classes("flex-1 overflow-y-auto"):
                with ui.column().classes("w-full p-6 gap-6"):
                    with ui.row().classes(
                        "w-full grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"
                    ):
                        stat_card(
                            title="总任务数",
                            value="12",
                            icon="task_alt",
                            icon_color="blue",
                        )
                    stat_card(
                        title="运行中",
                        value="3",
                        icon="play_circle",
                        icon_color="green",
                    )
                    stat_card(
                        title="已停用",
                        value="2",
                        icon="pause_circle",
                        icon_color="amber",
                    )
                    stat_card(
                        title="失败率",
                        value="2.5%",
                        icon="error",
                        icon_color="red",
                    )

                with ui.card().classes(
                    "w-full bg-slate-800 rounded-xl border border-slate-700 "
                    "hover:border-slate-600 transition-all duration-300"
                ):
                    with ui.row().classes(
                        "items-center justify-between px-6 py-4 border-b border-slate-700"
                    ):
                        ui.label("任务列表").classes("text-white text-lg font-semibold")

                    with ui.column().classes("p-4 gap-3"):
                        for task in tasks_data:
                            status_color = "green" if task["enabled"] else "red"
                            status_text = "运行中" if task["enabled"] else "已停用"

                            with ui.card().classes(
                                "bg-slate-700/50 rounded-lg p-4 "
                                "hover:bg-slate-700 transition-all duration-200"
                            ):
                                with ui.row().classes(
                                    "items-center justify-between flex-wrap gap-4"
                                ):
                                    with ui.column().classes("flex-1 min-w-0"):
                                        with ui.row().classes(
                                            "items-center gap-3 flex-wrap"
                                        ):
                                            ui.icon(
                                                "check_circle"
                                                if task["enabled"]
                                                else "cancel"
                                            ).classes(
                                                f"w-6 h-6 {'text-green-400' if task['enabled'] else 'text-red-400'}"
                                            )
                                            ui.label(task["name"]).classes(
                                                "text-white text-lg font-semibold truncate"
                                            )
                                            ui.label(status_text).classes(
                                                f"px-2 py-0.5 rounded-full text-xs font-medium "
                                                f"bg-{status_color}-500/20 text-{status_color}-400"
                                            )

                                        ui.label(
                                            f"执行时间: {task['schedule']}"
                                        ).classes("text-slate-400 text-sm mt-1")
                                        ui.label(
                                            f"成功率: {task['success_rate']}%"
                                        ).classes("text-slate-400 text-sm")

                                    with ui.column().classes("items-end gap-2"):
                                        ui.label(
                                            f"下次执行: {task['next_run']}"
                                        ).classes("text-slate-400 text-sm")
                                        with ui.row().classes(
                                            "items-center gap-2 flex-wrap"
                                        ):
                                            AdminButton.sm(
                                                "详情",
                                                on_click=lambda t=task: show_task_detail(
                                                    t["id"]
                                                ),
                                            )
                                            if task["enabled"]:
                                                AdminButton.sm(
                                                    "停用",
                                                    on_click=lambda t=task: toggle_task(
                                                        t["id"], t["name"], False
                                                    ),
                                                ).classes(
                                                    "bg-amber-600 hover:bg-amber-500"
                                                )
                                                AdminButton.sm(
                                                    "执行",
                                                    on_click=lambda t=task: execute_task(
                                                        t["id"], t["name"]
                                                    ),
                                                ).classes(
                                                    "bg-green-600 hover:bg-green-500"
                                                )
                                            else:
                                                AdminButton.sm(
                                                    "启用",
                                                    on_click=lambda t=task: toggle_task(
                                                        t["id"], t["name"], True
                                                    ),
                                                ).classes(
                                                    "bg-blue-600 hover:bg-blue-500"
                                                )
