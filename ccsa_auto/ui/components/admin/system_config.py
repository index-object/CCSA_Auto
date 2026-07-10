from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService
from ccsa_auto.ui.components.admin.common import PageHeader, LoadingOverlay, Toast


def create_system_config():
    """创建系统配置页面"""
    loading = LoadingOverlay("加载配置中...")

    header = PageHeader(
        title="系统配置",
        subtitle="管理系统任务调度和功能设置",
        icon="settings",
    )
    header.render()

    result = AdminService.get_system_config()
    if result["success"]:
        config = result["config"]
        task_details = config["task_details"]

        with ui.card().classes(
            "w-full p-6 mb-6 bg-white rounded-2xl border border-gray-200 shadow-sm"
        ):
            with ui.row().classes("items-center justify-between mb-5"):
                with ui.row().classes("items-center gap-3"):
                    with ui.row().classes(
                        "w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 "
                        "flex items-center justify-center shadow-lg shadow-blue-200"
                    ):
                        ui.icon("schedule").classes("w-5 h-5 text-white")
                    ui.label("任务调度时间配置").classes(
                        "text-xl font-bold text-gray-800"
                    )
                ui.button(icon="help_outline", on_click=lambda: None).classes(
                    "p-2 rounded-xl hover:bg-gray-100 text-gray-400 hover:text-blue-600 "
                    "transition-all duration-200"
                ).props("flat round")

            with ui.row().classes(
                "items-center gap-4 mb-5 p-4 bg-blue-50 rounded-xl border border-blue-100 flex-wrap"
            ):
                ui.label("每日一题:").classes(
                    "w-24 text-gray-700 font-semibold text-lg"
                )
                daily_start = ui.number(
                    "开始时间",
                    value=task_details["DAILY"]["hour_range"][0],
                    min=0,
                    max=23,
                ).classes(
                    "w-28 px-3 py-2.5 bg-white border border-gray-200 "
                    "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                )
                ui.label("-").classes("text-gray-500 font-medium")
                daily_end = ui.number(
                    "结束时间",
                    value=task_details["DAILY"]["hour_range"][1],
                    min=0,
                    max=23,
                ).classes(
                    "w-28 px-3 py-2.5 bg-white border border-gray-200 "
                    "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                )

            with ui.row().classes(
                "items-center gap-4 mb-5 p-4 bg-emerald-50 rounded-xl border border-emerald-100 flex-wrap"
            ):
                ui.label("每周一课:").classes(
                    "w-24 text-gray-700 font-semibold text-lg"
                )
                weekly_start = ui.number(
                    "开始时间",
                    value=task_details["WEEKLY"]["hour_range"][0],
                    min=0,
                    max=23,
                ).classes(
                    "w-28 px-3 py-2.5 bg-white border border-gray-200 "
                    "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                )
                ui.label("-").classes("text-gray-500 font-medium")
                weekly_end = ui.number(
                    "结束时间",
                    value=task_details["WEEKLY"]["hour_range"][1],
                    min=0,
                    max=23,
                ).classes(
                    "w-28 px-3 py-2.5 bg-white border border-gray-200 "
                    "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                )

            with ui.row().classes(
                "items-center gap-4 mb-5 p-4 bg-purple-50 rounded-xl border border-purple-100 flex-wrap"
            ):
                ui.label("每月一考:").classes(
                    "w-24 text-gray-700 font-semibold text-lg"
                )
                monthly_start = ui.number(
                    "开始时间",
                    value=task_details["MONTHLY"]["hour_range"][0],
                    min=0,
                    max=23,
                ).classes(
                    "w-28 px-3 py-2.5 bg-white border border-gray-200 "
                    "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                )
                ui.label("-").classes("text-gray-500 font-medium")
                monthly_end = ui.number(
                    "结束时间",
                    value=task_details["MONTHLY"]["hour_range"][1],
                    min=0,
                    max=23,
                ).classes(
                    "w-28 px-3 py-2.5 bg-white border border-gray-200 "
                    "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                )

            save_schedule_btn = ui.button("保存调度时间", icon="save").classes(
                "bg-blue-600 text-white px-8 py-3 rounded-xl hover:bg-blue-700 "
                "transition-all duration-200 shadow-lg shadow-blue-200 hover:shadow-blue-300 "
                "font-medium text-lg"
            )

        with ui.card().classes(
            "w-full p-6 mb-6 bg-white rounded-2xl border border-gray-200 shadow-sm"
        ):
            with ui.row().classes("items-center justify-between mb-5"):
                with ui.row().classes("items-center gap-3"):
                    with ui.row().classes(
                        "w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 "
                        "flex items-center justify-center shadow-lg shadow-emerald-200"
                    ):
                        ui.icon("build").classes("w-5 h-5 text-white")
                    ui.label("任务修复器").classes("text-xl font-bold text-gray-800")
                ui.button(icon="help_outline", on_click=lambda: None).classes(
                    "p-2 rounded-xl hover:bg-gray-100 text-gray-400 hover:text-blue-600 "
                    "transition-all duration-200"
                ).props("flat round")

            with ui.row().classes(
                "items-center gap-4 p-5 bg-emerald-50 rounded-xl border border-emerald-100"
            ):
                fixer_switch = ui.switch(
                    "启用任务修复器", value=config["task_fixer_enabled"]
                ).classes("text-gray-700 text-lg")
                ui.label("（自动检测并修复失败的任务）").classes(
                    "text-gray-500 text-base font-medium"
                )

            apply_fixer_btn = ui.button("应用", icon="check_circle").classes(
                "bg-emerald-600 text-white px-8 py-3 rounded-xl hover:bg-emerald-700 "
                "transition-all duration-200 shadow-lg shadow-emerald-200 hover:shadow-emerald-300 "
                "font-medium text-lg mt-4"
            )

        with ui.card().classes(
            "w-full p-6 bg-white rounded-2xl border border-gray-200 shadow-sm"
        ):
            with ui.row().classes("items-center justify-between mb-5"):
                with ui.row().classes("items-center gap-3"):
                    with ui.row().classes(
                        "w-10 h-10 rounded-xl bg-gradient-to-br from-gray-500 to-gray-600 "
                        "flex items-center justify-center shadow-lg"
                    ):
                        ui.icon("info").classes("w-5 h-5 text-white")
                    ui.label("系统信息").classes("text-xl font-bold text-gray-800")

            with ui.row().classes("items-center gap-5 flex-wrap"):
                with ui.column().classes(
                    "flex-1 min-w-[180px] p-5 bg-gray-50 rounded-xl border border-gray-200 "
                    "hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
                ):
                    ui.label("数据库").classes(
                        "text-sm text-gray-500 font-semibold uppercase tracking-wide"
                    )
                    ui.label("SQLite").classes(
                        "text-2xl font-bold text-gray-800 mt-2 tracking-tight"
                    )

                with ui.column().classes(
                    "flex-1 min-w-[180px] p-5 bg-blue-50 rounded-xl border border-blue-200 "
                    "hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
                ):
                    ui.label("调度器").classes(
                        "text-sm text-gray-500 font-semibold uppercase tracking-wide"
                    )
                    ui.label("APScheduler").classes(
                        "text-2xl font-bold text-gray-800 mt-2 tracking-tight"
                    )

                with ui.column().classes(
                    "flex-1 min-w-[180px] p-5 bg-purple-50 rounded-xl border border-purple-200 "
                    "hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
                ):
                    ui.label("时区").classes(
                        "text-sm text-gray-500 font-semibold uppercase tracking-wide"
                    )
                    ui.label("Asia/Shanghai").classes(
                        "text-2xl font-bold text-gray-800 mt-2 tracking-tight"
                    )

        def save_task_schedule():
            result = AdminService.update_task_schedule_config(
                int(daily_start.value),
                int(daily_end.value),
                int(weekly_start.value),
                int(weekly_end.value),
                int(monthly_start.value),
                int(monthly_end.value),
            )
            if result["success"]:
                Toast.success(result["message"])
            else:
                Toast.error(result["message"])

        def toggle_fixer():
            result = AdminService.toggle_task_fixer(fixer_switch.value)
            if result["success"]:
                Toast.success(result["message"])
            else:
                Toast.error(result["message"])

        save_schedule_btn.on("click", save_task_schedule)
        apply_fixer_btn.on("click", toggle_fixer)
