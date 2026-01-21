from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService
from ccsa_auto.ui.components.admin.common import PageHeader, LoadingOverlay, Toast


def create_statistics():
    """创建数据统计页面 - 现代化增强版"""
    loading = LoadingOverlay("加载统计数据中...")

    # 页面标题
    header = PageHeader(
        title="数据统计",
        subtitle="平台运营数据概览和分析",
        icon="insights",
    )
    header.render()

    # 操作按钮
    with ui.row().classes("gap-3 mb-6"):
        refresh_btn = ui.button("刷新统计", icon="refresh").classes(
            "bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        )
        export_btn = ui.button("导出报表", icon="download").classes(
            "bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
        )

    # 统计内容容器
    content_container = ui.column().classes("w-full")

    def show_statistics():
        content_container.clear()
        with content_container:
            loading.show()
            try:
                result = AdminService.get_statistics()
                if result["success"]:
                    data = result["data"]

                    # 用户统计卡片
                    with ui.row().classes("gap-4 mb-4 flex-wrap"):
                        user_stats = data["users"]
                        with ui.card().classes(
                            "p-5 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200"
                        ):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                with ui.column().classes("items-start"):
                                    ui.label("总用户").classes(
                                        "text-sm text-blue-600 font-medium"
                                    )
                                    ui.label(str(user_stats["total"])).classes(
                                        "text-3xl font-bold text-blue-800"
                                    )
                                ui.icon("people").classes("w-12 h-12 text-blue-400")
                        with ui.card().classes(
                            "p-5 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200"
                        ):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                with ui.column().classes("items-start"):
                                    ui.label("活跃用户").classes(
                                        "text-sm text-green-600 font-medium"
                                    )
                                    ui.label(str(user_stats["active"])).classes(
                                        "text-3xl font-bold text-green-800"
                                    )
                                ui.icon("how_to_reg").classes(
                                    "w-12 h-12 text-green-400"
                                )
                        with ui.card().classes(
                            "p-5 bg-gradient-to-br from-red-50 to-red-100 rounded-xl border border-red-200"
                        ):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                with ui.column().classes("items-start"):
                                    ui.label("封号用户").classes(
                                        "text-sm text-red-600 font-medium"
                                    )
                                    ui.label(str(user_stats["banned"])).classes(
                                        "text-3xl font-bold text-red-800"
                                    )
                                ui.icon("block").classes("w-12 h-12 text-red-400")
                        with ui.card().classes(
                            "p-5 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border border-purple-200"
                        ):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                with ui.column().classes("items-start"):
                                    ui.label("本周新增").classes(
                                        "text-sm text-purple-600 font-medium"
                                    )
                                    ui.label(str(user_stats["new_week"])).classes(
                                        "text-3xl font-bold text-purple-800"
                                    )
                                ui.icon("trending_up").classes(
                                    "w-12 h-12 text-purple-400"
                                )

                    # 任务统计卡片
                    task_stats = data["tasks"]
                    with ui.row().classes("gap-4 mb-4 flex-wrap"):
                        with ui.card().classes(
                            "p-5 bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-xl border border-cyan-200"
                        ):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                with ui.column().classes("items-start"):
                                    ui.label("总任务").classes(
                                        "text-sm text-cyan-600 font-medium"
                                    )
                                    ui.label(str(task_stats["total"])).classes(
                                        "text-3xl font-bold text-cyan-800"
                                    )
                                ui.icon("assignment").classes("w-12 h-12 text-cyan-400")
                        with ui.card().classes(
                            "p-5 bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl border border-emerald-200"
                        ):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                with ui.column().classes("items-start"):
                                    ui.label("已完成").classes(
                                        "text-sm text-emerald-600 font-medium"
                                    )
                                    ui.label(str(task_stats["completed"])).classes(
                                        "text-3xl font-bold text-emerald-800"
                                    )
                                ui.icon("check_circle").classes(
                                    "w-12 h-12 text-emerald-400"
                                )
                        with ui.card().classes(
                            "p-5 bg-gradient-to-br from-amber-50 to-amber-100 rounded-xl border border-amber-200"
                        ):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                with ui.column().classes("items-start"):
                                    ui.label("执行中").classes(
                                        "text-sm text-amber-600 font-medium"
                                    )
                                    ui.label(str(task_stats["running"])).classes(
                                        "text-3xl font-bold text-amber-800"
                                    )
                                ui.icon("play_circle").classes(
                                    "w-12 h-12 text-amber-400"
                                )
                        with ui.card().classes(
                            "p-5 bg-gradient-to-br from-rose-50 to-rose-100 rounded-xl border border-rose-200"
                        ):
                            with ui.row().classes(
                                "items-center justify-between w-full"
                            ):
                                with ui.column().classes("items-start"):
                                    ui.label("失败").classes(
                                        "text-sm text-rose-600 font-medium"
                                    )
                                    ui.label(str(task_stats["failed"])).classes(
                                        "text-3xl font-bold text-rose-800"
                                    )
                                ui.icon("error").classes("w-12 h-12 text-rose-400")

                    # 公告统计
                    with ui.card().classes(
                        "p-5 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border border-gray-200 w-full"
                    ):
                        with ui.row().classes("items-center justify-between w-full"):
                            with ui.column().classes("items-start"):
                                ui.label("总公告").classes(
                                    "text-sm text-gray-600 font-medium"
                                )
                                ui.label(str(data["announcements"]["total"])).classes(
                                    "text-3xl font-bold text-gray-800"
                                )
                            ui.icon("campaign").classes("w-12 h-12 text-gray-400")

                    # 每日趋势表格
                    with ui.card().classes(
                        "w-full p-5 mt-4 bg-white rounded-xl border border-gray-200 shadow-sm"
                    ):
                        ui.label("每日趋势（近7天）").classes(
                            "text-lg font-semibold text-gray-800 mb-4"
                        )
                        trend_result = AdminService.get_daily_stats(7)
                        if trend_result["success"]:
                            ui.table(
                                columns=[
                                    {"name": "date", "label": "日期", "field": "date"},
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
                else:
                    Toast.error(result.get("message", "获取统计数据失败"))
            except Exception as e:
                Toast.error(f"加载失败: {str(e)}")
            finally:
                loading.close()

    def export_report():
        result = AdminService.export_statistics_report()
        if result:
            Toast.success("报表导出成功")
            ui.download(result)
        else:
            Toast.error("导出失败")

    # 绑定事件
    refresh_btn.on("click", show_statistics)
    export_btn.on("click", export_report)

    # 初始加载
    show_statistics()
