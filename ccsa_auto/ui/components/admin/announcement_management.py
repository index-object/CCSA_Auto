from nicegui import ui
from ccsa_auto.modules.announcement.service import AnnouncementService


def create_announcement_management():
    with ui.column().classes("w-full"):
        with ui.card().classes("w-full p-4 mb-4"):
            ui.label("发布公告").classes("text-lg font-semibold text-gray-800 mb-3")
            title = ui.input("标题").classes("w-full mb-3")
            content = ui.textarea("内容").classes("w-full mb-3")

            with ui.row().classes("gap-3"):
                ui.button(
                    "发布公告",
                    on_click=lambda: create_announcement(
                        title.value,
                        content.value,
                        title,
                        content,
                        editing_id,
                        refresh_announcements,
                    ),
                ).classes("bg-blue-600 text-white hover:bg-blue-700")
                ui.button(
                    "保存修改",
                    on_click=lambda: update_announcement(
                        title.value,
                        content.value,
                        editing_id,
                        refresh_announcements,
                        title,
                        content,
                    ),
                ).classes("bg-green-600 text-white hover:bg-green-700")

        editing_id = [None]

        def create_announcement(t, c, title_input, content_input, eid, refresh):
            if t and c:
                result = AnnouncementService.create_announcement(t, c)
                if result["success"]:
                    ui.notify("公告发布成功", type="positive")
                    title_input.value = ""
                    content_input.value = ""
                    eid[0] = None
                    refresh()
                else:
                    ui.notify(result["message"], type="negative")
            else:
                ui.notify("标题和内容不能为空", type="warning")

        def update_announcement(t, c, eid, refresh, title_input, content_input):
            if not eid[0]:
                return
            if t and c:
                result = AnnouncementService.update_announcement(eid[0], t, c)
                if result["success"]:
                    ui.notify("公告更新成功", type="positive")
                    title_input.value = ""
                    content_input.value = ""
                    eid[0] = None
                    refresh()
                else:
                    ui.notify(result["message"], type="negative")
            else:
                ui.notify("标题和内容不能为空", type="warning")

        def refresh_announcements():
            result = AnnouncementService.get_announcements()
            if result["success"]:
                announcement_table.rows = result["announcements"]

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
        ).classes("w-full")

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

        with ui.row().classes("gap-3 mt-4"):
            ui.button("刷新列表", on_click=refresh_announcements).classes(
                "bg-gray-200 text-gray-700 hover:bg-gray-300"
            )

        refresh_announcements()
