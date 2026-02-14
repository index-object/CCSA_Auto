from nicegui import ui
from datetime import datetime, timedelta

from ccsa_auto.admin_v2.services.log_service import LogManagementService


def create_logs_page():
    """Create the logs page"""
    # State
    keyword = {"value": ""}
    log_type_filter = {"value": None}
    start_date = {"value": ""}
    end_date = {"value": ""}
    current_page = {"value": 1}
    page_size = {"value": 20}
    logs_data = {"data": [], "total": 0}

    def load_logs():
        """Load logs data"""
        result = LogManagementService.get_logs(
            keyword=keyword["value"] if keyword["value"] else None,
            log_type=log_type_filter["value"],
            start_date=start_date["value"] if start_date["value"] else None,
            end_date=end_date["value"] if end_date["value"] else None,
            page=current_page["value"],
            page_size=page_size["value"],
        )
        if result.get("success"):
            logs_data["data"] = result.get("data", [])
            logs_data["total"] = result.get("total", 0)
        else:
            ui.notify(f"加载日志失败: {result.get('message')}", type="negative")

    def on_search():
        """Handle search"""
        current_page["value"] = 1
        load_logs()

    def on_type_filter(log_type: str):
        """Handle type filter"""
        log_type_filter["value"] = log_type
        current_page["value"] = 1
        load_logs()

    def on_page_change(page: int):
        """Handle page change"""
        current_page["value"] = page
        load_logs()

    def export_logs():
        """Export logs"""
        result = LogManagementService.export_logs(
            log_type=log_type_filter["value"],
            start_date=start_date["value"] if start_date["value"] else None,
            end_date=end_date["value"] if end_date["value"] else None,
        )
        if result.get("success"):
            ui.notify(f"日志导出成功: {result.get('filepath')}", type="positive")
        else:
            ui.notify(f"导出失败: {result.get('message')}", type="negative")

    def set_date_range(days: int):
        """Set quick date range"""
        now = datetime.now()
        end_date["value"] = now.strftime("%Y-%m-%d")
        start_date["value"] = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        on_search()

    # Initial load
    load_logs()

    # Toolbar
    with ui.card().classes("p-4 mb-4"):
        with ui.row().classes("items-center gap-4 w-full flex-wrap"):
            # Search
            with ui.row().classes("items-center gap-2"):
                ui.input(
                    "搜索内容",
                    value=keyword["value"],
                    on_change=lambda e: keyword.update(value=e.value),
                    on_enter=on_search,
                ).props("outlined dense clearable").classes("w-48")
                ui.button("搜索", on_click=on_search).props("flat color=primary")

            # Log type filters
            with ui.row().classes("items-center gap-2"):
                ui.button(
                    "全部",
                    on_click=lambda: on_type_filter(None),
                ).props(
                    f"flat {'color=primary' if log_type_filter['value'] is None else ''}"
                )
                ui.button(
                    "操作",
                    on_click=lambda: on_type_filter("operation"),
                ).props(
                    f"flat {'color=info' if log_type_filter['value'] == 'operation' else ''}"
                )
                ui.button(
                    "任务",
                    on_click=lambda: on_type_filter("task"),
                ).props(
                    f"flat {'color=purple' if log_type_filter['value'] == 'task' else ''}"
                )
                ui.button(
                    "认证",
                    on_click=lambda: on_type_filter("auth"),
                ).props(
                    f"flat {'color=warning' if log_type_filter['value'] == 'auth' else ''}"
                )
                ui.button(
                    "错误",
                    on_click=lambda: on_type_filter("error"),
                ).props(
                    f"flat {'color=negative' if log_type_filter['value'] == 'error' else ''}"
                )

            # Date range
            with ui.row().classes("items-center gap-2"):
                ui.input(
                    "开始日期",
                    value=start_date["value"],
                    on_change=lambda e: start_date.update(value=e.value),
                ).props("outlined dense type=date").classes("w-36")
                ui.input(
                    "结束日期",
                    value=end_date["value"],
                    on_change=lambda e: end_date.update(value=e.value),
                ).props("outlined dense type=date").classes("w-36")

            # Quick date buttons
            with ui.row().classes("items-center gap-1"):
                ui.button(
                    "今天",
                    on_click=lambda: set_date_range(0),
                ).props("flat dense size=sm")
                ui.button(
                    "7天",
                    on_click=lambda: set_date_range(7),
                ).props("flat dense size=sm")
                ui.button(
                    "30天",
                    on_click=lambda: set_date_range(30),
                ).props("flat dense size=sm")

            # Export
            ui.button("导出日志", on_click=export_logs, icon="download").props(
                "flat color=positive"
            )

    # Logs table
    with ui.card().classes("p-4"):
        # Table header
        with ui.row().classes("font-bold border-b pb-2 mb-2"):
            with ui.column().classes("w-16"):
                ui.label("ID")
            with ui.column().classes("w-24"):
                ui.label("类型")
            with ui.column().classes("w-32"):
                ui.label("操作")
            with ui.column().classes("flex-1"):
                ui.label("内容")
            with ui.column().classes("w-20"):
                ui.label("用户")
            with ui.column().classes("w-16"):
                ui.label("状态")
            with ui.column().classes("w-32"):
                ui.label("时间")

        # Table rows
        for log in logs_data["data"]:
            with ui.row().classes("border-b py-2 hover:bg-gray-50 items-center"):
                with ui.column().classes("w-16"):
                    ui.label(str(log.get("id", "")))
                with ui.column().classes("w-24"):
                    log_type = log.get("log_type", "")
                    type_colors = {
                        "operation": "info",
                        "task": "purple",
                        "auth": "warning",
                        "error": "negative",
                        "system": "grey",
                    }
                    ui.badge(log_type, color=type_colors.get(log_type, "grey"))
                with ui.column().classes("w-32"):
                    ui.label(str(log.get("operation", ""))[:15])
                with ui.column().classes("flex-1"):
                    ui.label(str(log.get("content", ""))[:60])
                with ui.column().classes("w-20"):
                    ui.label(str(log.get("user_id") or "-"))
                with ui.column().classes("w-16"):
                    status = log.get("status", "")
                    if status == "success":
                        ui.badge("成功", color="positive")
                    else:
                        ui.badge("失败", color="negative")
                with ui.column().classes("w-32"):
                    created_at = log.get("created_at", "")
                    if created_at and isinstance(created_at, str):
                        ui.label(created_at[:19])
                    else:
                        ui.label("-")

        # Pagination
        total_pages = max(
            1, (logs_data["total"] + page_size["value"] - 1) // page_size["value"]
        )
        with ui.row().classes("items-center justify-between w-full mt-4"):
            with ui.row().classes("items-center gap-2"):
                ui.label(f"共 {logs_data['total']} 条").classes("text-sm text-gray-500")

            pagination = ui.pagination(
                current_page["value"],
                1,
                total_pages,
                on_change=lambda e: on_page_change(e.value),
            )
            pagination.props("boundary-links")


def render():
    """Render the logs page"""
    create_logs_page()
