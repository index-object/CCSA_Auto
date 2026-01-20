from nicegui import ui
from ccsa_auto.ui.components.admin import (
    admin_sidebar,
    breadcrumb,
    AdminButton,
    AdminInput,
    AdminSelect,
)


@ui.page("/admin/announcements")
def admin_announcements():
    def publish_announcement():
        ui.notify("公告已发布", type="positive")

    def delete_announcement(announcement_id: int):
        ui.notify("公告已删除", type="warning")

    def edit_announcement(announcement_id: int):
        ui.notify("打开编辑窗口", type="info")

    def refresh_announcements():
        ui.notify("公告列表已刷新", type="positive")

    def export_announcements():
        ui.notify("正在导出公告数据...", type="info")

    announcements_data = [
        {
            "id": 1,
            "title": "关于清明节放假安排的通知",
            "type": "important",
            "content": "清明节放假时间为4月4日至4月6日，共3天...",
            "created_at": "2024-03-15 09:30",
            "views": 1234,
            "status": "published",
        },
        {
            "id": 2,
            "title": "系统维护通知",
            "type": "info",
            "content": "本周六凌晨2:00-4:00进行系统维护...",
            "created_at": "2024-03-14 14:00",
            "views": 567,
            "status": "published",
        },
        {
            "id": 3,
            "title": "新功能上线公告",
            "type": "info",
            "content": "全新任务管理功能现已上线...",
            "created_at": "2024-03-10 10:00",
            "views": 890,
            "status": "published",
        },
    ]

    def get_type_info(type_key: str):
        type_map = {
            "important": ("重要", "red", "bg-red-500/20"),
            "info": ("普通", "blue", "bg-blue-500/20"),
            "warning": ("提醒", "amber", "bg-amber-500/20"),
        }
        return type_map.get(type_key, ("普通", "gray", "bg-slate-500/20"))

    with ui.row().classes("w-full h-screen bg-slate-900 overflow-hidden"):
        admin_sidebar("/admin/announcements")

        with ui.column().classes("flex-1 h-full"):
            with ui.row().classes(
                "items-center justify-between px-8 py-6 border-b border-slate-700 bg-slate-900 flex-shrink-0"
            ):
                with ui.column():
                    breadcrumb(
                        [
                            {"label": "首页", "route": "/admin"},
                            {"label": "公告管理"},
                        ]
                    )
                    ui.label("公告管理").classes("text-2xl font-bold text-white mt-2")

                from ccsa_auto.ui.components.admin.toolbar import toolbar

                toolbar(
                    search_placeholder="搜索公告...",
                    filters=["全部", "已发布", "草稿", "已下架"],
                    actions=[
                        {
                            "icon": "refresh",
                            "on_click": refresh_announcements,
                            "style": "secondary",
                        },
                        {
                            "icon": "download",
                            "text": "导出",
                            "on_click": export_announcements,
                            "style": "secondary",
                        },
                        {
                            "icon": "add",
                            "text": "发布公告",
                            "on_click": publish_announcement,
                            "primary": True,
                        },
                    ],
                ).render()

            with ui.column().classes("flex-1 overflow-y-auto"):
                with ui.column().classes("w-full p-6"):
                    with ui.card().classes(
                        "w-full bg-slate-800 rounded-xl border border-slate-700 "
                        "hover:border-slate-600 transition-all duration-300"
                    ):
                        with ui.column().classes("p-4 gap-4"):
                            for announcement in announcements_data:
                                type_label, color, bg_color = get_type_info(
                                    announcement["type"]
                                )

                                with ui.card().classes(
                                    "bg-slate-700/50 rounded-lg p-4 "
                                    "hover:bg-slate-700 transition-all duration-200 cursor-pointer"
                                ):
                                    with ui.row().classes(
                                        "items-start gap-4 flex-wrap"
                                    ):
                                        with ui.column().classes("flex-1 min-w-0"):
                                            with ui.row().classes(
                                                "items-center gap-3 flex-wrap"
                                            ):
                                                ui.label(announcement["title"]).classes(
                                                    "text-white text-lg font-semibold truncate"
                                                )
                                                ui.label(type_label).classes(
                                                    f"px-2 py-0.5 rounded-full text-xs font-medium "
                                                    f"{bg_color} text-{color}-400"
                                                )

                                            ui.label(
                                                announcement["content"][:100] + "..."
                                            ).classes(
                                                "text-slate-400 text-sm mt-2 line-clamp-2"
                                            )

                                            with ui.row().classes(
                                                "items-center gap-4 mt-3 flex-wrap"
                                            ):
                                                ui.label(
                                                    f"发布时间: {announcement['created_at']}"
                                                ).classes("text-slate-500 text-xs")
                                                ui.label(
                                                    f"阅读量: {announcement['views']}"
                                                ).classes("text-slate-500 text-xs")

                                        with ui.column().classes("items-end gap-2"):
                                            with ui.row().classes("gap-2"):
                                                AdminButton.icon_sm(
                                                    "edit",
                                                    on_click=lambda a=announcement: edit_announcement(
                                                        a["id"]
                                                    ),
                                                    tooltip="编辑",
                                                )
                                                AdminButton.icon_sm(
                                                    "delete",
                                                    on_click=lambda a=announcement: delete_announcement(
                                                        a["id"]
                                                    ),
                                                    tooltip="删除",
                                                ).classes("text-red-400")
