from nicegui import ui

from ccsa_auto.admin_v2.services.announcement_service import AnnouncementManagementService


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
                    on_click=lambda: do_create(title_input["value"], content_input["value"], dialog),
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

    def edit_announcement(announcement_id: int, current_title: str, current_content: str):
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
                        announcement_id, title_input["value"], content_input["value"], dialog
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
                    on_enter=on_search,
                ).props("outlined dense clearable").classes("w-64")
                ui.button("搜索", on_click=on_search).props("flat color=primary")

            # Add button
            ui.button("创建公告", on_click=create_announcement, icon="add").props(
                "color=primary"
            )

    # Announcements table
    with ui.card().classes("p-4"):
        # Table header
        with ui.row().classes("font-bold border-b pb-2 mb-2"):
            with ui.column().classes("w-16"):
                ui.label("ID")
            with ui.column().classes("flex-1"):
                ui.label("标题")
            with ui.column().classes("w-24"):
                ui.label("阅读数")
            with ui.column().classes("w-32"):
                ui.label("创建时间")
            with ui.column().classes("w-32"):
                ui.label("更新时间")
            with ui.column().classes("w-32"):
                ui.label("操作")

        # Table rows
        for ann in announcements_data["data"]:
            with ui.row().classes("border-b py-2 hover:bg-gray-50 items-center"):
                with ui.column().classes("w-16"):
                    ui.label(str(ann.get("id", "")))
                with ui.column().classes("flex-1"):
                    ui.label(str(ann.get("title", ""))[:50])
                with ui.column().classes("w-24"):
                    ui.label(str(ann.get("read_count", 0)))
                with ui.column().classes("w-32"):
                    ui.label(str(ann.get("created_at", ""))[:19])
                with ui.column().classes("w-32"):
                    ui.label(str(ann.get("updated_at", ""))[:19])
                with ui.column().classes("w-32"):
                    with ui.row().classes("gap-1"):
                        ui.button(
                            "编辑",
                            on_click=lambda a=ann: edit_announcement(
                                a.get("id"), a.get("title"), a.get("content")
                            ),
                            icon="edit",
                        ).props("flat dense size=sm")
                        ui.button(
                            "删除",
                            on_click=lambda a=ann: delete_announcement(a.get("id")),
                            icon="delete",
                        ).props("flat dense size=sm color=negative")

        # Pagination
        total_pages = max(
            1,
            (announcements_data["total"] + page_size["value"] - 1) // page_size["value"],
        )
        with ui.row().classes("items-center justify-between w-full mt-4"):
            with ui.row().classes("items-center gap-2"):
                ui.label(f"共 {announcements_data['total']} 条").classes(
                    "text-sm text-gray-500"
                )

            with ui.pagination(
                current_page["value"],
                1,
                total_pages,
                on_change=lambda e: on_page_change(e.value),
            ).props("boundary-links")


def render():
    """Render the announcements page"""
    create_announcements_page()
