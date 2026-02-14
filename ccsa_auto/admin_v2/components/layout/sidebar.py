from nicegui import ui


class Sidebar:
    def __init__(self):
        self.collapsed = False
        self.menu_items = [
            {"label": "数据概览", "icon": "dashboard", "path": "/admin_v2"},
            {"label": "用户管理", "icon": "people", "path": "/admin_v2/users"},
            {"label": "任务管理", "icon": "task", "path": "/admin_v2/tasks"},
            {
                "label": "公告管理",
                "icon": "campaign",
                "path": "/admin_v2/announcements",
            },
            {"label": "操作日志", "icon": "history", "path": "/admin_v2/logs"},
            {"label": "系统设置", "icon": "settings", "path": "/admin_v2/settings"},
        ]

    def render(self):
        width = "w-16" if self.collapsed else "w-64"
        with ui.column().classes(f"{width} bg-gray-900 text-white h-full"):
            with ui.row().classes("w-full justify-between items-center p-4"):
                if not self.collapsed:
                    ui.label("CCSA Auto").classes("text-xl font-bold")
                ui.button(icon="menu", on_click=self.toggle).props(
                    "flat color=white"
                ).classes("text-white")

            ui.separator()

            for item in self.menu_items:
                with (
                    ui.button(on_click=lambda p=item["path"]: ui.navigate.to(p))
                    .props("flat")
                    .classes("w-full justify-start p-4 text-white")
                ):
                    ui.icon(item["icon"]).classes("mr-2")
                    if not self.collapsed:
                        ui.label(item["label"])

            with ui.column().classes("mt-auto p-4"):
                if not self.collapsed:
                    ui.label("v1.0.0").classes("text-gray-500 text-sm")

    def toggle(self):
        self.collapsed = not self.collapsed
