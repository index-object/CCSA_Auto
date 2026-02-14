from nicegui import ui


class Header:
    def __init__(self, title: str = "仪表盘"):
        self.title = title

    def render(self):
        with ui.row().classes("w-full bg-white p-4 items-center justify-between"):
            with ui.row().classes("items-center"):
                ui.label(self.title).classes("text-2xl font-bold")

            with ui.row().classes("items-center gap-2"):
                ui.button(icon="refresh", on_click=self.on_refresh).props("flat round")
                ui.button(icon="notifications", on_click=self.on_notifications).props(
                    "flat round"
                )
                with ui.button(icon="person").props("flat round"):
                    ui.label("管理员")
