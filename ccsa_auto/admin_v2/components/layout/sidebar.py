from nicegui import ui
from typing import Any


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

    def is_active(self, path: str) -> bool:
        current_url = ui.context.client.page.path
        if path == "/admin_v2":
            return current_url == path
        return current_url.startswith(path + "/")

    def render(self) -> None:
        width = "w-16" if self.collapsed else "w-[260px]"

        with ui.element("aside").classes(
            f"{width} h-full flex flex-col shrink-0 overflow-hidden "
            "bg-gradient-to-b from-[#065f46] to-[#064e3b]"
        ):
            with ui.row().classes(
                "items-center gap-3 px-6 py-6 border-b border-white/10"
            ):
                with ui.element("div").classes(
                    "w-10 h-10 bg-[#10b981] rounded-lg flex items-center justify-center shrink-0"
                ):
                    ui.icon("auto_awesome").classes("text-white text-xl")

                if not self.collapsed:
                    ui.label("CCSA Auto").classes("text-white text-xl font-semibold")

            with ui.column().classes("flex-1 px-4 py-4 gap-1 overflow-y-auto"):
                for item in self.menu_items:
                    is_item_active = self.is_active(item["path"])

                    bg_color = (
                        "bg-[#10b981]"
                        if is_item_active
                        else "bg-transparent hover:bg-white/5"
                    )
                    text_color = "text-white" if is_item_active else "text-[#a7f3d0]"
                    icon_color = "text-white" if is_item_active else "text-[#6ee7b7]"
                    item_path = item["path"]

                    btn = (
                        ui.button()
                        .classes(
                            f"w-full justify-start items-center gap-3 px-4 py-3 rounded-lg "
                            f"{bg_color} transition-colors duration-200"
                        )
                        .props("flat no-caps")
                    )
                    btn.on_click(lambda _, p=item_path: ui.navigate.to(p))
                    with btn:
                        ui.icon(item["icon"]).classes(f"{icon_color} text-lg shrink-0")
                        if not self.collapsed:
                            ui.label(item["label"]).classes(
                                f"{text_color} text-sm font-medium"
                            )

            with ui.row().classes("px-4 py-4 border-t border-white/10"):
                toggle_btn = (
                    ui.button(
                        icon="chevron_left" if not self.collapsed else "chevron_right"
                    )
                    .classes(
                        "text-white/70 hover:text-white hover:bg-white/10 rounded-lg w-full"
                    )
                    .props("flat dense")
                )
                toggle_btn.on_click(self.toggle)

    def toggle(self, _) -> None:
        self.collapsed = not self.collapsed
        ui.navigate.to(str(ui.context.client.page.path))
