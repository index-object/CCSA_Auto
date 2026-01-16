"""管理后台页面模块"""

from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService
from ccsa_auto.modules.announcement.service import AnnouncementService
from ccsa_auto.modules.logging.service import LoggingService


def create_admin_page():
    """创建管理后台页面"""
    with ui.card().classes("w-full h-auto p-6 page-card admin-page"):
        ui.label("管理后台").classes("text-2xl font-bold mb-6")

        with ui.row().classes("w-full mb-4") as tabs:
            ui.button("用户管理")
            ui.button("任务管理")
            ui.button("公告管理")
            ui.button("操作日志")
            ui.button("系统配置")
            ui.button("数据统计")

        with ui.column().classes("w-full"):
            with ui.card().classes("w-full page-card users-tab"):
                ui.label("用户管理").classes("text-xl font-bold mb-4")

                keyword_input = ui.input("搜索账号/公司").classes("w-48")
                status_select = ui.select(
                    {None: "全部", 0: "正常", 1: "封号"}, label="状态", value=None
                ).classes("w-32")

                user_table = ui.table(
                    columns=[
                        {"name": "id", "label": "ID", "field": "id", "align": "center"},
                        {"name": "username", "label": "账号", "field": "username"},
                        {
                            "name": "company_name",
                            "label": "公司",
                            "field": "company_name",
                        },
                        {
                            "name": "status",
                            "label": "状态",
                            "field": "status",
                            "align": "center",
                        },
                        {
                            "name": "created_at",
                            "label": "创建时间",
                            "field": "created_at",
                        },
                    ],
                    rows=[],
                    row_key="id",
                    selection="multiple",
                ).classes("w-full")

                def refresh_users():
                    result = AdminService.get_users(
                        keyword=keyword_input.value or "",
                        status=status_select.value,
                    )
                    if result["success"]:
                        for user in result["users"]:
                            user["status"] = "正常" if user["status"] == 0 else "封号"
                        user_table.rows = result["users"]

                def batch_update_status(status):
                    selected = user_table.selected
                    if not selected:
                        ui.notify("请先选择用户", type="warning")
                        return
                    user_ids = [row["id"] for row in selected]
                    result = AdminService.batch_update_user_status(user_ids, status)
                    ui.notify(
                        result["message"],
                        type="positive" if result["success"] else "negative",
                    )
                    refresh_users()

                ui.button("搜索", on_click=refresh_users).classes(
                    "bg-blue-500 text-white"
                )
                ui.button("刷新", on_click=refresh_users).classes("bg-gray-100")
                ui.button("批量封禁", on_click=lambda: batch_update_status(1)).classes(
                    "bg-red-500 text-white"
                )
                ui.button("批量解封", on_click=lambda: batch_update_status(0)).classes(
                    "bg-green-500 text-white"
                )

                refresh_users()

            with ui.card().classes("w-full page-card tasks-tab"):
                ui.label("任务管理").classes("text-xl font-bold mb-4")

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
                task_status_select = ui.select(
                    {
                        None: "全部",
                        "pending": "待执行",
                        "running": "执行中",
                        "completed": "已完成",
                        "failed": "失败",
                    },
                    label="执行状态",
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
                        task_type=task_type_select.value,
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
                            task["task_type"] = task_type_map.get(
                                task.get("task_type"), ""
                            )
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

                ui.button("搜索", on_click=refresh_tasks).classes(
                    "bg-blue-500 text-white"
                )
                ui.button("刷新", on_click=refresh_tasks).classes("bg-gray-100")

                refresh_tasks()

            with ui.card().classes("w-full page-card announcements-tab"):
                ui.label("公告管理").classes("text-xl font-bold mb-4")

                title = ui.input("标题").classes("w-full mb-4")
                content = ui.textarea("内容").classes("w-full mb-4")

                announcement_table = ui.table(
                    columns=[
                        {"name": "id", "label": "ID", "field": "id", "align": "center"},
                        {"name": "title", "label": "标题", "field": "title"},
                        {
                            "name": "created_at",
                            "label": "发布时间",
                            "field": "created_at",
                        },
                    ],
                    rows=[],
                    row_key="id",
                ).classes("w-full mb-4")

                editing_id = [None]

                def create_announcement():
                    if title.value and content.value:
                        result = AnnouncementService.create_announcement(
                            title.value, content.value
                        )
                        if result["success"]:
                            ui.notify("公告发布成功", type="positive")
                            title.value = ""
                            content.value = ""
                            editing_id[0] = None
                            refresh_announcements()
                        else:
                            ui.notify(result["message"], type="negative")
                    else:
                        ui.notify("标题和内容不能为空", type="warning")

                def update_announcement():
                    if not editing_id[0]:
                        return
                    if title.value and content.value:
                        result = AnnouncementService.update_announcement(
                            editing_id[0], title.value, content.value
                        )
                        if result["success"]:
                            ui.notify("公告更新成功", type="positive")
                            title.value = ""
                            content.value = ""
                            editing_id[0] = None
                            refresh_announcements()
                        else:
                            ui.notify(result["message"], type="negative")
                    else:
                        ui.notify("标题和内容不能为空", type="warning")

                def refresh_announcements():
                    result = AnnouncementService.get_announcements()
                    if result["success"]:
                        announcement_table.rows = result["announcements"]

                def edit_handler(row):
                    title.value = row["title"]
                    editing_id[0] = row["id"]
                    content.value = row.get("content", "")

                def delete_handler(row):
                    result = AnnouncementService.delete_announcement(row["id"])
                    if result["success"]:
                        ui.notify("公告删除成功", type="positive")
                        refresh_announcements()
                    else:
                        ui.notify(result["message"], type="negative")

                ui.button("发布公告", on_click=create_announcement).classes(
                    "bg-blue-500 text-white"
                )
                ui.button("保存修改", on_click=update_announcement).classes(
                    "bg-green-500 text-white mr-2"
                )
                ui.button("刷新列表", on_click=refresh_announcements).classes(
                    "bg-gray-100"
                )

                refresh_announcements()

            with ui.card().classes("w-full page-card logs-tab"):
                ui.label("操作日志").classes("text-xl font-bold mb-4")

                log_type_select = ui.select(
                    {
                        "all": "全部",
                        "operation": "操作日志",
                        "task": "任务日志",
                        "auth": "认证日志",
                        "error": "错误日志",
                    },
                    label="日志类型",
                    value="all",
                ).classes("w-32")
                log_user_input = ui.input("用户ID").classes("w-32")

                log_table = ui.table(
                    columns=[
                        {"name": "created_at", "label": "时间", "field": "created_at"},
                        {"name": "log_type", "label": "类型", "field": "log_type"},
                        {"name": "operation", "label": "操作", "field": "operation"},
                        {"name": "content", "label": "内容", "field": "content"},
                        {"name": "user_id", "label": "用户ID", "field": "user_id"},
                        {"name": "status", "label": "状态", "field": "status"},
                    ],
                    rows=[],
                    row_key="id",
                ).classes("w-full")

                log_page = ui.label("第 1 页").classes("text-center")

                def refresh_logs():
                    result = LoggingService.get_logs(
                        log_type=log_type_select.value
                        if log_type_select.value != "all"
                        else None,
                        user_id=int(log_user_input.value)
                        if log_user_input.value
                        else None,
                        page=1,
                        page_size=20,
                    )
                    if result["success"]:
                        log_type_map = {
                            "operation": "操作",
                            "task": "任务",
                            "auth": "认证",
                            "system": "系统",
                            "error": "错误",
                        }
                        for log in result["logs"]:
                            log["log_type"] = log_type_map.get(log.get("log_type"), "")
                        log_table.rows = result["logs"]
                        log_page.text = f"第 {result['page']} 页 / 共 {(result['total'] + 19) // 20} 页"

                def change_page(delta):
                    current_page = int(log_page.text.split(" ")[1])
                    new_page = current_page + delta
                    if new_page < 1:
                        return
                    result = LoggingService.get_logs(
                        log_type=log_type_select.value
                        if log_type_select.value != "all"
                        else None,
                        user_id=int(log_user_input.value)
                        if log_user_input.value
                        else None,
                        page=new_page,
                        page_size=20,
                    )
                    if result["success"]:
                        log_type_map = {
                            "operation": "操作",
                            "task": "任务",
                            "auth": "认证",
                            "system": "系统",
                            "error": "错误",
                        }
                        for log in result["logs"]:
                            log["log_type"] = log_type_map.get(log.get("log_type"), "")
                        log_table.rows = result["logs"]
                        log_page.text = (
                            f"第 {new_page} 页 / 共 {(result['total'] + 19) // 20} 页"
                        )

                def export_logs():
                    filepath = LoggingService.export_to_xlsx(
                        log_type=log_type_select.value
                        if log_type_select.value != "all"
                        else None
                    )
                    if filepath:
                        ui.notify(f"日志已导出", type="positive")
                        ui.download(filepath)
                    else:
                        ui.notify("导出失败", type="negative")

                ui.button("筛选", on_click=refresh_logs).classes(
                    "bg-blue-500 text-white"
                )
                ui.button("导出XLSX", on_click=export_logs).classes(
                    "bg-green-500 text-white"
                )

                with ui.row().classes("justify-center mt-4 gap-4"):
                    ui.button("上一页", on_click=lambda: change_page(-1))
                    log_page
                    ui.button("下一页", on_click=lambda: change_page(1))

                refresh_logs()

            with ui.card().classes("w-full page-card config-tab"):
                ui.label("系统配置").classes("text-xl font-bold mb-4")

                result = AdminService.get_system_config()
                if result["success"]:
                    config = result["config"]
                    task_details = config["task_details"]

                    ui.label("任务调度时间配置").classes("text-lg font-bold mb-2 mt-4")

                    with ui.row().classes("gap-4 mb-4"):
                        ui.label("每日一题:").classes("self-center")
                        daily_start = ui.number(
                            "开始",
                            value=task_details["DAILY"]["hour_range"][0],
                            min=0,
                            max=23,
                        ).classes("w-20")
                        ui.label("-").classes("self-center")
                        daily_end = ui.number(
                            "结束",
                            value=task_details["DAILY"]["hour_range"][1],
                            min=0,
                            max=23,
                        ).classes("w-20")

                    with ui.row().classes("gap-4 mb-4"):
                        ui.label("每周一课:").classes("self-center")
                        weekly_start = ui.number(
                            "开始",
                            value=task_details["WEEKLY"]["hour_range"][0],
                            min=0,
                            max=23,
                        ).classes("w-20")
                        ui.label("-").classes("self-center")
                        weekly_end = ui.number(
                            "结束",
                            value=task_details["WEEKLY"]["hour_range"][1],
                            min=0,
                            max=23,
                        ).classes("w-20")

                    with ui.row().classes("gap-4 mb-4"):
                        ui.label("每月一考:").classes("self-center")
                        monthly_start = ui.number(
                            "开始",
                            value=task_details["MONTHLY"]["hour_range"][0],
                            min=0,
                            max=23,
                        ).classes("w-20")
                        ui.label("-").classes("self-center")
                        monthly_end = ui.number(
                            "结束",
                            value=task_details["MONTHLY"]["hour_range"][1],
                            min=0,
                            max=23,
                        ).classes("w-20")

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
                        "bg-blue-500 text-white"
                    )

                    ui.label("任务修复器").classes("text-lg font-bold mb-2 mt-6")
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
                        "bg-green-500 text-white"
                    )

            with ui.card().classes("w-full page-card statistics-tab"):
                ui.label("数据统计").classes("text-xl font-bold mb-4")

                stats_container = ui.column().classes("w-full")

                def show_statistics():
                    stats_container.clear()
                    result = AdminService.get_statistics()
                    if result["success"]:
                        data = result["data"]

                        with stats_container:
                            with ui.row().classes("gap-4 mb-4"):
                                with ui.card().classes("p-4"):
                                    ui.label("用户统计").classes(
                                        "text-lg font-semibold mb-2"
                                    )
                                    ui.label(f"总用户: {data['users']['total']}")
                                    ui.label(f"活跃用户: {data['users']['active']}")
                                    ui.label(f"封号用户: {data['users']['banned']}")
                                    ui.label(f"本周新增: {data['users']['new_week']}")
                                    ui.label(f"本月新增: {data['users']['new_month']}")
                                with ui.card().classes("p-4"):
                                    ui.label("任务统计").classes(
                                        "text-lg font-semibold mb-2"
                                    )
                                    ui.label(f"总任务: {data['tasks']['total']}")
                                    ui.label(f"激活任务: {data['tasks']['active']}")
                                    ui.label(f"待执行: {data['tasks']['pending']}")
                                    ui.label(f"执行中: {data['tasks']['running']}")
                                    ui.label(f"已完成: {data['tasks']['completed']}")
                                    ui.label(f"失败: {data['tasks']['failed']}")
                                with ui.card().classes("p-4"):
                                    ui.label("完成趋势").classes(
                                        "text-lg font-semibold mb-2"
                                    )
                                    ui.label(
                                        f"本周完成: {data['tasks']['completed_week']}"
                                    )
                                    ui.label(
                                        f"本月完成: {data['tasks']['completed_month']}"
                                    )
                                with ui.card().classes("p-4"):
                                    ui.label("公告统计").classes(
                                        "text-lg font-semibold mb-2"
                                    )
                                    ui.label(
                                        f"总公告: {data['announcements']['total']}"
                                    )

                            with ui.card().classes("p-4 w-full"):
                                ui.label("每日趋势（近7天）").classes(
                                    "text-lg font-semibold mb-2"
                                )
                                trend_result = AdminService.get_daily_stats(7)
                                if trend_result["success"]:
                                    trend_table = ui.table(
                                        columns=[
                                            {
                                                "name": "date",
                                                "label": "日期",
                                                "field": "date",
                                            },
                                            {
                                                "name": "new_users",
                                                "label": "新增用户",
                                                "field": "new_users",
                                            },
                                            {
                                                "name": "completed_tasks",
                                                "label": "完成任务",
                                                "field": "completed_tasks",
                                            },
                                        ],
                                        rows=trend_result["stats"],
                                        row_key="date",
                                    ).classes("w-full")

                def export_report():
                    filepath = AdminService.export_statistics_report()
                    if filepath:
                        ui.notify("报表已导出", type="positive")
                        ui.download(filepath)
                    else:
                        ui.notify("导出失败", type="negative")

                ui.button("刷新统计", on_click=show_statistics).classes(
                    "bg-blue-500 text-white mr-2"
                )
                ui.button("导出报表", on_click=export_report).classes(
                    "bg-green-500 text-white"
                )

                show_statistics()
