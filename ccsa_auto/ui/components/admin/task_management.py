from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService
from ccsa_auto.ui.components.admin.common import (
    PageHeader,
    LoadingOverlay,
    ConfirmDialog,
    Toast,
)


def create_task_management():
    """创建任务管理页面 - 现代化增强版"""
    loading = LoadingOverlay("加载任务数据中...")

    # 页面标题
    header = PageHeader(
        title="任务管理",
        subtitle="管理系统定时任务和执行状态",
        icon="task_alt",
    )
    header.render()

    # 筛选工具栏
    with ui.row().classes(
        "items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 "
        "shadow-sm mb-4 flex-wrap"
    ):
        task_keyword = ui.input("搜索用户").classes(
            "w-64 px-4 py-2.5 bg-gray-50 border border-gray-200 "
            "rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 "
            "focus:border-blue-400 transition-all"
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
            "w-36 px-4 py-2.5 bg-gray-50 border border-gray-200 "
            "rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        )

        search_btn = ui.button("搜索").classes(
            "bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        )
        refresh_btn = ui.button("刷新").classes(
            "bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors"
        )

    # 任务表格
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
        "w-full bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden"
    )

    # 任务统计卡片
    with ui.row().classes("gap-4 mb-4 flex-wrap"):
        with ui.card().classes(
            "p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200"
        ):
            with ui.row().classes("items-center gap-3"):
                ui.icon("pending_actions").classes("w-10 h-10 text-blue-500")
                with ui.column().classes("items-start"):
                    ui.label("待执行").classes("text-sm text-blue-600 font-medium")
                    ui.label("0").classes("text-2xl font-bold text-blue-800")
        with ui.card().classes(
            "p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200"
        ):
            with ui.row().classes("items-center gap-3"):
                ui.icon("check_circle").classes("w-10 h-10 text-green-500")
                with ui.column().classes("items-start"):
                    ui.label("已完成").classes("text-sm text-green-600 font-medium")
                    ui.label("0").classes("text-2xl font-bold text-green-800")
        with ui.card().classes(
            "p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-xl border border-red-200"
        ):
            with ui.row().classes("items-center gap-3"):
                ui.icon("error").classes("w-10 h-10 text-red-500")
                with ui.column().classes("items-start"):
                    ui.label("失败").classes("text-sm text-red-600 font-medium")
                    ui.label("0").classes("text-2xl font-bold text-red-800")

    # 定义函数
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

    # 绑定事件
    search_btn.on("click", refresh_tasks)
    refresh_btn.on("click", refresh_tasks)

    # 初始加载
    refresh_tasks()
