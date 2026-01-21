from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService
from ccsa_auto.ui.components.admin.common import PageHeader, LoadingOverlay, Toast


def create_system_config():
    """创建系统配置页面 - 现代化增强版"""
    loading = LoadingOverlay("加载配置中...")

    # 页面标题
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

        # 任务调度时间配置
        with ui.card().classes(
            "w-full p-6 mb-6 bg-white rounded-xl border border-gray-200 shadow-sm"
        ):
            ui.label("任务调度时间配置").classes(
                "text-lg font-semibold text-gray-800 mb-4"
            )

            with ui.row().classes("items-center gap-4 mb-4 flex-wrap"):
                ui.label("每日一题:").classes("w-20 text-gray-700 font-medium")
                daily_start = ui.number(
                    "开始时间",
                    value=task_details["DAILY"]["hour_range"][0],
                    min=0,
                    max=23,
                ).classes("w-28 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg")
                ui.label("-").classes("text-gray-500")
                daily_end = ui.number(
                    "结束时间",
                    value=task_details["DAILY"]["hour_range"][1],
                    min=0,
                    max=23,
                ).classes("w-28 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg")

            with ui.row().classes("items-center gap-4 mb-4 flex-wrap"):
                ui.label("每周一课:").classes("w-20 text-gray-700 font-medium")
                weekly_start = ui.number(
                    "开始时间",
                    value=task_details["WEEKLY"]["hour_range"][0],
                    min=0,
                    max=23,
                ).classes("w-28 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg")
                ui.label("-").classes("text-gray-500")
                weekly_end = ui.number(
                    "结束时间",
                    value=task_details["WEEKLY"]["hour_range"][1],
                    min=0,
                    max=23,
                ).classes("w-28 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg")

            with ui.row().classes("items-center gap-4 mb-4 flex-wrap"):
                ui.label("每月一考:").classes("w-20 text-gray-700 font-medium")
                monthly_start = ui.number(
                    "开始时间",
                    value=task_details["MONTHLY"]["hour_range"][0],
                    min=0,
                    max=23,
                ).classes("w-28 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg")
                ui.label("-").classes("text-gray-500")
                monthly_end = ui.number(
                    "结束时间",
                    value=task_details["MONTHLY"]["hour_range"][1],
                    min=0,
                    max=23,
                ).classes("w-28 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg")

            save_schedule_btn = ui.button("保存调度时间").classes(
                "bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            )

        # 任务修复器配置
        with ui.card().classes(
            "w-full p-6 mb-6 bg-white rounded-xl border border-gray-200 shadow-sm"
        ):
            ui.label("任务修复器").classes("text-lg font-semibold text-gray-800 mb-4")

            with ui.row().classes("items-center gap-4"):
                fixer_switch = ui.switch(
                    "启用任务修复器", value=config["task_fixer_enabled"]
                )
                ui.label("（自动检测并修复失败的任务）").classes(
                    "text-gray-500 text-sm"
                )

            apply_fixer_btn = ui.button("应用").classes(
                "bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors mt-4"
            )

        # 其他系统信息
        with ui.card().classes(
            "w-full p-6 bg-white rounded-xl border border-gray-200 shadow-sm"
        ):
            ui.label("系统信息").classes("text-lg font-semibold text-gray-800 mb-4")

            with ui.row().classes("items-center gap-4 flex-wrap"):
                with ui.column().classes("p-4 bg-gray-50 rounded-lg"):
                    ui.label("数据库").classes("text-sm text-gray-500")
                    ui.label("SQLite").classes("text-lg font-medium text-gray-800")
                with ui.column().classes("p-4 bg-gray-50 rounded-lg"):
                    ui.label("调度器").classes("text-sm text-gray-500")
                    ui.label("APScheduler").classes("text-lg font-medium text-gray-800")
                with ui.column().classes("p-4 bg-gray-50 rounded-lg"):
                    ui.label("时区").classes("text-sm text-gray-500")
                    ui.label("Asia/Shanghai").classes(
                        "text-lg font-medium text-gray-800"
                    )

        # 定义函数
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

        # 绑定事件
        save_schedule_btn.on("click", save_task_schedule)
        apply_fixer_btn.on("click", toggle_fixer)
