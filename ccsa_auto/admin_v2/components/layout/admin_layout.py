from nicegui import ui


class AdminLayout:
    def __init__(self):
        self.sidebar = None
        self.header = None

    def render(self):
        with ui.row().classes("w-full h-screen"):
            with ui.column().classes("w-64 bg-gray-900 text-white"):
                ui.label("CCSA Auto").classes("text-xl font-bold p-4")
                ui.separator()

            with ui.column().classes("flex-1 bg-gray-100"):
                with ui.row().classes("w-full bg-white p-4 items-center"):
                    ui.label("Dashboard").classes("text-2xl font-bold")

                with ui.row().classes("w-full p-4"):
                    ui.label("Content").classes("text-gray-600")
