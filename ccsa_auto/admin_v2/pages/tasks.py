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
    selected_ids = {"value": []}
    is_executing = {"value": False}

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
        task_table.refresh()

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

    def on_select_all(checked: bool):
        """全选/取消全选当前页"""
        if checked:
            for task in tasks_data["data"]:
                tid = task["id"]
                if tid not in selected_ids["value"]:
                    selected_ids["value"] = selected_ids["value"] + [tid]
        else:
            page_ids = {task["id"] for task in tasks_data["data"]}
            selected_ids["value"] = [tid for tid in selected_ids["value"] if tid not in page_ids]
        task_table.refresh()

    def on_select_task(task_id: int, checked: bool):
        """勾选/取消勾选单个任务"""
        if checked:
            if task_id not in selected_ids["value"]:
                selected_ids["value"] = selected_ids["value"] + [task_id]
        else:
            selected_ids["value"] = [tid for tid in selected_ids["value"] if tid != task_id]
        task_table.refresh()

    def on_batch_execute():
        """批量执行选中任务"""
        ids = list(selected_ids["value"])
        if not ids:
            ui.notify("请先选择要执行的任务", type="warning")
            return
        batch_btn.props("disabled")
        is_executing["value"] = True
        try:
            result = TaskManagementService.batch_execute_tasks(ids)
            selected_ids["value"] = []
            load_tasks()
            if result.get("success"):
                ui.notify(result.get("message", "批量执行完成"), type="positive")
            else:
                failed = result.get("failed_count", 0)
                if failed > 0:
                    ui.notify(result.get("message", "批量执行完成"), type="warning")
                else:
                    ui.notify(result.get("message", "批量执行完成"), type="positive")
        except Exception as e:
            ui.notify(f"批量执行失败: {str(e)}", type="negative")
        finally:
            batch_btn.props(remove="disabled")
            is_executing["value"] = False

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
                ).props("outlined dense clearable").classes("w-64").on(
                    "keydown.enter", on_search
                )
                ui.button("搜索", on_click=on_search).props("flat color=primary")

            # Task type filters
            with ui.row().classes("items-center gap-2"):
                ui.button(
                    "全部",
                    on_click=lambda: on_task_type_filter(None),
                ).props(
                    f"flat {'color=primary' if task_type_filter['value'] is None else ''}"
                )
                ui.button(
                    "每日",
                    on_click=lambda: on_task_type_filter("daily"),
                ).props(
                    f"flat {'color=info' if task_type_filter['value'] == 'daily' else ''}"
                )
                ui.button(
                    "每周",
                    on_click=lambda: on_task_type_filter("weekly"),
                ).props(
                    f"flat {'color=purple' if task_type_filter['value'] == 'weekly' else ''}"
                )
                ui.button(
                    "每月",
                    on_click=lambda: on_task_type_filter("monthly"),
                ).props(
                    f"flat {'color=warning' if task_type_filter['value'] == 'monthly' else ''}"
                )

            # Status filters
            with ui.row().classes("items-center gap-2"):
                ui.button(
                    "全部",
                    on_click=lambda: on_status_filter(None),
                ).props(
                    f"flat {'color=primary' if status_filter['value'] is None else ''}"
                )
                ui.button(
                    "待执行",
                    on_click=lambda: on_status_filter("pending"),
                ).props(
                    f"flat {'color=grey' if status_filter['value'] == 'pending' else ''}"
                )
                ui.button(
                    "执行中",
                    on_click=lambda: on_status_filter("running"),
                ).props(
                    f"flat {'color=warning' if status_filter['value'] == 'running' else ''}"
                )
                ui.button(
                    "已完成",
                    on_click=lambda: on_status_filter("completed"),
                ).props(
                    f"flat {'color=positive' if status_filter['value'] == 'completed' else ''}"
                )
                ui.button(
                    "失败",
                    on_click=lambda: on_status_filter("failed"),
                ).props(
                    f"flat {'color=negative' if status_filter['value'] == 'failed' else ''}"
                )

            # Batch execute
            with ui.row().classes("items-center gap-2 ml-auto"):
                batch_btn = ui.button(
                    "批量执行",
                    icon="playlist_play",
                    on_click=on_batch_execute,
                ).props("color=primary")

    @ui.refreshable
    def task_table():
        """渲染任务表格"""
        with ui.card().classes("rounded-2xl p-6 shadow-sm bg-white flex flex-col"):
            with ui.row().classes(
                "grid grid-cols-10 gap-4 pb-4 border-b border-gray-100 mb-4 shrink-0"
            ):
                with ui.element("div").classes("flex items-center"):
                    all_check = ui.checkbox(on_change=lambda e: on_select_all(e.value))
                ui.label("ID").classes("text-xs font-semibold text-[#6b7280] uppercase")
                ui.label("用户").classes("text-xs font-semibold text-[#6b7280] uppercase")
                ui.label("类型").classes("text-xs font-semibold text-[#6b7280] uppercase")
                ui.label("任务名称").classes(
                    "text-xs font-semibold text-[#6b7280] uppercase"
                )
                ui.label("启用").classes("text-xs font-semibold text-[#6b7280] uppercase")
                ui.label("执行状态").classes(
                    "text-xs font-semibold text-[#6b7280] uppercase"
                )
                ui.label("外部状态").classes(
                    "text-xs font-semibold text-[#6b7280] uppercase"
                )
                ui.label("下次运行").classes(
                    "text-xs font-semibold text-[#6b7280] uppercase"
                )
                ui.label("操作").classes("text-xs font-semibold text-[#6b7280] uppercase")

            with ui.element("div").classes("overflow-y-auto max-h-[calc(100vh-380px)]"):
                for idx, task in enumerate(tasks_data["data"]):
                    row_bg = "bg-[#f9fafb]" if idx % 2 == 1 else "bg-white"
                    with ui.row().classes(
                        f"grid grid-cols-10 gap-4 py-4 {row_bg} items-center"
                    ):
                        with ui.element("div").classes("flex items-center"):
                            ui.checkbox(
                                value=task.get("id") in selected_ids["value"],
                                on_change=lambda e, tid=task.get("id"): on_select_task(tid, e.value),
                            )
                        ui.label(str(task.get("id", ""))).classes("text-sm text-[#1f2937]")
                        ui.label(str(task.get("username", ""))[:10]).classes(
                            "text-sm text-[#1f2937]"
                        )

                        task_type = task.get("task_type", "")
                        type_badge = {
                            "daily": "每日",
                            "weekly": "每周",
                            "monthly": "每月",
                        }.get(task_type, task_type)
                        with ui.element("div"):
                            if task_type == "daily":
                                with ui.element("span").classes(
                                    "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700 w-fit"
                                ):
                                    ui.label(type_badge)
                            elif task_type == "weekly":
                                with ui.element("span").classes(
                                    "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 w-fit"
                                ):
                                    ui.label(type_badge)
                            elif task_type == "monthly":
                                with ui.element("span").classes(
                                    "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700 w-fit"
                                ):
                                    ui.label(type_badge)
                            else:
                                ui.label(type_badge).classes("text-sm text-[#6b7280]")

                        ui.label(str(task.get("task_name") or "-")).classes(
                            "text-sm text-[#1f2937]"
                        )

                        if task.get("is_active"):
                            with ui.element("span").classes(
                                "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 w-fit"
                            ):
                                ui.label("启用")
                        else:
                            with ui.element("span").classes(
                                "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 w-fit"
                            ):
                                ui.label("禁用")

                        status = task.get("execution_status", "")
                        status_colors_bg = {
                            "pending": "bg-gray-100 text-gray-600",
                            "running": "bg-amber-100 text-amber-700",
                            "completed": "bg-green-100 text-green-700",
                            "failed": "bg-red-100 text-red-700",
                        }
                        status_labels = {
                            "pending": "待执行",
                            "running": "执行中",
                            "completed": "已完成",
                            "failed": "失败",
                        }
                        badge_class = status_colors_bg.get(
                            status, "bg-gray-100 text-gray-600"
                        )
                        with ui.element("span").classes(
                            f"inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {badge_class} w-fit"
                        ):
                            ui.label(status_labels.get(status, status))

                        ext_status = task.get("external_status", "")
                        ext_colors = {
                            "success": ("bg-green-100", "text-green-700"),
                            "failed": ("bg-red-100", "text-red-700"),
                            "unknown": ("bg-gray-100", "text-gray-600"),
                        }
                        ext_bg, ext_text = ext_colors.get(
                            ext_status, ("bg-gray-100", "text-gray-600")
                        )
                        with ui.element("span").classes(
                            f"inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {ext_bg} {ext_text} w-fit"
                        ):
                            ui.label(ext_status)

                        ui.label(str(task.get("next_run_time") or "-")).classes(
                            "text-sm text-[#6b7280]"
                        )

                        with ui.row().classes("items-center gap-1"):
                            task_id = task.get("id")
                            is_active = task.get("is_active")

                            trigger_btn = (
                                ui.button()
                                .classes(
                                    "text-[#6b7280] hover:text-blue-500 hover:bg-blue-50 rounded p-1 transition-colors"
                                )
                                .props("flat dense")
                            )
                            trigger_btn.on_click(lambda _, tid=task_id: trigger_task(tid))
                            with trigger_btn:
                                ui.icon("play_arrow").classes("text-base")

                            toggle_text = "禁用" if is_active else "启用"
                            toggle_btn = (
                                ui.button()
                                .classes(
                                    "text-[#6b7280] hover:text-amber-500 hover:bg-amber-50 rounded p-1 transition-colors"
                                )
                                .props("flat dense")
                            )
                            toggle_btn.on_click(
                                lambda _, tid=task_id, st=is_active: toggle_task_status(
                                    tid, st
                                )
                            )
                            with toggle_btn:
                                toggle_icon = "toggle_on" if is_active else "toggle_off"
                                ui.icon(toggle_icon).classes("text-base")

                            delete_btn = (
                                ui.button()
                                .classes(
                                    "text-[#6b7280] hover:text-red-500 hover:bg-red-50 rounded p-1 transition-colors"
                                )
                                .props("flat dense")
                            )
                            delete_btn.on_click(lambda _, tid=task_id: delete_task(tid))
                            with delete_btn:
                                ui.icon("delete").classes("text-base")

            # Pagination
            total_pages = max(
                1, (tasks_data["total"] + page_size["value"] - 1) // page_size["value"]
            )
            with ui.row().classes("items-center justify-between w-full mt-4"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(f"共 {tasks_data['total']} 条").classes(
                        "text-sm text-gray-500"
                    )

                total_pages = max(1, (tasks_data["total"] + 19) // 20)
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

    # 初始渲染表格
    task_table()


def render():
    """Render the tasks page"""
    create_tasks_page()
