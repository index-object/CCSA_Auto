from nicegui import ui
from ccsa_auto.ui.components.admin import (
    admin_sidebar,
    breadcrumb,
    AdminButton,
    AdminInput,
    AdminSelect,
    AdminSwitch,
)


@ui.page("/admin/config")
def admin_config():
    def save_config():
        ui.notify("配置已保存", type="positive")

    def reset_config():
        ui.notify("配置已重置为默认值", type="info")

    with ui.row().classes("w-full h-screen bg-slate-900 overflow-hidden"):
        admin_sidebar("/admin/config")

        with ui.column().classes("flex-1 h-full"):
            with ui.row().classes(
                "items-center justify-between px-8 py-6 border-b border-slate-700 bg-slate-900 flex-shrink-0"
            ):
                with ui.column():
                    breadcrumb(
                        [
                            {"label": "首页", "route": "/admin"},
                            {"label": "系统配置"},
                        ]
                    )
                    ui.label("系统配置").classes("text-2xl font-bold text-white mt-2")

                with ui.row().classes("items-center gap-3"):
                    AdminButton.secondary("重置", icon="restore", on_click=reset_config)
                    AdminButton.primary("保存配置", icon="save", on_click=save_config)

            with ui.column().classes("flex-1 overflow-y-auto"):
                with ui.column().classes("w-full p-6 gap-6"):
                    with ui.card().classes(
                        "w-full bg-slate-800 rounded-xl border border-slate-700 "
                        "hover:border-slate-600 transition-all duration-300"
                    ):
                        with ui.row().classes(
                            "items-center px-6 py-4 border-b border-slate-700"
                        ):
                            ui.icon("schedule").classes("w-6 h-6 text-blue-400")
                            ui.label("任务调度配置").classes(
                                "text-white text-lg font-semibold ml-3"
                            )

                        with ui.column().classes("p-6 gap-6"):
                            with ui.column().classes("gap-4"):
                                with ui.row().classes(
                                    "items-center justify-between flex-wrap gap-4"
                                ):
                                    ui.label("每日一题").classes(
                                        "text-white font-medium w-32"
                                    )
                                    with ui.row().classes(
                                        "items-center gap-2 flex-1 flex-wrap"
                                    ):
                                        AdminInput.time(value="09:00").classes("w-28")
                                        ui.label("至").classes("text-slate-400")
                                        AdminInput.time(value="18:00").classes("w-28")
                                    AdminSwitch.create(value=True)

                                with ui.row().classes(
                                    "items-center justify-between flex-wrap gap-4"
                                ):
                                    ui.label("每周一课").classes(
                                        "text-white font-medium w-32"
                                    )
                                    with ui.row().classes(
                                        "items-center gap-2 flex-1 flex-wrap"
                                    ):
                                        AdminSelect.small(
                                            options=[
                                                "周一",
                                                "周二",
                                                "周三",
                                                "周四",
                                                "周五",
                                                "周六",
                                                "周日",
                                            ],
                                            value="周一",
                                        )
                                        ui.label("10:00").classes("text-slate-400")
                                    AdminSwitch.create(value=True)

                                with ui.row().classes(
                                    "items-center justify-between flex-wrap gap-4"
                                ):
                                    ui.label("每月一考").classes(
                                        "text-white font-medium w-32"
                                    )
                                    with ui.row().classes(
                                        "items-center gap-2 flex-1 flex-wrap"
                                    ):
                                        ui.label("每月").classes("text-slate-400")
                                        AdminInput.number(
                                            value=1, min_value=1, max_value=31
                                        ).classes("w-16")
                                        ui.label("号 09:00").classes("text-slate-400")
                                    AdminSwitch.create(value=False)

                    with ui.card().classes(
                        "w-full bg-slate-800 rounded-xl border border-slate-700 "
                        "hover:border-slate-600 transition-all duration-300"
                    ):
                        with ui.row().classes(
                            "items-center px-6 py-4 border-b border-slate-700"
                        ):
                            ui.icon("build").classes("w-6 h-6 text-amber-400")
                            ui.label("任务修复器").classes(
                                "text-white text-lg font-semibold ml-3"
                            )

                        with ui.column().classes("p-6 gap-4"):
                            with ui.row().classes(
                                "items-center justify-between flex-wrap gap-4"
                            ):
                                ui.label("自动修复失败任务").classes(
                                    "text-white font-medium flex-1"
                                )
                                AdminSwitch.create(value=True)

                            with ui.row().classes(
                                "items-center justify-between flex-wrap gap-4"
                            ):
                                ui.label("失败通知邮件").classes(
                                    "text-white font-medium flex-1"
                                )
                                AdminSwitch.create(value=True)

                            with ui.row().classes(
                                "items-center justify-between flex-wrap gap-4"
                            ):
                                ui.label("最大重试次数").classes(
                                    "text-white font-medium w-32"
                                )
                                AdminInput.number(
                                    value=3, min_value=1, max_value=10
                                ).classes("w-20")

                            with ui.row().classes(
                                "items-center justify-between flex-wrap gap-4"
                            ):
                                ui.label("任务超时时间(秒)").classes(
                                    "text-white font-medium w-32"
                                )
                                AdminInput.number(
                                    value=30, min_value=5, max_value=300
                                ).classes("w-20")

                    with ui.card().classes(
                        "w-full bg-slate-800 rounded-xl border border-slate-700 "
                        "hover:border-slate-600 transition-all duration-300"
                    ):
                        with ui.row().classes(
                            "items-center px-6 py-4 border-b border-slate-700"
                        ):
                            ui.icon("notifications_active").classes(
                                "w-6 h-6 text-green-400"
                            )
                            ui.label("通知设置").classes(
                                "text-white text-lg font-semibold ml-3"
                            )

                        with ui.column().classes("p-6 gap-4"):
                            with ui.row().classes(
                                "items-center justify-between flex-wrap gap-4"
                            ):
                                ui.label("任务执行成功通知").classes(
                                    "text-white font-medium flex-1"
                                )
                                AdminSwitch.create(value=True)

                            with ui.row().classes(
                                "items-center justify-between flex-wrap gap-4"
                            ):
                                ui.label("任务执行失败通知").classes(
                                    "text-white font-medium flex-1"
                                )
                                AdminSwitch.create(value=True)

                            with ui.row().classes(
                                "items-center justify-between flex-wrap gap-4"
                            ):
                                ui.label("新用户注册通知").classes(
                                    "text-white font-medium flex-1"
                                )
                                AdminSwitch.create(value=False)

                    with ui.row().classes("justify-end gap-3 mt-4 flex-wrap"):
                        AdminButton.secondary("取消", on_click=reset_config)
                        AdminButton.primary("保存配置", on_click=save_config)
