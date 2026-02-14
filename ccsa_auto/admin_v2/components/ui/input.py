from nicegui import ui
from typing import Callable, Optional


class Input:
    def __init__(
        self,
        label: str = None,
        placeholder: str = None,
        on_change: Optional[Callable] = None,
        value=None,
    ):
        self.label = label
        self.placeholder = placeholder
        self.on_change = on_change
        self.value = value

    def render(self):
        if self.label:
            return ui.input(
                label=self.label,
                placeholder=self.placeholder,
                on_change=self.on_change,
                value=self.value,
            ).classes("rounded-xl w-full")
        else:
            return ui.input(
                placeholder=self.placeholder, on_change=self.on_change, value=self.value
            ).classes("rounded-xl w-full")
