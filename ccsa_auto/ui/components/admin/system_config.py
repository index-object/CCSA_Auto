from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService


def create_system_config():
    result = AdminService.get_system_config()
    if result["success"]:
        config = result["config"]
        task_details = config["task_details"]

        with ui.column().classes("w-full"):
            ui.label("任务调度时间配置").classes(
                "text-lg font-bold mb-4 mt-2 text-gray-800"
            )

            with ui.card().classes("w-full p-4 mb-4"):
                with ui.row().classes("items-center gap-4 mb-3"):
                    ui.label("每日一题:").classes("w-20 text-gray-700")
                    daily_start = ui.number(
                        "开始",
                        value=task_details["DAILY"]["hour_range"][0],
                        min=0,
                        max=23,
                    ).classes("w-24")
                    ui.label("-").classes("text-gray-500")
                    daily_end = ui.number(
                        "结束",
                        value=task_details["DAILY"]["hour_range"][1],
                        min=0,
                        max=23,
                    ).classes("w-24")

                with ui.row().classes("items-center gap-4 mb-3"):
                    ui.label("每周一课:").classes("w-20 text-gray-700")
                    weekly_start = ui.number(
                        "开始",
                        value=task_details["WEEKLY"]["hour_range"][0],
                        min=0,
                        max=23,
                    ).classes("w-24")
                    ui.label("-").classes("text-gray-500")
                    weekly_end = ui.number(
                        "结束",
                        value=task_details["WEEKLY"]["hour_range"][1],
                        min=0,
                        max=23,
                    ).classes("w-24")

                with ui.row().classes("items-center gap-4 mb-3"):
                    ui.label("每月一考:").classes("w-20 text-gray-700")
                    monthly_start = ui.number(
                        "开始",
                        value=task_details["MONTHLY"]["hour_range"][0],
                        min=0,
                        max=23,
                    ).classes("w-24")
                    ui.label("-").classes("text-gray-500")
                    monthly_end = ui.number(
                        "结束",
                        value=task_details["MONTHLY"]["hour_range"][1],
                        min=0,
                        max=23,
                    ).classes("w-24")

            def save_task_schedule():
                result = AdminService.update_task_schedule_config(
                    int(daily_start.value),
                    int(daily_end.value),
                    int(weekly_start.value),
                    int(weekly_end.value),
                    int(monthly_start.value),
                    int(monthly_end.value),
                )
                ui.notify(
                    result["message"],
                    type="positive" if result["success"] else "negative",
                )

            ui.button("保存调度时间", on_click=save_task_schedule).classes(
                "bg-blue-600 text-white hover:bg-blue-700"
            )

            ui.label("任务修复器").classes("text-lg font-bold mb-4 mt-6 text-gray-800")

            with ui.card().classes("w-full p-4"):
                fixer_enabled = ui.switch(
                    "启用任务修复器", value=config["task_fixer_enabled"]
                )

                def toggle_fixer():
                    result = AdminService.toggle_task_fixer(fixer_enabled.value)
                    ui.notify(
                        result["message"],
                        type="positive" if result["success"] else "negative",
                    )

                ui.button("应用", on_click=toggle_fixer).classes(
                    "bg-green-600 text-white hover:bg-green-700 mt-3"
                )
