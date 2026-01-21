from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService


def create_task_management():
    with ui.column().classes("w-full"):
        with ui.row().classes("items-center gap-4 mb-4"):
            task_keyword = ui.input("搜索用户").classes("w-48")
            task_type_select = ui.select(
                {
                    None: "全部",
                    "daily": "每日一题",
                    "weekly": "每周一课",
                    "monthly": "每月一考",
                },
                label="任务类型",
                value=None,
            ).classes("w-32")

        admin_task_table = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id", "align": "center"},
                {"name": "username", "label": "用户", "field": "username"},
                {
                    "name": "task_type",
                    "label": "任务类型",
                    "field": "task_type",
                },
                {
                    "name": "is_active",
                    "label": "启用",
                    "field": "is_active",
                    "align": "center",
                },
                {
                    "name": "execution_status",
                    "label": "执行状态",
                    "field": "execution_status",
                },
                {
                    "name": "scheduled_time",
                    "label": "下次运行时间",
                    "field": "scheduled_time",
                },
            ],
            rows=[],
            row_key="id",
        ).classes("w-full")

        def refresh_tasks():
            result = AdminService.get_all_tasks(
                keyword=task_keyword.value or "",
                task_type=task_type_select.value
                if task_type_select.value is not None
                else None,
            )
            if result["success"]:
                task_type_map = {
                    "daily": "每日一题",
                    "weekly": "每周一课",
                    "monthly": "每月一考",
                }
                status_map = {
                    "pending": "待执行",
                    "running": "执行中",
                    "completed": "已完成",
                    "failed": "失败",
                }
                for task in result["tasks"]:
                    task["task_type"] = task_type_map.get(task.get("task_type"), "")
                    task["execution_status"] = status_map.get(
                        task.get("execution_status"), ""
                    )
                    task["is_active"] = "是" if task.get("is_active") else "否"
                admin_task_table.rows = result["tasks"]

        def toggle_task_handler(task_id, current_active):
            result = AdminService.toggle_task(task_id, not current_active)
            if result["success"]:
                ui.notify(result["message"], type="positive")
                refresh_tasks()
            else:
                ui.notify(result["message"], type="negative")

        def trigger_task_handler(task_id):
            result = AdminService.trigger_task(task_id)
            if result["success"]:
                ui.notify(result["message"], type="positive")
            else:
                ui.notify(result["message"], type="negative")

        def delete_task_handler(task_id):
            result = AdminService.delete_task(task_id)
            if result["success"]:
                ui.notify(result["message"], type="positive")
                refresh_tasks()
            else:
                ui.notify(result["message"], type="negative")

        with ui.row().classes("gap-3 mt-4"):
            ui.button("搜索", on_click=refresh_tasks).classes(
                "bg-blue-600 text-white hover:bg-blue-700"
            )
            ui.button("刷新", on_click=refresh_tasks).classes(
                "bg-gray-200 text-gray-700 hover:bg-gray-300"
            )

        refresh_tasks()
