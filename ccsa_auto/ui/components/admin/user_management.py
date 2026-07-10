from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService
from ccsa_auto.ui.components.admin.common import (
    PageHeader,
    LoadingOverlay,
    ConfirmDialog,
    Toast,
)


def create_user_management():
    """创建用户管理页面"""
    loading = LoadingOverlay("加载用户数据中...")

    header = PageHeader(
        title="用户管理",
        subtitle="管理系统用户账户和权限状态",
        icon="people",
    )
    header.render()

    with ui.row().classes(
        "items-center gap-4 p-5 bg-white rounded-2xl border border-gray-200 "
        "shadow-sm mb-6 flex-wrap"
    ):
        keyword_input = ui.input("搜索账号/姓名/公司").classes(
            "flex-1 min-w-[250px] px-4 py-3 bg-gray-50 border border-gray-200 "
            "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 "
            "focus:border-blue-400 transition-all placeholder:text-gray-400 text-gray-700 text-lg"
        )
        status_select = ui.select(
            {None: "全部状态", 0: "正常", 1: "封号"},
            label="状态",
            value=None,
        ).classes(
            "w-36 px-4 py-3 bg-gray-50 border border-gray-200 "
            "rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-lg"
        )

        search_btn = ui.button("搜索", icon="search").classes(
            "bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 "
            "transition-all duration-200 shadow-lg shadow-blue-200 hover:shadow-blue-300 "
            "font-medium text-lg"
        )
        refresh_btn = ui.button("刷新", icon="refresh").classes(
            "bg-white text-gray-700 px-6 py-3 rounded-xl border-2 border-gray-200 "
            "hover:border-blue-400 hover:text-blue-600 transition-all duration-200 "
            "font-medium text-lg"
        )

    user_table = ui.table(
        columns=[
            {
                "name": "id",
                "label": "ID",
                "field": "id",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "username",
                "label": "账号",
                "field": "username",
                "sortable": True,
            },
            {"name": "name", "label": "姓名", "field": "name", "sortable": True},
            {"name": "company_name", "label": "公司", "field": "company_name"},
            {
                "name": "status",
                "label": "状态",
                "field": "status",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "created_at",
                "label": "创建时间",
                "field": "created_at",
                "sortable": True,
            },
        ],
        rows=[],
        row_key="id",
        selection="multiple",
    ).classes(
        "w-full bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden"
    )

    with ui.row().classes(
        "items-center gap-4 mt-5 p-4 bg-blue-50 rounded-2xl border border-blue-100"
    ):
        with ui.row().classes(
            "w-10 h-10 rounded-xl bg-blue-500 flex items-center justify-center"
        ):
            ui.icon("info").classes("w-5 h-5 text-white")
        ui.label("批量操作").classes("text-blue-800 font-bold text-base")
        ui.separator().classes("h-8 w-px bg-blue-300")
        ban_btn = ui.button("批量封禁").classes(
            "bg-red-600 text-white px-5 py-2.5 rounded-xl hover:bg-red-700 "
            "transition-all duration-200 text-base font-medium shadow-lg shadow-red-200"
        )
        unban_btn = ui.button("批量解封").classes(
            "bg-emerald-600 text-white px-5 py-2.5 rounded-xl hover:bg-emerald-700 "
            "transition-all duration-200 text-base font-medium shadow-lg shadow-emerald-200"
        )

    def refresh_users():
        loading.show()
        try:
            result = AdminService.get_users(
                keyword=keyword_input.value or "",
                status=status_select.value if status_select.value is not None else None,
            )
            if result["success"]:
                users = result["users"]
                for user in users:
                    user["status"] = "正常" if user["status"] == 0 else "封号"
                user_table.rows = users
            else:
                Toast.error(result.get("message", "获取用户列表失败"))
        except Exception as e:
            Toast.error(f"加载失败: {str(e)}")
        finally:
            loading.close()

    def batch_update_status(status: int):
        selected = user_table.selected
        if not selected:
            Toast.warning("请先选择用户")
            return

        user_ids = [row["id"] for row in selected]
        action_text = "封禁" if status == 1 else "解封"

        ConfirmDialog(
            title=f"确认{action_text}",
            message=f"确定要{action_text}选中的 {len(user_ids)} 个用户吗？",
            confirm_text=action_text,
            confirm_color="red" if status == 1 else "green",
            on_confirm=lambda: execute_batch_update(user_ids, status),
        ).show()

    def execute_batch_update(user_ids: list, status: int):
        result = AdminService.batch_update_user_status(user_ids, status)
        if result["success"]:
            Toast.success(result["message"])
            refresh_users()
        else:
            Toast.error(result["message"])

    search_btn.on("click", refresh_users)
    refresh_btn.on("click", refresh_users)
    ban_btn.on("click", lambda: batch_update_status(1))
    unban_btn.on("click", lambda: batch_update_status(0))

    refresh_users()
