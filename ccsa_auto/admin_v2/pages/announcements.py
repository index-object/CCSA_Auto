from nicegui import ui

from ccsa_auto.admin_v2.services.announcement_service import (
    AnnouncementManagementService,
)


def create_announcements_page():
    """Create the announcements management page"""
    # State
    keyword = {"value": ""}
    current_page = {"value": 1}
    page_size = {"value": 20}
    announcements_data = {"data": [], "total": 0}

    def load_announcements():
        """Load announcements data"""
        result = AnnouncementManagementService.get_announcements(
            keyword=keyword["value"] if keyword["value"] else None,
            page=current_page["value"],
            page_size=page_size["value"],
        )
        if result.get("success"):
            announcements_data["data"] = result.get("data", [])
            announcements_data["total"] = result.get("total", 0)
        else:
            ui.notify(f"加载公告失败: {result.get('message')}", type="negative")

    def on_search():
        """Handle search"""
        current_page["value"] = 1
        load_announcements()

    def on_page_change(page: int):
        """Handle page change"""
        current_page["value"] = page
        load_announcements()

    def create_announcement():
        """Show create announcement dialog"""
        title_input = {"value": ""}
        content_input = {"value": ""}

        with ui.dialog() as dialog, ui.card().classes("w-full max-w-2xl"):
            ui.label("创建公告").classes("text-xl font-bold")
            ui.input(
                "标题",
                value=title_input["value"],
                on_change=lambda e: title_input.update(value=e.value),
            ).props("outlined dense clearable").classes("w-full mb-4")
            ui.textarea(
                "内容",
                value=content_input["value"],
                on_change=lambda e: content_input.update(value=e.value),
            ).props("outlined clearable").classes("w-full h-64 mb-4")

            with ui.row().classes("justify-end gap-2"):
                ui.button("取消", on_click=dialog.close).props("flat")
                ui.button(
                    "创建",
                    on_click=lambda: do_create(
                        title_input["value"], content_input["value"], dialog
                    ),
                ).props("color=primary")

        dialog.open()

    def do_create(title: str, content: str, dialog):
        """Create announcement"""
        if not title or not content:
            ui.notify("请填写标题和内容", type="warning")
            return

        result = AnnouncementManagementService.create_announcement(title, content)
        if result.get("success"):
            ui.notify("公告创建成功", type="positive")
            dialog.close()
            load_announcements()
        else:
            ui.notify(f"创建失败: {result.get('message')}", type="negative")

    def edit_announcement(
        announcement_id: int, current_title: str, current_content: str
    ):
        """Show edit announcement dialog"""
        title_input = {"value": current_title}
        content_input = {"value": current_content}

        with ui.dialog() as dialog, ui.card().classes("w-full max-w-2xl"):
            ui.label("编辑公告").classes("text-xl font-bold")
            ui.input(
                "标题",
                value=title_input["value"],
                on_change=lambda e: title_input.update(value=e.value),
            ).props("outlined dense clearable").classes("w-full mb-4")
            ui.textarea(
                "内容",
                value=content_input["value"],
                on_change=lambda e: content_input.update(value=e.value),
            ).props("outlined clearable").classes("w-full h-64 mb-4")

            with ui.row().classes("justify-end gap-2"):
                ui.button("取消", on_click=dialog.close).props("flat")
                ui.button(
                    "保存",
                    on_click=lambda: do_update(
                        announcement_id,
                        title_input["value"],
                        content_input["value"],
                        dialog,
                    ),
                ).props("color=primary")

        dialog.open()

    def do_update(announcement_id: int, title: str, content: str, dialog):
        """Update announcement"""
        if not title or not content:
            ui.notify("请填写标题和内容", type="warning")
            return

        result = AnnouncementManagementService.update_announcement(
            announcement_id, title, content
        )
        if result.get("success"):
            ui.notify("公告更新成功", type="positive")
            dialog.close()
            load_announcements()
        else:
            ui.notify(f"更新失败: {result.get('message')}", type="negative")

    def delete_announcement(announcement_id: int):
        """Delete announcement"""
        with ui.dialog() as dialog, ui.card():
            ui.label("确定要删除这条公告吗？")
            with ui.row().classes("justify-end gap-2 mt-4"):
                ui.button("取消", on_click=dialog.close).props("flat")
                ui.button(
                    "删除",
                    on_click=lambda: do_delete(announcement_id, dialog),
                ).props("color=negative")

        dialog.open()

    def do_delete(announcement_id: int, dialog):
        """Confirm delete"""
        result = AnnouncementManagementService.delete_announcement(announcement_id)
        if result.get("success"):
            ui.notify("公告删除成功", type="positive")
            dialog.close()
            load_announcements()
        else:
            ui.notify(f"删除失败: {result.get('message')}", type="negative")

    # Initial load
    load_announcements()

    # Toolbar
    with ui.card().classes("p-4 mb-4"):
        with ui.row().classes("items-center gap-4 w-full"):
            # Search
            with ui.row().classes("items-center gap-2 flex-1"):
                ui.input(
                    "搜索公告标题",
                    value=keyword["value"],
                    on_change=lambda e: keyword.update(value=e.value),
                ).props("outlined dense clearable").classes("w-64").on(
                    "keydown.enter", on_search
                )
                ui.button("搜索", on_click=on_search).props("flat color=primary")

            # Add button
            ui.button("创建公告", on_click=create_announcement, icon="add").props(
                "color=primary"
            )

    with ui.card().classes("rounded-2xl p-6 shadow-sm bg-white flex flex-col"):
        with ui.row().classes(
            "grid grid-cols-6 gap-4 pb-4 border-b border-gray-100 mb-4 shrink-0"
        ):
            ui.label("ID").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("标题").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("阅读数").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("创建时间").classes(
                "text-xs font-semibold text-[#6b7280] uppercase"
            )
            ui.label("更新时间").classes(
                "text-xs font-semibold text-[#6b7280] uppercase"
            )
            ui.label("操作").classes("text-xs font-semibold text-[#6b7280] uppercase")

        with ui.element("div").classes("overflow-y-auto max-h-[calc(100vh-380px)]"):
            for idx, ann in enumerate(announcements_data["data"]):
                row_bg = "bg-[#f9fafb]" if idx % 2 == 1 else "bg-white"

                with ui.row().classes(
                    f"grid grid-cols-6 gap-4 py-4 {row_bg} items-center"
                ):
                    ui.label(str(ann.get("id", ""))).classes("text-sm text-[#1f2937]")
                    ui.label(str(ann.get("title", ""))[:50]).classes(
                        "text-sm text-[#1f2937]"
                    )
                    ui.label(str(ann.get("read_count", 0))).classes(
                        "text-sm text-[#6b7280]"
                    )
                    ui.label(str(ann.get("created_at", ""))[:19]).classes(
                        "text-sm text-[#6b7280]"
                    )
                    ui.label(str(ann.get("updated_at", ""))[:19]).classes(
                        "text-sm text-[#6b7280]"
                    )

                    with ui.row().classes("items-center gap-1"):
                        ann_id = ann.get("id")
                        ann_title = ann.get("title")
                        ann_content = ann.get("content")

                        edit_btn = (
                            ui.button()
                            .classes(
                                "text-[#6b7280] hover:text-blue-500 hover:bg-blue-50 rounded p-1 transition-colors"
                            )
                            .props("flat dense")
                        )
                        edit_btn.on_click(
                            lambda _,
                            aid=ann_id,
                            at=ann_title,
                            ac=ann_content: edit_announcement(aid, at, ac)
                        )
                        with edit_btn:
                            ui.icon("edit").classes("text-base")

                        delete_btn = (
                            ui.button()
                            .classes(
                                "text-[#6b7280] hover:text-red-500 hover:bg-red-50 rounded p-1 transition-colors"
                            )
                            .props("flat dense")
                        )
                        delete_btn.on_click(
                            lambda _, aid=ann_id: delete_announcement(aid)
                        )
                        with delete_btn:
                            ui.icon("delete").classes("text-base")

        # Pagination
        total_pages = max(
            1,
            (announcements_data["total"] + page_size["value"] - 1)
            // page_size["value"],
        )
        with ui.row().classes("items-center justify-between w-full mt-4"):
            with ui.row().classes("items-center gap-2"):
                ui.label(f"共 {announcements_data['total']} 条").classes(
                    "text-sm text-gray-500"
                )

            total_pages = max(1, (announcements_data["total"] + 19) // 20)
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


def render():
    """Render the announcements page"""
    create_announcements_page()
