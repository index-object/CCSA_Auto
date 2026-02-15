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
                ).props("outlined dense clearable").classes("w-48").on(
                    "keydown.enter", on_search
                )
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

    with ui.card().classes("rounded-2xl p-6 shadow-sm bg-white flex flex-col"):
        with ui.row().classes(
            "grid grid-cols-7 gap-4 pb-4 border-b border-gray-100 mb-4 shrink-0"
        ):
            ui.label("ID").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("类型").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("操作").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("内容").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("用户").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("状态").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("时间").classes("text-xs font-semibold text-[#6b7280] uppercase")

        with ui.element("div").classes("overflow-y-auto max-h-[calc(100vh-380px)]"):
            for idx, log in enumerate(logs_data["data"]):
                row_bg = "bg-[#f9fafb]" if idx % 2 == 1 else "bg-white"
                with ui.row().classes(
                    f"grid grid-cols-7 gap-4 py-4 {row_bg} items-center"
                ):
                    ui.label(str(log.get("id", ""))).classes("text-sm text-[#1f2937]")

                    log_type = log.get("log_type", "")
                    type_colors = {
                        "operation": ("bg-blue-100", "text-blue-700"),
                        "task": ("bg-purple-100", "text-purple-700"),
                        "auth": ("bg-amber-100", "text-amber-700"),
                        "error": ("bg-red-100", "text-red-700"),
                        "system": ("bg-gray-100", "text-gray-600"),
                    }
                    bg_color, text_color = type_colors.get(
                        log_type, ("bg-gray-100", "text-gray-600")
                    )
                    with ui.element("span").classes(
                        f"inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {bg_color} {text_color} w-fit"
                    ):
                        ui.label(log_type)

                    ui.label(str(log.get("operation", ""))[:15]).classes(
                        "text-sm text-[#1f2937]"
                    )
                    ui.label(str(log.get("content", ""))[:60]).classes(
                        "text-sm text-[#6b7280]"
                    )
                    ui.label(str(log.get("user_id") or "-")).classes(
                        "text-sm text-[#6b7280]"
                    )

                    status = log.get("status", "")
                    if status == "success":
                        with ui.element("span").classes(
                            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 w-fit"
                        ):
                            ui.label("成功")
                    else:
                        with ui.element("span").classes(
                            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 w-fit"
                        ):
                            ui.label("失败")

                    created_at = log.get("created_at", "")
                    if created_at and isinstance(created_at, str):
                        ui.label(created_at[:19]).classes("text-sm text-[#6b7280]")
                    else:
                        ui.label("-").classes("text-sm text-[#6b7280]")

        # Pagination
        total_pages = max(
            1, (logs_data["total"] + page_size["value"] - 1) // page_size["value"]
        )
        with ui.row().classes("items-center justify-between w-full mt-4"):
            with ui.row().classes("items-center gap-2"):
                ui.label(f"共 {logs_data['total']} 条").classes("text-sm text-gray-500")

            total_pages = max(1, (logs_data["total"] + 19) // 20)
            with ui.row().classes("items-center gap-2"):
                ui.button("首页", on_click=lambda: on_page_change(1)).props("flat")
                ui.button(
                    "上一页",
                    on_click=lambda: on_page_change(max(1, current_page["value"] - 1)),
                ).props("flat")
                ui.label(f"{current_page['value']} / {total_pages}").classes("px-3")
                ui.button(
                    "下一页",
                    on_click=lambda: on_page_change(
                        min(total_pages, current_page["value"] + 1)
                    ),
                ).props("flat")
                ui.button("末页", on_click=lambda: on_page_change(total_pages)).props(
                    "flat"
                )


def render():
    """Render the logs page"""
    create_logs_page()
