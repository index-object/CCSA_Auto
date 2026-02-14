from nicegui import ui
from typing import Callable, Optional

from ccsa_auto.admin_v2.components.layout.sidebar import Sidebar


class AdminLayout:
    def __init__(
        self, render_content: Optional[Callable] = None, title: str = "Dashboard"
    ):
        self.sidebar = Sidebar()
        self.render_content = render_content
        self.title = title

    def render(self):
        with ui.row().classes("w-full h-screen"):
            self.sidebar.render()

            with ui.column().classes("flex-1 bg-gray-100 overflow-auto"):
                with ui.row().classes("w-full bg-white p-4 items-center shadow"):
                    ui.label(self.title).classes("text-2xl font-bold")

                with ui.column().classes("w-full p-6"):
                    if self.render_content:
                        self.render_content()
                    else:
                        ui.label("Content").classes("text-gray-600")
