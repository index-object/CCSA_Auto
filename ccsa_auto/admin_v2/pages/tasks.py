from nicegui import ui
from typing import Optional

from ccsa_auto.admin_v2.services.task_service import TaskManagementService
from ccsa_auto.admin_v2.stores.admin_store import AdminStore


def create_tasks_page():
    """Create the tasks management page"""
    # State
    keyword = {"value": ""}
    task_type_filter = {"value": None}
    status_filter = {"value": None}
    current_page = {"value": 1}
    page_size = {"value": 20}
    tasks_data = {"data": [], "total": 0}

    def load_tasks():
        """Load tasks data"""
        result = TaskManagementService.get_tasks(
            keyword=keyword["value"] if keyword["value"] else None,
            task_type=task_type_filter["value"],
            execution_status=status_filter["value"],
            page=current_page["value"],
            page_size=page_size["value"],
        )
        if result.get("success"):
            tasks_data["data"] = result.get("data", [])
            tasks_data["total"] = result.get("total", 0)
        else:
            ui.notify(f"加载任务失败: {result.get('message')}", type="negative")

    def on_search():
        """Handle search"""
        current_page["value"] = 1
        load_tasks()

    def on_task_type_filter(task_type: Optional[str]):
        """Handle task type filter"""
        task_type_filter["value"] = task_type
        current_page["value"] = 1
        load_tasks()

    def on_status_filter(status: Optional[str]):
        """Handle execution status filter"""
        status_filter["value"] = status
        current_page["value"] = 1
        load_tasks()

    def on_page_change(page: int):
        """Handle page change"""
        current_page["value"] = page
        load_tasks()

    def toggle_task_status(task_id: int, current_status: bool):
        """Toggle task active status"""
        result = TaskManagementService.toggle_task(task_id)
        if result.get("success"):
            ui.notify(result.get("message"), type="positive")
            load_tasks()
        else:
            ui.notify(f"操作失败: {result.get('message')}", type="negative")

    def trigger_task(task_id: int):
        """Manually trigger a task"""
        result = TaskManagementService.trigger_task(task_id)
        if result.get("success"):
            ui.notify(result.get("message"), type="positive")
        else:
            ui.notify(f"触发失败: {result.get('message')}", type="negative")

    def delete_task(task_id: int):
        """Delete a task"""
        result = TaskManagementService.delete_task(task_id)
        if result.get("success"):
            ui.notify("任务删除成功", type="positive")
            load_tasks()
        else:
            ui.notify(f"删除失败: {result.get('message')}", type="negative")

    def render_task_type_badge(task_type: str) -> str:
        """Render task type badge with color"""
        colors = {
            "daily": "color=info",
            "weekly": "color=purple",
            "monthly": "color=warning",
        }
        return colors.get(task_type, "")

    # Initial load
    load_tasks()

    # Toolbar
    with ui.card().classes("p-4 mb-4"):
        with ui.row().classes("items-center gap-4 w-full"):
            # Search
            with ui.row().classes("items-center gap-2 flex-1"):
                ui.input(
                    "搜索任务名称",
                    value=keyword["value"],
                    on_change=lambda e: keyword.update(value=e.value),
                    on_enter=on_search,
                ).props("outlined dense clearable").classes("w-64")
                ui.button("搜索", on_click=on_search).props("flat color=primary")

            # Task type filters
            with ui.row().classes("items-center gap-2"):
                ui.button(
                    "全部",
                    on_click=lambda: on_task_type_filter(None),
                ).props(f"flat {'color=primary' if task_type_filter['value'] is None else ''}")
                ui.button(
                    "每日",
                    on_click=lambda: on_task_type_filter("daily"),
                ).props(f"flat {'color=info' if task_type_filter['value'] == 'daily' else ''}")
                ui.button(
                    "每周",
                    on_click=lambda: on_task_type_filter("weekly"),
                ).props(f"flat {'color=purple' if task_type_filter['value'] == 'weekly' else ''}")
                ui.button(
                    "每月",
                    on_click=lambda: on_task_type_filter("monthly"),
                ).props(f"flat {'color=warning' if task_type_filter['value'] == 'monthly' else ''}")

            # Status filters
            with ui.row().classes("items-center gap-2"):
                ui.button(
                    "全部",
                    on_click=lambda: on_status_filter(None),
                ).props(f"flat {'color=primary' if status_filter['value'] is None else ''}")
                ui.button(
                    "待执行",
                    on_click=lambda: on_status_filter("pending"),
                ).props(f"flat {'color=grey' if status_filter['value'] == 'pending' else ''}")
                ui.button(
                    "执行中",
                    on_click=lambda: on_status_filter("running"),
                ).props(f"flat {'color=warning' if status_filter['value'] == 'running' else ''}")
                ui.button(
                    "已完成",
                    on_click=lambda: on_status_filter("completed"),
                ).props(f"flat {'color=positive' if status_filter['value'] == 'completed' else ''}")
                ui.button(
                    "失败",
                    on_click=lambda: on_status_filter("failed"),
                ).props(f"flat {'color=negative' if status_filter['value'] == 'failed' else ''}")

    # Tasks table
    with ui.card().classes("p-4"):
        # Table header
        with ui.row().classes("font-bold border-b pb-2 mb-2"):
            with ui.column().classes("w-16"):
                ui.label("ID")
            with ui.column().classes("w-20"):
                ui.label("用户")
            with ui.column().classes("w-20"):
                ui.label("类型")
            with ui.column().classes("flex-1"):
                ui.label("任务名称")
            with ui.column().classes("w-20"):
                ui.label("启用")
            with ui.column().classes("w-20"):
                ui.label("执行状态")
            with ui.column().classes("w-20"):
                ui.label("外部状态")
            with ui.column().classes("w-32"):
                ui.label("下次运行")
            with ui.column().classes("w-32"):
                ui.label("操作")

        # Table rows
        for task in tasks_data["data"]:
            with ui.row().classes("border-b py-2 hover:bg-gray-50 items-center"):
                with ui.column().classes("w-16"):
                    ui.label(str(task.get("id", "")))
                with ui.column().classes("w-20"):
                    ui.label(str(task.get("username", ""))[:10])
                with ui.column().classes("w-20"):
                    task_type = task.get("task_type", "")
                    type_badge = {
                        "daily": "每日",
                        "weekly": "每周",
                        "monthly": "每月",
                    }.get(task_type, task_type)
                    if task_type == "daily":
                        ui.badge(type_badge, color="info")
                    elif task_type == "weekly":
                        ui.badge(type_badge, color="purple")
                    elif task_type == "monthly":
                        ui.badge(type_badge, color="warning")
                    else:
                        ui.label(type_badge)
                with ui.column().classes("flex-1"):
                    ui.label(str(task.get("task_name") or "-"))
                with ui.column().classes("w-20"):
                    if task.get("is_active"):
                        ui.badge("启用", color="positive")
                    else:
                        ui.badge("禁用", color="grey")
                with ui.column().classes("w-20"):
                    status = task.get("execution_status", "")
                    status_colors = {
                        "pending": "grey",
                        "running": "warning",
                        "completed": "positive",
                        "failed": "negative",
                    }
                    status_labels = {
                        "pending": "待执行",
                        "running": "执行中",
                        "completed": "已完成",
                        "failed": "失败",
                    }
                    ui.badge(status_labels.get(status, status), color=status_colors.get(status, "grey"))
                with ui.column().classes("w-20"):
                    ext_status = task.get("external_status", "")
                    ext_colors = {
                        "success": "positive",
                        "failed": "negative",
                        "unknown": "grey",
                    }
                    ui.badge(ext_status, color=ext_colors.get(ext_status, "grey"))
                with ui.column().classes("w-32"):
                    ui.label(str(task.get("next_run_time") or "-"))
                with ui.column().classes("w-32"):
                    with ui.row().classes("gap-1"):
                        ui.button(
                            "触发",
                            on_click=lambda t=task: trigger_task(t.get("id")),
                            icon="play_arrow"
                        ).props("flat dense size=sm")
                        ui.button(
                            "启用" if not task.get("is_active") else "禁用",
                            on_click=lambda t=task: toggle_task_status(t.get("id"), t.get("is_active")),
                            icon="toggle_on" if task.get("is_active") else "toggle_off"
                        ).props("flat dense size=sm")
                        ui.button(
                            "删除",
                            on_click=lambda t=task: delete_task(t.get("id")),
                            icon="delete"
                        ).props("flat dense size=sm color=negative")

        # Pagination
        total_pages = max(1, (tasks_data["total"] + page_size["value"] - 1) // page_size["value"])
        with ui.row().classes("items-center justify-between w-full mt-4"):
            with ui.row().classes("items-center gap-2"):
                ui.label(f"共 {tasks_data['total']} 条").classes("text-sm text-gray-500")

            with ui.pagination(
                current_page["value"],
                1,
                total_pages,
                on_change=lambda e: on_page_change(e.value),
            ).props("boundary-links")


def render():
    """Render the tasks page"""
    create_tasks_page()
