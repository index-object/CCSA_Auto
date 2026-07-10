from nicegui import ui


class Card:
    def __init__(self, title: str = None):
        self.title = title

    def render(self):
        with ui.card().classes("rounded-2xl p-6"):
            if self.title:
                ui.label(self.title).classes("text-lg font-bold mb-4")
