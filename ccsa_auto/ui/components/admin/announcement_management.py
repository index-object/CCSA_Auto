from nicegui import ui
from ccsa_auto.modules.announcement.service import AnnouncementService
from ccsa_auto.ui.components.admin.common import (
    PageHeader,
    LoadingOverlay,
    ConfirmDialog,
    Toast,
)


def create_announcement_management():
    """创建公告管理页面"""
    loading = LoadingOverlay("加载公告数据中...")

    header = PageHeader(
        title="公告管理",
        subtitle="发布和管理系统公告",
        icon="campaign",
    )
    header.render()

    with ui.card().classes(
        "w-full p-6 mb-6 bg-white rounded-2xl border border-gray-200 shadow-sm"
    ):
        with ui.row().classes("items-center justify-between mb-4"):
            with ui.row().classes("items-center gap-3"):
                with ui.row().classes(
                    "w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 "
                    "flex items-center justify-center shadow-lg shadow-blue-200"
                ):
                    ui.icon("edit_note").classes("w-5 h-5 text-white")
                ui.label("发布公告").classes("text-xl font-bold text-gray-800")

        with ui.row().classes("w-full gap-4"):
            title_input = ui.input("标题").classes(
                "flex-1 px-4 py-3 bg-gray-50 border border-gray-200 "
                "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 "
                "focus:border-blue-400 transition-all placeholder:text-gray-400 text-gray-700 text-lg"
            )

        content_input = ui.textarea("内容").classes(
            "w-full h-40 px-4 py-3 bg-gray-50 border border-gray-200 "
            "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 "
            "focus:border-blue-400 transition-all resize-none text-gray-700 mt-4 text-lg"
        )

        with ui.row().classes("gap-3 mt-5"):
            publish_btn = ui.button("发布公告", icon="send").classes(
                "bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 "
                "transition-all duration-200 shadow-lg shadow-blue-200 hover:shadow-blue-300 "
                "font-medium text-lg"
            )
            save_btn = ui.button("保存修改", icon="save").classes(
                "bg-emerald-600 text-white px-6 py-3 rounded-xl hover:bg-emerald-700 "
                "transition-all duration-200 shadow-lg shadow-emerald-200 hover:shadow-emerald-300 "
                "font-medium text-lg"
            )
            clear_btn = ui.button("清空", icon="clear").classes(
                "bg-white text-gray-700 px-6 py-3 rounded-xl border-2 border-gray-200 "
                "hover:border-blue-400 hover:text-blue-600 transition-all duration-200 "
                "font-medium text-lg"
            )

    with ui.card().classes(
        "w-full bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden"
    ):
        with ui.row().classes(
            "items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50"
        ):
            with ui.row().classes("items-center gap-3"):
                with ui.row().classes(
                    "w-10 h-10 rounded-xl bg-gradient-to-br from-gray-100 to-gray-200 "
                    "flex items-center justify-center"
                ):
                    ui.icon("list").classes("w-5 h-5 text-gray-600")
                ui.label("公告列表").classes("text-xl font-bold text-gray-800")
            refresh_list_btn = (
                ui.button(icon="refresh")
                .classes(
                    "p-2.5 rounded-xl hover:bg-blue-50 hover:text-blue-600 "
                    "text-gray-500 transition-all duration-200"
                )
                .props("flat round size='sm'")
            )

        announcement_table = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id", "align": "center"},
                {"name": "title", "label": "标题", "field": "title"},
                {"name": "content", "label": "内容", "field": "content"},
                {"name": "created_at", "label": "发布时间", "field": "created_at"},
                {
                    "name": "actions",
                    "label": "操作",
                    "field": "actions",
                    "align": "center",
                },
            ],
            rows=[],
            row_key="id",
        ).classes("w-full")

    editing_id = [None]

    def refresh_announcements():
        loading.show()
        try:
            result = AnnouncementService.get_announcements()
            if result["success"]:
                announcements = result["announcements"]
                announcement_table.rows = announcements
            else:
                Toast.error(result.get("message", "获取公告列表失败"))
        except Exception as e:
            Toast.error(f"加载失败: {str(e)}")
        finally:
            loading.close()

    def create_announcement():
        title = title_input.value
        content = content_input.value
        if title and content:
            result = AnnouncementService.create_announcement(title, content)
            if result["success"]:
                Toast.success("公告发布成功")
                clear_form()
                refresh_announcements()
            else:
                Toast.error(result["message"])
        else:
            Toast.warning("标题和内容不能为空")

    def update_announcement():
        if not editing_id[0]:
            return
        title = title_input.value
        content = content_input.value
        if title and content:
            result = AnnouncementService.update_announcement(
                editing_id[0], title, content
            )
            if result["success"]:
                Toast.success("公告更新成功")
                clear_form()
                refresh_announcements()
            else:
                Toast.error(result["message"])
        else:
            Toast.warning("标题和内容不能为空")

    def edit_handler(row):
        title_input.value = row["title"]
        editing_id[0] = row["id"]
        content_input.value = row.get("content", "")
        Toast.info(f"正在编辑: {row['title']}")

    def delete_handler(row):
        ConfirmDialog(
            title="删除公告",
            message=f"确定要删除公告「{row['title']}」吗？此操作不可恢复。",
            confirm_text="删除",
            confirm_color="red",
            on_confirm=lambda: execute_delete(row["id"]),
        ).show()

    def execute_delete(announcement_id: int):
        result = AnnouncementService.delete_announcement(announcement_id)
        if result["success"]:
            Toast.success("公告删除成功")
            refresh_announcements()
        else:
            Toast.error(result["message"])

    def clear_form():
        title_input.value = ""
        content_input.value = ""
        editing_id[0] = None

    publish_btn.on("click", create_announcement)
    save_btn.on("click", update_announcement)
    clear_btn.on("click", clear_form)
    refresh_list_btn.on("click", refresh_announcements)

    refresh_announcements()
