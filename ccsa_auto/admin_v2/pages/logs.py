from nicegui import ui
from datetime import datetime, timedelta

from ccsa_auto.admin_v2.services.log_service import LogManagementService


# 任务运行状态 -> (中文文案, 颜色样式)
TASK_RUN_STATUS = {
    "success": ("成功", "bg-green-100 text-green-700"),
    "failed": ("失败", "bg-red-100 text-red-700"),
    "running": ("运行中", "bg-blue-100 text-blue-700"),
    "skipped": ("跳过", "bg-gray-100 text-gray-600"),
}

# 触发方式中文映射
TASK_TRIGGER_LABELS = {
    "schedule": "定时",
    "manual": "手动",
    "batch": "批量",
    "fixer": "修复",
}

# 任务类型中文映射
TASK_TYPE_LABELS = {
    "daily": "每日",
    "weekly": "每周",
    "monthly": "每月",
}


def create_logs_page():
    """Create the logs page"""
    # ---------------- 操作日志状态 ----------------
    keyword = {"value": ""}
    log_type_filter = {"value": None}
    start_date = {"value": ""}
    end_date = {"value": ""}
    current_page = {"value": 1}
    page_size = {"value": 20}
    logs_data = {"data": [], "total": 0}

    # ---------------- 任务运行状态 ----------------
    tr_task_id = {"value": ""}
    tr_user_id = {"value": ""}
    tr_status_filter = {"value": None}
    tr_task_type_filter = {"value": None}
    tr_start_date = {"value": ""}
    tr_end_date = {"value": ""}
    tr_current_page = {"value": 1}
    tr_page_size = {"value": 20}
    task_runs_data = {"data": [], "total": 0}
    task_stats = {"value": {}}

    # ------------------------------------------------------------------
    # 操作日志
    # ------------------------------------------------------------------
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
        operation_view.refresh()

    def on_type_filter(log_type: str):
        """Handle type filter"""
        log_type_filter["value"] = log_type
        current_page["value"] = 1
        operation_view.refresh()

    def on_page_change(page: int):
        """Handle page change"""
        current_page["value"] = page
        operation_view.refresh()

    def export_logs():
        """Export logs"""
        result = LogManagementService.export_logs(
            log_type=log_type_filter["value"],
            start_date=start_date["value"] if start_date["value"] else None,
            end_date=end_date["value"] if end_date["value"] else None,
            keyword=keyword["value"] if keyword["value"] else None,
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

    @ui.refreshable
    def operation_view():
        """操作日志视图（工具栏 + 表格 + 分页）"""
        load_logs()

        # Toolbar
        with ui.card().classes("p-4 mb-4 w-full"):
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
                        "访问",
                        on_click=lambda: on_type_filter("access"),
                    ).props(
                        f"flat {'color=cyan' if log_type_filter['value'] == 'access' else ''}"
                    )
                    ui.button(
                        "系统",
                        on_click=lambda: on_type_filter("system"),
                    ).props(
                        f"flat {'color=grey' if log_type_filter['value'] == 'system' else ''}"
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

        with ui.card().classes(
            "rounded-2xl p-6 shadow-sm bg-white flex flex-col w-full"
        ):
            with ui.row().classes(
                "grid grid-cols-7 gap-4 pb-4 border-b border-gray-100 mb-4 shrink-0"
            ):
                ui.label("ID").classes("text-xs font-semibold text-[#6b7280] uppercase")
                ui.label("类型").classes(
                    "text-xs font-semibold text-[#6b7280] uppercase"
                )
                ui.label("操作").classes(
                    "text-xs font-semibold text-[#6b7280] uppercase"
                )
                ui.label("内容").classes(
                    "text-xs font-semibold text-[#6b7280] uppercase"
                )
                ui.label("用户").classes(
                    "text-xs font-semibold text-[#6b7280] uppercase"
                )
                ui.label("状态").classes(
                    "text-xs font-semibold text-[#6b7280] uppercase"
                )
                ui.label("时间").classes(
                    "text-xs font-semibold text-[#6b7280] uppercase"
                )

            with ui.element("div").classes(
                "overflow-y-auto max-h-[calc(100vh-380px)]"
            ):
                for idx, log in enumerate(logs_data["data"]):
                    row_bg = "bg-[#f9fafb]" if idx % 2 == 1 else "bg-white"
                    with ui.row().classes(
                        f"grid grid-cols-7 gap-4 py-4 {row_bg} items-center"
                    ):
                        ui.label(str(log.get("id", ""))).classes(
                            "text-sm text-[#1f2937]"
                        )

                        log_type = log.get("log_type", "")
                        type_colors = {
                            "operation": ("bg-blue-100", "text-blue-700"),
                            "task": ("bg-purple-100", "text-purple-700"),
                            "auth": ("bg-amber-100", "text-amber-700"),
                            "access": ("bg-cyan-100", "text-cyan-700"),
                            "system": ("bg-gray-100", "text-gray-600"),
                            "error": ("bg-red-100", "text-red-700"),
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
                            ui.label(created_at[:19]).classes(
                                "text-sm text-[#6b7280]"
                            )
                        else:
                            ui.label("-").classes("text-sm text-[#6b7280]")

            # Pagination
            total_pages = max(
                1,
                (logs_data["total"] + page_size["value"] - 1) // page_size["value"],
            )
            with ui.row().classes("items-center justify-between w-full mt-4"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(f"共 {logs_data['total']} 条").classes(
                        "text-sm text-gray-500"
                    )

                with ui.row().classes("items-center gap-2"):
                    ui.button("首页", on_click=lambda: on_page_change(1)).props("flat")
                    ui.button(
                        "上一页",
                        on_click=lambda: on_page_change(
                            max(1, current_page["value"] - 1)
                        ),
                    ).props("flat")
                    ui.label(f"{current_page['value']} / {total_pages}").classes("px-3")
                    ui.button(
                        "下一页",
                        on_click=lambda: on_page_change(
                            min(total_pages, current_page["value"] + 1)
                        ),
                    ).props("flat")
                    ui.button(
                        "末页", on_click=lambda: on_page_change(total_pages)
                    ).props("flat")

    # ------------------------------------------------------------------
    # 任务运行
    # ------------------------------------------------------------------
    def _parse_optional_int(value):
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def load_task_runs():
        """加载任务运行记录"""
        result = LogManagementService.get_task_runs(
            task_id=_parse_optional_int(tr_task_id["value"]),
            user_id=_parse_optional_int(tr_user_id["value"]),
            status=tr_status_filter["value"],
            task_type=tr_task_type_filter["value"],
            start_date=tr_start_date["value"] if tr_start_date["value"] else None,
            end_date=tr_end_date["value"] if tr_end_date["value"] else None,
            page=tr_current_page["value"],
            page_size=tr_page_size["value"],
        )
        if result.get("success"):
            task_runs_data["data"] = result.get("data", [])
            task_runs_data["total"] = result.get("total", 0)
        else:
            ui.notify(f"加载任务运行失败: {result.get('message')}", type="negative")

    def load_task_stats():
        """加载最近 7 天任务运行统计"""
        result = LogManagementService.get_task_run_statistics(7)
        if result.get("success"):
            task_stats["value"] = result
        else:
            task_stats["value"] = {}
            ui.notify(f"加载任务统计失败: {result.get('message')}", type="negative")

    def on_task_search():
        tr_current_page["value"] = 1
        task_run_view.refresh()

    def on_task_status_filter(status):
        tr_status_filter["value"] = status
        tr_current_page["value"] = 1
        task_run_view.refresh()

    def on_task_type_filter(task_type):
        tr_task_type_filter["value"] = task_type
        tr_current_page["value"] = 1
        task_run_view.refresh()

    def on_task_page_change(page: int):
        tr_current_page["value"] = page
        task_run_view.refresh()

    def set_task_date_range(days: int):
        now = datetime.now()
        tr_end_date["value"] = now.strftime("%Y-%m-%d")
        tr_start_date["value"] = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        on_task_search()

    def _format_duration(duration_ms):
        if duration_ms is None:
            return "-"
        try:
            return f"{float(duration_ms) / 1000:.2f}s"
        except (TypeError, ValueError):
            return "-"

    def _format_score(run):
        score = run.get("score")
        max_score = run.get("max_score")
        if score is None or max_score is None:
            return "-"
        return f"{score}/{max_score}"

    def _format_task_name(run):
        name = run.get("task_name")
        if name:
            return str(name)
        task_id = run.get("task_id")
        if task_id is None:
            return "-"
        return f"task_{task_id}"

    @ui.refreshable
    def task_run_view():
        """任务运行视图（统计 + 工具栏 + 表格 + 分页）"""
        load_task_stats()
        load_task_runs()

        stats = task_stats["value"]
        total = stats.get("total")
        success = stats.get("success")
        failed = stats.get("failed")
        success_rate = stats.get("success_rate")
        avg_duration = stats.get("avg_duration_ms")
        rate_text = f"{success_rate}%" if success_rate is not None else "-"
        avg_text = f"{avg_duration} ms" if avg_duration is not None else "-"

        with ui.card().classes("p-4 mb-4 w-full"):
            ui.label(
                f"最近7天: 共 {total if total is not None else '-'} 次, "
                f"成功 {success if success is not None else '-'}, "
                f"失败 {failed if failed is not None else '-'}, "
                f"成功率 {rate_text}, 平均耗时 {avg_text}"
            ).classes("text-sm text-[#374151] mb-3")

            # Toolbar
            with ui.row().classes("items-center gap-4 w-full flex-wrap"):
                # Task / user id search
                with ui.row().classes("items-center gap-2"):
                    ui.input(
                        "任务ID",
                        value=tr_task_id["value"],
                        on_change=lambda e: tr_task_id.update(value=e.value),
                    ).props("outlined dense clearable type=number").classes(
                        "w-32"
                    ).on("keydown.enter", on_task_search)
                    ui.input(
                        "用户ID",
                        value=tr_user_id["value"],
                        on_change=lambda e: tr_user_id.update(value=e.value),
                    ).props("outlined dense clearable type=number").classes(
                        "w-32"
                    ).on("keydown.enter", on_task_search)
                    ui.button("搜索", on_click=on_task_search).props(
                        "flat color=primary"
                    )

                # Status filters
                with ui.row().classes("items-center gap-2"):
                    ui.button(
                        "全部",
                        on_click=lambda: on_task_status_filter(None),
                    ).props(
                        f"flat {'color=primary' if tr_status_filter['value'] is None else ''}"
                    )
                    ui.button(
                        "成功",
                        on_click=lambda: on_task_status_filter("success"),
                    ).props(
                        f"flat {'color=positive' if tr_status_filter['value'] == 'success' else ''}"
                    )
                    ui.button(
                        "失败",
                        on_click=lambda: on_task_status_filter("failed"),
                    ).props(
                        f"flat {'color=negative' if tr_status_filter['value'] == 'failed' else ''}"
                    )
                    ui.button(
                        "运行中",
                        on_click=lambda: on_task_status_filter("running"),
                    ).props(
                        f"flat {'color=info' if tr_status_filter['value'] == 'running' else ''}"
                    )

                # Task type filters
                with ui.row().classes("items-center gap-2"):
                    ui.button(
                        "全部",
                        on_click=lambda: on_task_type_filter(None),
                    ).props(
                        f"flat {'color=primary' if tr_task_type_filter['value'] is None else ''}"
                    )
                    ui.button(
                        "每日",
                        on_click=lambda: on_task_type_filter("daily"),
                    ).props(
                        f"flat {'color=purple' if tr_task_type_filter['value'] == 'daily' else ''}"
                    )
                    ui.button(
                        "每周",
                        on_click=lambda: on_task_type_filter("weekly"),
                    ).props(
                        f"flat {'color=purple' if tr_task_type_filter['value'] == 'weekly' else ''}"
                    )
                    ui.button(
                        "每月",
                        on_click=lambda: on_task_type_filter("monthly"),
                    ).props(
                        f"flat {'color=purple' if tr_task_type_filter['value'] == 'monthly' else ''}"
                    )

                # Date range
                with ui.row().classes("items-center gap-2"):
                    ui.input(
                        "开始日期",
                        value=tr_start_date["value"],
                        on_change=lambda e: tr_start_date.update(value=e.value),
                    ).props("outlined dense type=date").classes("w-36")
                    ui.input(
                        "结束日期",
                        value=tr_end_date["value"],
                        on_change=lambda e: tr_end_date.update(value=e.value),
                    ).props("outlined dense type=date").classes("w-36")

                # Quick date buttons
                with ui.row().classes("items-center gap-1"):
                    ui.button(
                        "今天",
                        on_click=lambda: set_task_date_range(0),
                    ).props("flat dense size=sm")
                    ui.button(
                        "7天",
                        on_click=lambda: set_task_date_range(7),
                    ).props("flat dense size=sm")
                    ui.button(
                        "30天",
                        on_click=lambda: set_task_date_range(30),
                    ).props("flat dense size=sm")

        with ui.card().classes(
            "rounded-2xl p-6 shadow-sm bg-white flex flex-col w-full"
        ):
            with ui.row().classes(
                "grid grid-cols-10 gap-4 pb-4 border-b border-gray-100 mb-4 shrink-0"
            ):
                for title in (
                    "ID",
                    "任务",
                    "用户ID",
                    "类型",
                    "状态",
                    "耗时",
                    "得分",
                    "触发方式",
                    "开始时间",
                    "结果/消息",
                ):
                    ui.label(title).classes(
                        "text-xs font-semibold text-[#6b7280] uppercase"
                    )

            with ui.element("div").classes(
                "overflow-y-auto max-h-[calc(100vh-420px)]"
            ):
                for idx, run in enumerate(task_runs_data["data"]):
                    row_bg = "bg-[#f9fafb]" if idx % 2 == 1 else "bg-white"
                    with ui.row().classes(
                        f"grid grid-cols-10 gap-4 py-4 {row_bg} items-center"
                    ):
                        ui.label(str(run.get("id", ""))).classes(
                            "text-sm text-[#1f2937]"
                        )
                        ui.label(_format_task_name(run)[:20]).classes(
                            "text-sm text-[#1f2937]"
                        )
                        user_id = run.get("user_id")
                        ui.label(
                            str(user_id) if user_id is not None else "-"
                        ).classes("text-sm text-[#6b7280]")

                        task_type = run.get("task_type", "")
                        with ui.element("span").classes(
                            "inline-flex items-center px-2.5 py-0.5 rounded-full "
                            "text-xs font-medium bg-purple-100 text-purple-700 w-fit"
                        ):
                            ui.label(
                                TASK_TYPE_LABELS.get(task_type, str(task_type))
                            )

                        status = run.get("status", "")
                        status_label, status_color = TASK_RUN_STATUS.get(
                            status, (str(status), "bg-gray-100 text-gray-600")
                        )
                        with ui.element("span").classes(
                            f"inline-flex items-center px-2.5 py-0.5 rounded-full "
                            f"text-xs font-medium {status_color} w-fit"
                        ):
                            ui.label(status_label)

                        ui.label(_format_duration(run.get("duration_ms"))).classes(
                            "text-sm text-[#6b7280]"
                        )
                        ui.label(_format_score(run)).classes("text-sm text-[#6b7280]")

                        trigger = run.get("trigger", "")
                        ui.label(
                            TASK_TRIGGER_LABELS.get(trigger, str(trigger))
                        ).classes("text-sm text-[#6b7280]")

                        started_at = run.get("started_at")
                        if started_at:
                            ui.label(str(started_at)[:19]).classes(
                                "text-sm text-[#6b7280]"
                            )
                        else:
                            ui.label("-").classes("text-sm text-[#6b7280]")

                        message = run.get("message")
                        ui.label(str(message)[:40] if message else "-").classes(
                            "text-sm text-[#6b7280]"
                        )

            # Pagination
            total_pages = max(
                1,
                (task_runs_data["total"] + tr_page_size["value"] - 1)
                // tr_page_size["value"],
            )
            with ui.row().classes("items-center justify-between w-full mt-4"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(f"共 {task_runs_data['total']} 条").classes(
                        "text-sm text-gray-500"
                    )

                with ui.row().classes("items-center gap-2"):
                    ui.button("首页", on_click=lambda: on_task_page_change(1)).props(
                        "flat"
                    )
                    ui.button(
                        "上一页",
                        on_click=lambda: on_task_page_change(
                            max(1, tr_current_page["value"] - 1)
                        ),
                    ).props("flat")
                    ui.label(f"{tr_current_page['value']} / {total_pages}").classes(
                        "px-3"
                    )
                    ui.button(
                        "下一页",
                        on_click=lambda: on_task_page_change(
                            min(total_pages, tr_current_page["value"] + 1)
                        ),
                    ).props("flat")
                    ui.button(
                        "末页",
                        on_click=lambda: on_task_page_change(total_pages),
                    ).props("flat")

    # ------------------------------------------------------------------
    # 视图切换
    # ------------------------------------------------------------------
    with ui.tabs().classes("w-full") as view_tabs:
        operation_tab = ui.tab("操作日志")
        task_run_tab = ui.tab("任务运行")

    with ui.tab_panels(view_tabs, value=operation_tab).classes(
        "w-full bg-transparent p-0"
    ):
        with ui.tab_panel(operation_tab).classes("p-0"):
            operation_view()
        with ui.tab_panel(task_run_tab).classes("p-0"):
            task_run_view()


def render():
    """Render the logs page"""
    create_logs_page()
