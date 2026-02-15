from nicegui import ui
from typing import List, Optional, Dict, Any

from ccsa_auto.admin_v2.services.user_service import UserService
from ccsa_auto.admin_v2.stores.admin_store import AdminStore


def create_users_page():
    keyword: Dict[str, str] = {"value": ""}
    status_filter: Dict[str, Optional[int]] = {"value": None}
    current_page: Dict[str, int] = {"value": 1}
    page_size: Dict[str, int] = {"value": 20}
    selected_users: Dict[str, List[int]] = {"value": []}
    users_data: Dict[str, Any] = {"data": [], "total": 0}
    selected_user_detail: Dict[str, Any] = {"data": None}

    def load_users():
        kw = keyword["value"] if keyword["value"] else None
        st = status_filter["value"]
        result = UserService.get_users(
            keyword=kw,
            status=st,
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

    load_users()

    with ui.row().classes("items-center justify-between w-full mb-6"):
        ui.label("用户管理").classes("text-2xl font-semibold text-[#1f2937]")

        with ui.row().classes("items-center gap-3"):
            with ui.element("div").classes(
                "flex items-center gap-2 bg-white rounded-lg px-4 py-2 border border-gray-200"
            ):
                ui.icon("search").classes("text-[#9ca3af]")
                search_input = ui.input(placeholder="搜索用户...")
                search_input.classes(
                    "border-none outline-none bg-transparent text-sm w-48"
                )
                search_input.bind_value(keyword, "value")
                search_input.on("keydown.enter", on_search)

            add_btn = (
                ui.button()
                .classes(
                    "bg-[#10b981] hover:bg-[#059669] text-white rounded-lg px-4 py-2 "
                    "flex items-center gap-2 transition-colors"
                )
                .props("flat no-caps")
            )
            add_btn.on_click(lambda _: ui.notify("添加用户功能开发中", type="info"))
            with add_btn:
                ui.icon("add").classes("text-white")
                ui.label("添加用户").classes("text-sm font-medium text-white")

    with ui.card().classes("rounded-2xl p-6 shadow-sm bg-white flex flex-col"):
        with ui.row().classes(
            "grid grid-cols-6 gap-4 pb-4 border-b border-gray-100 mb-4 shrink-0"
        ):
            ui.label("用户ID").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("用户名").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("邮箱").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("状态").classes("text-xs font-semibold text-[#6b7280] uppercase")
            ui.label("注册时间").classes(
                "text-xs font-semibold text-[#6b7280] uppercase"
            )
            ui.label("操作").classes("text-xs font-semibold text-[#6b7280] uppercase")

        with ui.element("div").classes("overflow-y-auto max-h-[calc(100vh-380px)]"):
            for idx, user in enumerate(users_data["data"]):
                row_bg = "bg-[#f9fafb]" if idx % 2 == 1 else "bg-white"

                with ui.row().classes(
                    f"grid grid-cols-6 gap-4 py-4 {row_bg} items-center"
                ):
                    ui.label(str(user.get("id", ""))).classes(
                        "text-sm text-[#1f2937] font-medium"
                    )
                    ui.label(str(user.get("username", ""))).classes(
                        "text-sm text-[#1f2937]"
                    )
                    ui.label(str(user.get("email") or "-")).classes(
                        "text-sm text-[#6b7280]"
                    )

                    if user.get("status") == 0:
                        with ui.element("span").classes(
                            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#d1fae5] text-[#059669] w-fit"
                        ):
                            ui.label("正常")
                    else:
                        with ui.element("span").classes(
                            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#fee2e2] text-[#dc2626] w-fit"
                        ):
                            ui.label("禁用")

                    ui.label(str(user.get("created_at", ""))).classes(
                        "text-sm text-[#6b7280]"
                    )

                    with ui.row().classes("items-center gap-2"):
                        user_id_val = user.get("id")
                        user_status_val = user.get("status")

                        edit_btn = (
                            ui.button()
                            .classes(
                                "text-[#6b7280] hover:text-[#10b981] hover:bg-[#ecfdf5] rounded p-1 transition-colors"
                            )
                            .props("flat dense")
                        )
                        edit_btn.on_click(
                            lambda _, uid=user_id_val: show_user_detail(uid)
                        )
                        with edit_btn:
                            ui.icon("edit").classes("text-base")

                        status_btn = (
                            ui.button()
                            .classes(
                                "text-[#6b7280] hover:text-amber-500 hover:bg-amber-50 rounded p-1 transition-colors"
                            )
                            .props("flat dense")
                        )
                        status_btn.on_click(
                            lambda _,
                            uid=user_id_val,
                            st=user_status_val: toggle_user_status(uid, st)
                        )
                        with status_btn:
                            icon_name = (
                                "block" if user_status_val == 0 else "check_circle"
                            )
                            ui.icon(icon_name).classes("text-base")

                        delete_btn = (
                            ui.button()
                            .classes(
                                "text-[#6b7280] hover:text-[#ef4444] hover:bg-[#fef2f2] rounded p-1 transition-colors"
                            )
                            .props("flat dense")
                        )
                    delete_btn.on_click(lambda _, uid=user_id_val: delete_user(uid))
                    with delete_btn:
                        ui.icon("delete").classes("text-base")

    total_pages = max(
        1, (users_data["total"] + page_size["value"] - 1) // page_size["value"]
    )

    with ui.row().classes("items-center justify-between mt-6"):
        ui.label(
            f"共 {users_data['total']} 条记录，第 {current_page['value']}/{total_pages} 页"
        ).classes("text-sm text-[#6b7280]")

        with ui.row().classes("items-center gap-2"):
            prev_btn = (
                ui.button()
                .classes(
                    "px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-[#6b7280] "
                    "hover:bg-gray-50"
                )
                .props("flat")
            )
            prev_btn.on_click(
                lambda _: on_page_change(max(1, current_page["value"] - 1))
            )
            with prev_btn:
                ui.icon("chevron_left").classes("text-base")

            for page_num in range(1, min(total_pages + 1, 6)):
                is_active = page_num == current_page["value"]
                active_class = (
                    "bg-[#10b981] text-white"
                    if is_active
                    else "border border-gray-200 text-[#6b7280] hover:bg-gray-50"
                )
                page_btn = (
                    ui.button()
                    .classes(
                        f"px-3 py-1.5 rounded-lg text-sm font-medium {active_class}"
                    )
                    .props("flat")
                )
                page_btn.on_click(lambda _, p=page_num: on_page_change(p))
                with page_btn:
                    ui.label(str(page_num)).classes("text-sm")

            next_btn = (
                ui.button()
                .classes(
                    "px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-[#6b7280] "
                    "hover:bg-gray-50"
                )
                .props("flat")
            )
            next_btn.on_click(
                lambda _: on_page_change(min(total_pages, current_page["value"] + 1))
            )
            with next_btn:
                ui.icon("chevron_right").classes("text-base")


def render():
    """Render the users page"""
    create_users_page()
