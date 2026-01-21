from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService


def create_statistics():
    stats_container = ui.column().classes("w-full")

    def show_statistics():
        stats_container.clear()
        result = AdminService.get_statistics()
        if result["success"]:
            data = result["data"]

            with stats_container:
                with ui.row().classes("gap-4 mb-4 flex-wrap"):
                    with ui.card().classes(
                        "p-4 bg-white border border-gray-200 rounded-lg shadow-sm"
                    ):
                        ui.label("用户统计").classes(
                            "text-lg font-semibold mb-2 text-gray-800"
                        )
                        ui.label(f"总用户: {data['users']['total']}").classes(
                            "text-gray-600"
                        )
                        ui.label(f"活跃用户: {data['users']['active']}").classes(
                            "text-gray-600"
                        )
                        ui.label(f"封号用户: {data['users']['banned']}").classes(
                            "text-gray-600"
                        )
                        ui.label(f"本周新增: {data['users']['new_week']}").classes(
                            "text-gray-600"
                        )
                        ui.label(f"本月新增: {data['users']['new_month']}").classes(
                            "text-gray-600"
                        )
                    with ui.card().classes(
                        "p-4 bg-white border border-gray-200 rounded-lg shadow-sm"
                    ):
                        ui.label("任务统计").classes(
                            "text-lg font-semibold mb-2 text-gray-800"
                        )
                        ui.label(f"总任务: {data['tasks']['total']}").classes(
                            "text-gray-600"
                        )
                        ui.label(f"激活任务: {data['tasks']['active']}").classes(
                            "text-gray-600"
                        )
                        ui.label(f"待执行: {data['tasks']['pending']}").classes(
                            "text-gray-600"
                        )
                        ui.label(f"执行中: {data['tasks']['running']}").classes(
                            "text-gray-600"
                        )
                        ui.label(f"已完成: {data['tasks']['completed']}").classes(
                            "text-gray-600"
                        )
                        ui.label(f"失败: {data['tasks']['failed']}").classes(
                            "text-gray-600"
                        )
                    with ui.card().classes(
                        "p-4 bg-white border border-gray-200 rounded-lg shadow-sm"
                    ):
                        ui.label("完成趋势").classes(
                            "text-lg font-semibold mb-2 text-gray-800"
                        )
                        ui.label(
                            f"本周完成: {data['tasks']['completed_week']}"
                        ).classes("text-gray-600")
                        ui.label(
                            f"本月完成: {data['tasks']['completed_month']}"
                        ).classes("text-gray-600")
                    with ui.card().classes(
                        "p-4 bg-white border border-gray-200 rounded-lg shadow-sm"
                    ):
                        ui.label("公告统计").classes(
                            "text-lg font-semibold mb-2 text-gray-800"
                        )
                        ui.label(f"总公告: {data['announcements']['total']}").classes(
                            "text-gray-600"
                        )

                with ui.card().classes(
                    "p-4 w-full bg-white border border-gray-200 rounded-lg shadow-sm"
                ):
                    ui.label("每日趋势（近7天）").classes(
                        "text-lg font-semibold mb-2 text-gray-800"
                    )
                    trend_result = AdminService.get_daily_stats(7)
                    if trend_result["success"]:
                        ui.table(
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

    with ui.row().classes("gap-3 mb-4"):
        ui.button("刷新统计", on_click=show_statistics).classes(
            "bg-blue-600 text-white hover:bg-blue-700"
        )
        ui.button("导出报表", on_click=export_report).classes(
            "bg-green-600 text-white hover:bg-green-700"
        )

    show_statistics()
