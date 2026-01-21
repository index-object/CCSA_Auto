from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService


def create_user_management():
    with ui.column().classes("w-full"):
        with ui.row().classes("items-center gap-4 mb-4"):
            keyword_input = ui.input("搜索账号/公司").classes("w-48")
            status_select = ui.select(
                {None: "全部", 0: "正常", 1: "封号"}, label="状态", value=None
            ).classes("w-32")

        user_table = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id", "align": "center"},
                {"name": "username", "label": "账号", "field": "username"},
                {
                    "name": "name",
                    "label": "姓名",
                    "field": "name",
                },
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
                status=status_select.value if status_select.value is not None else None,
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

        with ui.row().classes("gap-3 mt-4"):
            ui.button("搜索", on_click=refresh_users).classes(
                "bg-blue-600 text-white hover:bg-blue-700"
            )
            ui.button("刷新", on_click=refresh_users).classes(
                "bg-gray-200 text-gray-700 hover:bg-gray-300"
            )
            ui.button("批量封禁", on_click=lambda: batch_update_status(1)).classes(
                "bg-red-600 text-white hover:bg-red-700"
            )
            ui.button("批量解封", on_click=lambda: batch_update_status(0)).classes(
                "bg-green-600 text-white hover:bg-green-700"
            )

        refresh_users()
