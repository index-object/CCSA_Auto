"""管理后台页面模块"""

from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService
from ccsa_auto.modules.announcement.service import AnnouncementService


def create_admin_page():
    """创建管理后台页面"""
    with ui.card().classes("w-full h-auto p-6 page-card admin-page"):
        ui.label("管理后台").classes("text-2xl font-bold mb-6")

        # 管理菜单
        with ui.row().classes("w-full mb-4") as tabs:
            users_tab = ui.button("用户管理")
            tasks_tab = ui.button("任务管理")
            announcements_tab = ui.button("公告管理")
            statistics_tab = ui.button("数据统计")

        # 用户管理
        with ui.card().classes("w-full page-card users-tab"):
            ui.label("用户管理").classes("text-xl font-bold mb-4")
            # 用户列表
            user_table = ui.table(
                columns=[
                    {"name": "id", "label": "ID", "field": "id"},
                    {"name": "username", "label": "账号", "field": "username"},
                    {"name": "company_name", "label": "公司", "field": "company_name"},
                    {"name": "status", "label": "状态", "field": "status"},
                    {"name": "created_at", "label": "创建时间", "field": "created_at"},
                    {"name": "actions", "label": "操作", "field": "actions"},
                ],
                rows=[],
                row_key="id",
            ).classes("w-full")

            # 刷新用户列表
            def refresh_users():
                """刷新用户列表"""
                result = AdminService.get_users()
                if result["success"]:
                    users = result["users"]
                    for user in users:
                        # 转换状态显示
                        user["status"] = "正常" if user["status"] == 0 else "封号"

                        # 添加操作按钮
                        user["actions"] = (
                            "编辑" if user["username"] != "admin" else "无"
                        )

                    user_table.rows = users

            # 刷新按钮
            ui.button("刷新用户", on_click=refresh_users).classes(
                "mb-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded"
            )

            # 初始加载用户
            refresh_users()

        # 任务管理
        with ui.card().classes("w-full page-card tasks-tab"):
            ui.label("任务管理").classes("text-xl font-bold mb-4")
            # 任务列表
            admin_task_table = ui.table(
                columns=[
                    {"name": "id", "label": "ID", "field": "id"},
                    {"name": "username", "label": "用户", "field": "username"},
                    {"name": "task_type", "label": "任务类型", "field": "task_type"},
                    {
                        "name": "execution_status",
                        "label": "执行状态",
                        "field": "execution_status",
                    },
                    {
                        "name": "external_status",
                        "label": "外部状态",
                        "field": "external_status",
                    },
                    {
                        "name": "scheduled_time",
                        "label": "下次运行时间",
                        "field": "scheduled_time",
                    },
                    {
                        "name": "executed_at",
                        "label": "实际执行时间",
                        "field": "executed_at",
                    },
                ],
                rows=[],
                row_key="id",
            ).classes("w-full")

            # 刷新任务列表
            def refresh_admin_tasks():
                """刷新任务列表"""
                result = AdminService.get_all_tasks()
                if result["success"]:
                    tasks = result["tasks"]
                    for task in tasks:
                        # 转换任务类型显示
                        task_type_map = {
                            "daily": "每日一题",
                            "weekly": "每周一课",
                            "monthly": "每月一考",
                        }
                        task["task_type"] = task_type_map.get(
                            task["task_type"], task["task_type"]
                        )

                        # 转换执行状态显示
                        execution_status_map = {
                            "pending": "待执行",
                            "running": "执行中",
                            "completed": "已完成",
                        }
                        task["execution_status"] = execution_status_map.get(
                            task["execution_status"], task["execution_status"]
                        )

                        # 转换外部状态显示
                        external_status_map = {
                            "success": "成功",
                            "failed": "失败",
                            "unknown": "未知",
                        }
                        task["external_status"] = external_status_map.get(
                            task["external_status"], task["external_status"]
                        )

                    admin_task_table.rows = tasks

            # 刷新按钮
            ui.button("刷新任务", on_click=refresh_admin_tasks).classes(
                "mb-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded"
            )

            # 初始加载任务
            refresh_admin_tasks()

        # 公告管理
        with ui.card().classes("w-full page-card announcements-tab"):
            ui.label("公告管理").classes("text-xl font-bold mb-4")
            # 创建公告表单
            title = ui.input("标题").classes("w-full mb-4")
            content = ui.textarea("内容").classes("w-full mb-4")

            def create_announcement():
                """创建公告"""
                if title.value and content.value:
                    result = AnnouncementService.create_announcement(
                        title.value, content.value
                    )
                    if result["success"]:
                        ui.notify("公告发布成功", type="success")
                        title.value = ""
                        content.value = ""
                    else:
                        ui.notify(result["message"], type="error")
                else:
                    ui.notify("标题和内容不能为空", type="error")

            ui.button("发布", on_click=create_announcement).classes(
                "bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded"
            )

        # 数据统计
        with ui.card().classes("w-full page-card statistics-tab"):
            ui.label("数据统计").classes("text-xl font-bold mb-4")

            # 统计数据
            def show_statistics():
                """显示统计数据"""
                result = AdminService.get_statistics()
                if result["success"]:
                    data = result["data"]
                    with ui.row().classes("gap-4"):
                        # 用户统计
                        with ui.card().classes("p-4"):
                            ui.label("用户统计").classes("text-lg font-semibold mb-2")
                            ui.label(f"总用户: {data['users']['total']}")
                            ui.label(f"活跃用户: {data['users']['active']}")
                            ui.label(f"封号用户: {data['users']['banned']}")

                        # 任务统计
                        with ui.card().classes("p-4"):
                            ui.label("任务统计").classes("text-lg font-semibold mb-2")
                            ui.label(f"总任务: {data['tasks']['total']}")
                            ui.label(f"待执行: {data['tasks']['pending']}")
                            ui.label(f"已完成: {data['tasks']['completed']}")

                        # 公告统计
                        with ui.card().classes("p-4"):
                            ui.label("公告统计").classes("text-lg font-semibold mb-2")
                            ui.label(f"总公告: {data['announcements']['total']}")

            # 初始加载统计数据
            show_statistics()
