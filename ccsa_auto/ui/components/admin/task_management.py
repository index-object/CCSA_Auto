from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService
from ccsa_auto.ui.components.admin.common import (
    PageHeader,
    LoadingOverlay,
    ConfirmDialog,
    Toast,
)


def create_task_management():
    """创建任务管理页面"""
    loading = LoadingOverlay("加载任务数据中...")

    header = PageHeader(
        title="任务管理",
        subtitle="管理系统定时任务和执行状态",
        icon="task_alt",
    )
    header.render()

    with ui.row().classes(
        "items-center gap-4 p-5 bg-white rounded-2xl border border-gray-200 "
        "shadow-sm mb-6 flex-wrap"
    ):
        task_keyword = ui.input("搜索用户").classes(
            "flex-1 min-w-[250px] px-4 py-3 bg-gray-50 border border-gray-200 "
            "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 "
            "focus:border-blue-400 transition-all placeholder:text-gray-400 text-gray-700 text-lg"
        )
        task_type_select = ui.select(
            {
                None: "全部类型",
                "daily": "每日一题",
                "weekly": "每周一课",
                "monthly": "每月一考",
            },
            label="任务类型",
            value=None,
        ).classes(
            "w-40 px-4 py-3 bg-gray-50 border border-gray-200 "
            "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-lg"
        )

        search_btn = ui.button("搜索", icon="search").classes(
            "bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 "
            "transition-all duration-200 shadow-lg shadow-blue-200 hover:shadow-blue-300 "
            "font-medium text-lg"
        )
        refresh_btn = ui.button("刷新", icon="refresh").classes(
            "bg-white text-gray-700 px-6 py-3 rounded-xl border-2 border-gray-200 "
            "hover:border-blue-400 hover:text-blue-600 transition-all duration-200 "
            "font-medium text-lg"
        )

    task_table = ui.table(
        columns=[
            {
                "name": "id",
                "label": "ID",
                "field": "id",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "username",
                "label": "用户",
                "field": "username",
                "sortable": True,
            },
            {
                "name": "task_type",
                "label": "任务类型",
                "field": "task_type",
                "sortable": True,
            },
            {
                "name": "is_active",
                "label": "启用",
                "field": "is_active",
                "align": "center",
                "sortable": True,
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
                "sortable": True,
            },
            {"name": "actions", "label": "操作", "field": "actions", "align": "center"},
        ],
        rows=[],
        row_key="id",
    ).classes(
        "w-full bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden"
    )

    with ui.row().classes("gap-5 mb-6 flex-wrap"):
        with ui.card().classes(
            "flex-1 min-w-[240px] p-5 bg-white rounded-2xl border border-gray-200 "
            "shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
        ):
            with ui.row().classes("items-center gap-4"):
                with ui.row().classes(
                    "w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-100 to-blue-200 "
                    "flex items-center justify-center"
                ):
                    ui.icon("pending_actions").classes("w-6 h-6 text-blue-600")
                with ui.column().classes("items-start"):
                    ui.label("待执行").classes(
                        "text-sm font-semibold text-gray-500 uppercase tracking-wide"
                    )
                    ui.label("0").classes(
                        "text-4xl font-bold text-gray-800 mt-1 tracking-tight"
                    )

        with ui.card().classes(
            "flex-1 min-w-[240px] p-5 bg-white rounded-2xl border border-gray-200 "
            "shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
        ):
            with ui.row().classes("items-center gap-4"):
                with ui.row().classes(
                    "w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-100 to-emerald-200 "
                    "flex items-center justify-center"
                ):
                    ui.icon("check_circle").classes("w-6 h-6 text-emerald-600")
                with ui.column().classes("items-start"):
                    ui.label("已完成").classes(
                        "text-sm font-semibold text-gray-500 uppercase tracking-wide"
                    )
                    ui.label("0").classes(
                        "text-4xl font-bold text-gray-800 mt-1 tracking-tight"
                    )

        with ui.card().classes(
            "flex-1 min-w-[240px] p-5 bg-white rounded-2xl border border-gray-200 "
            "shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
        ):
            with ui.row().classes("items-center gap-4"):
                with ui.row().classes(
                    "w-12 h-12 rounded-2xl bg-gradient-to-br from-red-100 to-red-200 "
                    "flex items-center justify-center"
                ):
                    ui.icon("error").classes("w-6 h-6 text-red-600")
                with ui.column().classes("items-start"):
                    ui.label("失败").classes(
                        "text-sm font-semibold text-gray-500 uppercase tracking-wide"
                    )
                    ui.label("0").classes(
                        "text-4xl font-bold text-gray-800 mt-1 tracking-tight"
                    )

    def refresh_tasks():
        loading.show()
        try:
            result = AdminService.get_all_tasks(
                keyword=task_keyword.value or "",
                task_type=task_type_select.value if task_type_select.value else None,
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
                tasks = result["tasks"]
                for task in tasks:
                    task["task_type"] = task_type_map.get(task.get("task_type"), "")
                    task["execution_status"] = status_map.get(
                        task.get("execution_status"), ""
                    )
                    task["is_active"] = "是" if task.get("is_active") else "否"
                task_table.rows = tasks
            else:
                Toast.error(result.get("message", "获取任务列表失败"))
        except Exception as e:
            Toast.error(f"加载失败: {str(e)}")
        finally:
            loading.close()

    def toggle_task_handler(task_id: int, current_active: bool):
        result = AdminService.toggle_task(task_id, not current_active)
        if result["success"]:
            Toast.success(result["message"])
            refresh_tasks()
        else:
            Toast.error(result["message"])

    def trigger_task_handler(task_id: int):
        ConfirmDialog(
            title="手动触发任务",
            message="确定要立即执行此任务吗？",
            confirm_text="执行",
            confirm_color="green",
            on_confirm=lambda: execute_trigger(task_id),
        ).show()

    def execute_trigger(task_id: int):
        result = AdminService.trigger_task(task_id)
        if result["success"]:
            Toast.success(result["message"])
        else:
            Toast.error(result["message"])

    def delete_task_handler(task_id: int):
        ConfirmDialog(
            title="删除任务",
            message="确定要删除此任务吗？此操作不可恢复。",
            confirm_text="删除",
            confirm_color="red",
            on_confirm=lambda: execute_delete(task_id),
        ).show()

    def execute_delete(task_id: int):
        result = AdminService.delete_task(task_id)
        if result["success"]:
            Toast.success(result["message"])
            refresh_tasks()
        else:
            Toast.error(result["message"])

    search_btn.on("click", refresh_tasks)
    refresh_btn.on("click", refresh_tasks)

    refresh_tasks()
