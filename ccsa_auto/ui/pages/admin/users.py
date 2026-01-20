from nicegui import ui
from typing import List
from ccsa_auto.ui.components.admin import (
    admin_sidebar,
    breadcrumb,
    confirm_dialog,
    AdminInput,
    AdminSelect,
    AdminButton,
    AdminTable,
)


@ui.page("/admin/users")
def admin_users():
    def refresh_users():
        ui.notify("用户列表已刷新", type="positive")

    def export_users():
        ui.notify("正在导出用户数据...", type="info")

    def ban_user(user_id: int, username: str):
        ui.notify(f"用户 {username} 已被封禁", type="warning")

    def unban_user(user_id: int, username: str):
        ui.notify(f"用户 {username} 已解封", type="positive")

    def show_ban_confirm(user_id: int, username: str):
        confirm_dialog(
            title="确认封禁用户",
            message=f"确定要封禁用户 [{username}] 吗？封禁后该用户将无法登录系统。",
            confirm_text="确认封禁",
            destructive=True,
            on_confirm=lambda: ban_user(user_id, username),
        )

    users_data = [
        {
            "id": 1,
            "username": "zhangsan",
            "company": "ABC科技有限公司",
            "status": "normal",
            "created_at": "2024-01-15",
            "last_login": "2024-01-17 10:23",
        },
        {
            "id": 2,
            "username": "lisi",
            "company": "XYZ信息技术",
            "status": "banned",
            "created_at": "2024-01-14",
            "last_login": "2024-01-16 14:30",
        },
        {
            "id": 3,
            "username": "wangwu",
            "company": "123集团",
            "status": "normal",
            "created_at": "2024-01-13",
            "last_login": "2024-01-17 09:15",
        },
        {
            "id": 4,
            "username": "zhaoliu",
            "company": "测试企业",
            "status": "normal",
            "created_at": "2024-01-12",
            "last_login": "2024-01-17 08:45",
        },
        {
            "id": 5,
            "username": "qianqi",
            "company": "开发工作室",
            "status": "pending",
            "created_at": "2024-01-11",
            "last_login": None,
        },
    ]

    def get_status_info(status: str):
        status_map = {
            "normal": ("正常", "text-green-400", "bg-green-500/20"),
            "banned": ("已封禁", "text-red-400", "bg-red-500/20"),
            "pending": ("待审核", "text-amber-400", "bg-amber-500/20"),
        }
        return status_map.get(status, ("未知", "text-slate-400", "bg-slate-500/20"))

    columns = [
        {"name": "id", "label": "ID", "field": "id", "align": "center"},
        {"name": "username", "label": "用户名", "field": "username"},
        {"name": "company", "label": "公司", "field": "company"},
        {"name": "status", "label": "状态", "field": "status", "align": "center"},
        {"name": "created_at", "label": "创建时间", "field": "created_at"},
        {"name": "last_login", "label": "最后登录", "field": "last_login"},
        {"name": "actions", "label": "操作", "field": "actions", "align": "center"},
    ]

    def create_status_badge(status: str):
        label, text_color, bg_color = get_status_info(status)
        with ui.row().classes(
            f"items-center justify-center {bg_color} px-2 py-0.5 rounded-full"
        ):
            ui.label(label).classes(f"text-xs font-medium {text_color}")

    def create_action_buttons(user: dict):
        with ui.row().classes("items-center gap-1"):
            AdminButton.icon_sm("edit", tooltip="编辑").classes("p-1")
            if user["status"] == "banned":
                AdminButton.icon_sm(
                    "check",
                    on_click=lambda u=user: unban_user(u["id"], u["username"]),
                    tooltip="解封",
                ).classes("p-1 text-green-400")
            else:
                AdminButton.icon_sm(
                    "block",
                    on_click=lambda u=user: show_ban_confirm(u["id"], u["username"]),
                    tooltip="封禁",
                ).classes("p-1 text-red-400")

    table_rows = []
    for user in users_data:
        row = {
            "id": user["id"],
            "username": user["username"],
            "company": user["company"],
            "status": "",
            "created_at": user["created_at"],
            "last_login": user["last_login"] or "从未登录",
            "actions": "",
        }
        table_rows.append(row)

    with ui.row().classes("w-full h-screen bg-slate-900 overflow-hidden"):
        admin_sidebar("/admin/users")

        with ui.column().classes("flex-1 h-full"):
            with ui.row().classes(
                "items-center justify-between px-8 py-6 border-b border-slate-700 bg-slate-900 flex-shrink-0"
            ):
                with ui.column():
                    breadcrumb(
                        [
                            {"label": "首页", "route": "/admin"},
                            {"label": "用户管理"},
                        ]
                    )
                    ui.label("用户管理").classes("text-2xl font-bold text-white mt-2")

                from ccsa_auto.ui.components.admin.toolbar import toolbar

                toolbar(
                    search_placeholder="搜索用户名/公司...",
                    filters=["全部", "正常", "已封禁", "待审核"],
                    actions=[
                        {
                            "icon": "refresh",
                            "on_click": refresh_users,
                            "style": "secondary",
                        },
                        {
                            "icon": "download",
                            "text": "导出",
                            "on_click": export_users,
                            "primary": True,
                        },
                    ],
                ).render()

            with ui.column().classes("flex-1 overflow-y-auto"):
                with ui.column().classes("w-full p-6"):
                    AdminTable.card(
                        columns=columns,
                        rows=table_rows,
                        title="用户列表",
                        searchable=False,
                        actions=[
                            {
                                "icon": "refresh",
                                "label": "刷新",
                                "on_click": refresh_users,
                            },
                            {
                                "icon": "download",
                                "label": "导出",
                                "on_click": export_users,
                                "primary": True,
                            },
                        ],
                        pagination={
                            "page": 1,
                            "per_page": 20,
                            "total": len(users_data),
                        },
                    )
