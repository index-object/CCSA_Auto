from nicegui import ui
from typing import Callable, Optional


class Button:
    def __init__(
        self,
        text: str,
        on_click: Optional[Callable] = None,
        color: str = "primary",
        icon: Optional[str] = None,
    ):
        self.text = text
        self.on_click = on_click
        self.color = color
        self.icon = icon

    def render(self):
        props = {"color": self.color}
        if self.on_click:
            props["on_click"] = self.on_click

        if self.icon:
            with ui.button(props=props).classes("rounded-xl"):
                ui.icon(self.icon)
                ui.label(self.text)
        else:
            return ui.button(self.text, props=props).classes("rounded-xl px-6 py-3")
