from nicegui import ui
from typing import List, Optional

from ccsa_auto.admin_v2.services.user_service import UserService
from ccsa_auto.admin_v2.stores.admin_store import AdminStore
from ccsa_auto.admin_v2.components.ui.card import Card
from ccsa_auto.admin_v2.components.ui.button import Button
from ccsa_auto.admin_v2.components.ui.input import Input
from ccsa_auto.admin_v2.components.data.data_table import DataTable


def create_users_page():
    """Create the users management page"""
    # State
    keyword = {"value": ""}
    status_filter = {"value": None}  # None = all, 0 = normal, 1 = banned
    current_page = {"value": 1}
    page_size = {"value": 20}
    selected_users = {"value": []}
    users_data = {"data": [], "total": 0}
    selected_user_detail = {"data": None}

    def load_users():
        """Load users data"""
        result = UserService.get_users(
            keyword=keyword["value"] if keyword["value"] else None,
            status=status_filter["value"],
            page=current_page["value"],
            page_size=page_size["value"],
        )
        if result.get("success"):
            users_data["data"] = result.get("data", [])
            users_data["total"] = result.get("total", 0)
        else:
            ui.notify(f"加载用户失败: {result.get('message')}", type="negative")

    def on_search():
        """Handle search"""
        current_page["value"] = 1
        load_users()

    def on_status_filter(status: Optional[int]):
        """Handle status filter"""
        status_filter["value"] = status
        current_page["value"] = 1
        load_users()

    def on_page_change(page: int):
        """Handle page change"""
        current_page["value"] = page
        load_users()

    def on_page_size_change(size: int):
        """Handle page size change"""
        page_size["value"] = size
        current_page["value"] = 1
        load_users()

    def show_user_detail(user_id: int):
        """Show user detail sidebar"""
        result = UserService.get_user_detail(user_id)
        if result.get("success"):
            selected_user_detail["data"] = result.get("data")
            ui.notify(f"用户详情已加载", type="info")
        else:
            ui.notify(f"加载用户详情失败: {result.get('message')}", type="negative")

    def toggle_user_status(user_id: int, current_status: int):
        """Toggle user status (ban/unban)"""
        new_status = 1 if current_status == 0 else 0
        action = "封禁" if new_status == 1 else "解封"

        result = UserService.batch_update_status([user_id], new_status)
        if result.get("success"):
            ui.notify(f"用户{action}成功", type="positive")
            load_users()
        else:
            ui.notify(f"操作失败: {result.get('message')}", type="negative")

    def delete_user(user_id: int):
        """Delete user"""
        result = UserService.delete_user(user_id)
        if result.get("success"):
            ui.notify("用户删除成功", type="positive")
            load_users()
        else:
            ui.notify(f"删除失败: {result.get('message')}", type="negative")

    def batch_ban():
        """Batch ban selected users"""
        if not selected_users["value"]:
            ui.notify("请先选择用户", type="warning")
            return

        result = UserService.batch_update_status(selected_users["value"], 1)
        if result.get("success"):
            ui.notify(f"批量封禁成功", type="positive")
            selected_users["value"] = []
            load_users()
        else:
            ui.notify(f"操作失败: {result.get('message')}", type="negative")

    def batch_unban():
        """Batch unban selected users"""
        if not selected_users["value"]:
            ui.notify("请先选择用户", type="warning")
            return

        result = UserService.batch_update_status(selected_users["value"], 0)
        if result.get("success"):
            ui.notify(f"批量解封成功", type="positive")
            selected_users["value"] = []
            load_users()
        else:
            ui.notify(f"操作失败: {result.get('message')}", type="negative")

    # Initial load
    load_users()

    # Toolbar
    with ui.card().classes("p-4 mb-4"):
        with ui.row().classes("items-center gap-4 w-full"):
            # Search
            with ui.row().classes("items-center gap-2 flex-1"):
                ui.input(
                    "搜索用户名/姓名/公司",
                    value=keyword["value"],
                    on_change=lambda e: keyword.update(value=e.value),
                    on_enter=on_search,
                ).props("outlined dense clearable").classes("w-64")
                ui.button("搜索", on_click=on_search).props("flat color=primary")

            # Filter buttons
            with ui.row().classes("items-center gap-2"):
                ui.button(
                    "全部",
                    on_click=lambda: on_status_filter(None),
                ).props(
                    f"flat {'color=primary' if status_filter['value'] is None else ''}"
                )
                ui.button(
                    "正常",
                    on_click=lambda: on_status_filter(0),
                ).props(
                    f"flat {'color=positive' if status_filter['value'] == 0 else ''}"
                )
                ui.button(
                    "封号",
                    on_click=lambda: on_status_filter(1),
                ).props(
                    f"flat {'color=negative' if status_filter['value'] == 1 else ''}"
                )

            # Batch actions
            with ui.row().classes("items-center gap-2"):
                ui.button("批量封禁", on_click=batch_ban, icon="block").props(
                    "flat color=negative"
                )
                ui.button("批量解封", on_click=batch_unban, icon="check_circle").props(
                    "flat color=positive"
                )

    # Users table
    def render_status_badge(status: int) -> str:
        """Render status badge"""
        if status == 0:
            return '<span class="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">正常</span>'
        else:
            return '<span class="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs">封号</span>'

    with ui.card().classes("p-4"):
        # Table header
        with ui.row().classes("font-bold border-b pb-2 mb-2"):
            with ui.column().classes("w-12"):
                ui.label("ID")
            with ui.column().classes("flex-1"):
                ui.label("用户名")
            with ui.column().classes("w-24"):
                ui.label("姓名")
            with ui.column().classes("w-32"):
                ui.label("公司")
            with ui.column().classes("w-20"):
                ui.label("状态")
            with ui.column().classes("w-32"):
                ui.label("注册时间")
            with ui.column().classes("w-40"):
                ui.label("操作")

        # Table rows
        for user in users_data["data"]:
            with ui.row().classes("border-b py-2 hover:bg-gray-50 items-center"):
                with ui.column().classes("w-12"):
                    ui.label(str(user.get("id", "")))
                with ui.column().classes("flex-1"):
                    ui.label(str(user.get("username", "")))
                with ui.column().classes("w-24"):
                    ui.label(str(user.get("name") or "-"))
                with ui.column().classes("w-32"):
                    ui.label(str(user.get("company_name") or "-"))
                with ui.column().classes("w-20"):
                    if user.get("status") == 0:
                        ui.badge("正常", color="positive")
                    else:
                        ui.badge("封号", color="negative")
                with ui.column().classes("w-32"):
                    ui.label(str(user.get("created_at", "")))
                with ui.column().classes("w-40"):
                    with ui.row().classes("gap-1"):
                        ui.button(
                            "查看",
                            on_click=lambda u=user: show_user_detail(u.get("id")),
                            icon="visibility",
                        ).props("flat dense size=sm")
                        ui.button(
                            "封禁" if user.get("status") == 0 else "解封",
                            on_click=lambda u=user: toggle_user_status(
                                u.get("id"), u.get("status")
                            ),
                            icon="block" if user.get("status") == 0 else "check_circle",
                        ).props("flat dense size=sm")
                        ui.button(
                            "删除",
                            on_click=lambda u=user: delete_user(u.get("id")),
                            icon="delete",
                        ).props("flat dense size=sm color=negative")

        # Pagination
        total_pages = max(
            1, (users_data["total"] + page_size["value"] - 1) // page_size["value"]
        )
        with ui.row().classes("items-center justify-between w-full mt-4"):
            with ui.row().classes("items-center gap-2"):
                ui.label(f"共 {users_data['total']} 条").classes(
                    "text-sm text-gray-500"
                )

            pagination = ui.pagination(
                current_page["value"],
                1,
                total_pages,
                on_change=lambda e: on_page_change(e.value),
            )
            pagination.props("boundary-links")


def render():
    """Render the users page"""
    create_users_page()
