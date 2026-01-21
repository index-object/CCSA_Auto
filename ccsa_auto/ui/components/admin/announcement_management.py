from nicegui import ui
from ccsa_auto.modules.announcement.service import AnnouncementService
from ccsa_auto.ui.components.admin.common import (
    PageHeader,
    LoadingOverlay,
    ConfirmDialog,
    Toast,
)


def create_announcement_management():
    """创建公告管理页面 - 现代化增强版"""
    loading = LoadingOverlay("加载公告数据中...")

    # 页面标题
    header = PageHeader(
        title="公告管理",
        subtitle="发布和管理系统公告",
        icon="campaign",
    )
    header.render()

    # 发布/编辑表单
    with ui.card().classes(
        "w-full p-6 mb-6 bg-white rounded-xl border border-gray-200 shadow-sm"
    ):
        ui.label("发布公告").classes("text-lg font-semibold text-gray-800 mb-4")

        with ui.row().classes("w-full gap-4"):
            title_input = ui.input("标题").classes(
                "flex-1 px-4 py-2.5 bg-gray-50 border border-gray-200 "
                "rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            )

        content_input = ui.textarea("内容").classes(
            "w-full h-32 px-4 py-2.5 bg-gray-50 border border-gray-200 "
            "rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 mt-4"
        )

        with ui.row().classes("gap-3 mt-4"):
            publish_btn = ui.button("发布公告").classes(
                "bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            )
            save_btn = ui.button("保存修改").classes(
                "bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
            )
            clear_btn = ui.button("清空").classes(
                "bg-gray-100 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-200 transition-colors"
            )

    # 公告列表
    with ui.card().classes(
        "w-full bg-white rounded-xl border border-gray-200 shadow-sm"
    ):
        with ui.row().classes(
            "items-center justify-between px-4 py-3 border-b border-gray-200"
        ):
            ui.label("公告列表").classes("text-lg font-semibold text-gray-800")
            refresh_list_btn = (
                ui.button(icon="refresh")
                .classes(
                    "p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
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

    # 状态变量
    editing_id = [None]

    # 定义函数
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

    # 绑定事件
    publish_btn.on("click", create_announcement)
    save_btn.on("click", update_announcement)
    clear_btn.on("click", clear_form)
    refresh_list_btn.on("click", refresh_announcements)

    # 初始加载
    refresh_announcements()
