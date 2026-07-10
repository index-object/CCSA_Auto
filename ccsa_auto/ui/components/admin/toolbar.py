from nicegui import ui
from typing import List, Dict, Callable, Optional
from .input import AdminInput, AdminSelect
from .button import AdminButton


class AdminToolbar:
    """统一工具栏组件"""

    def __init__(self, title: str = ""):
        self.title = title
        self.left_elements = []
        self.right_elements = []

    def add_search(
        self,
        placeholder: str = "搜索...",
        width: str = "w-64",
        on_change: Callable = None,
    ):
        self.left_elements.append(
            lambda: AdminInput.search(placeholder, width, on_change)
        )
        return self

    def add_select(
        self,
        options: List[str],
        value: str = None,
        width: str = "w-32",
        on_change: Callable = None,
    ):
        self.left_elements.append(lambda: AdminSelect.filter(options, value, on_change))
        return self

    def add_button(
        self,
        text: str = "",
        icon: str = None,
        on_click: Callable = None,
        style: str = "secondary",
        primary: bool = False,
    ):
        btn_map = {
            "primary": AdminButton.primary,
            "secondary": AdminButton.secondary,
            "danger": AdminButton.danger,
            "success": AdminButton.success,
        }
        method = btn_map.get(style, btn_map["secondary"])

        if primary:
            method = AdminButton.primary

        self.right_elements.append(lambda: method(text, icon, on_click))
        return self

    def add_icon_button(
        self, icon: str, on_click: Callable = None, tooltip: str = None
    ):
        self.right_elements.append(
            lambda: AdminButton.icon_only(icon, on_click, tooltip)
        )
        return self

    def add_divider(self):
        self.right_elements.append(
            lambda: ui.separator().classes("h-6 w-px bg-slate-600 mx-2")
        )
        return self

    def render(self):
        with ui.row().classes(
            "w-full items-center justify-between px-6 py-4 "
            "border-b border-slate-700 bg-slate-800/50"
        ):
            with ui.row().classes("items-center gap-4 flex-wrap"):
                if self.title:
                    ui.label(self.title).classes("text-white text-lg font-semibold")
                with ui.row().classes("items-center gap-3"):
                    for element in self.left_elements:
                        element()

            with ui.row().classes("items-center gap-2 flex-wrap"):
                for element in self.right_elements:
                    element()


def toolbar(
    title: str = "",
    search_placeholder: str = None,
    filters: List[str] = None,
    actions: List[Dict] = None,
):
    """快捷创建工具栏"""
    tb = AdminToolbar(title)

    if search_placeholder:
        tb.add_search(search_placeholder)

    if filters:
        tb.add_select(filters)

    if actions:
        for action in actions:
            tb.add_button(
                text=action.get("text", ""),
                icon=action.get("icon"),
                on_click=action.get("on_click"),
                style=action.get("style", "secondary"),
                primary=action.get("primary", False),
            )

    return tb
