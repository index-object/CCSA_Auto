from nicegui import ui
from typing import Optional, Callable


class AdminButton:
    """统一风格按钮"""

    @staticmethod
    def primary(
        text: str = "", icon: str = None, on_click: Callable = None, width: str = None
    ):
        btn = ui.button(text=text, icon=icon, on_click=on_click)
        btn.classes(
            "bg-blue-600 hover:bg-blue-500 text-white font-medium "
            "rounded-lg px-4 py-2 transition-all duration-200 "
            "shadow-lg shadow-blue-500/20 "
            "hover:shadow-blue-500/30 "
            "disabled:opacity-50 disabled:cursor-not-allowed"
        )
        if width:
            btn.classes(width)
        return btn

    @staticmethod
    def secondary(text: str = "", icon: str = None, on_click: Callable = None):
        btn = ui.button(text=text, icon=icon, on_click=on_click)
        btn.classes(
            "bg-slate-700 hover:bg-slate-600 text-white font-medium "
            "rounded-lg px-4 py-2 transition-all duration-200 "
            "border border-slate-600 hover:border-slate-500"
        )
        return btn

    @staticmethod
    def danger(text: str = "", icon: str = None, on_click: Callable = None):
        btn = ui.button(text=text, icon=icon, on_click=on_click)
        btn.classes(
            "bg-red-600 hover:bg-red-500 text-white font-medium "
            "rounded-lg px-4 py-2 transition-all duration-200 "
            "shadow-lg shadow-red-500/20 "
            "hover:shadow-red-500/30"
        )
        return btn

    @staticmethod
    def success(text: str = "", icon: str = None, on_click: Callable = None):
        btn = ui.button(text=text, icon=icon, on_click=on_click)
        btn.classes(
            "bg-green-600 hover:bg-green-500 text-white font-medium "
            "rounded-lg px-4 py-2 transition-all duration-200 "
            "shadow-lg shadow-green-500/20 "
            "hover:shadow-green-500/30"
        )
        return btn

    @staticmethod
    def icon_only(icon: str, on_click: Callable = None, tooltip: str = None):
        btn = ui.button(icon=icon, on_click=on_click)
        btn.classes(
            "bg-slate-700/50 hover:bg-slate-700 text-slate-300 hover:text-white "
            "p-2 rounded-lg transition-all duration-200"
        )
        if tooltip:
            btn.props(f"title={tooltip}")
        return btn

    @staticmethod
    def sm(text: str = "", icon: str = None, on_click: Callable = None):
        btn = ui.button(text=text, icon=icon, on_click=on_click)
        btn.classes(
            "bg-slate-600 hover:bg-slate-500 text-white text-sm "
            "rounded px-3 py-1.5 transition-all duration-200"
        )
        return btn

    @staticmethod
    def lg(text: str = "", icon: str = None, on_click: Callable = None):
        btn = ui.button(text=text, icon=icon, on_click=on_click)
        btn.classes(
            "bg-blue-600 hover:bg-blue-500 text-white font-medium "
            "rounded-lg px-6 py-3 text-base transition-all duration-200 "
            "shadow-lg shadow-blue-500/20"
        )
        return btn

    @staticmethod
    def icon_sm(icon: str, on_click: Callable = None, tooltip: str = None):
        btn = ui.button(icon=icon, on_click=on_click)
        btn.classes(
            "bg-slate-700/50 hover:bg-slate-700 text-slate-300 hover:text-white "
            "p-1.5 rounded transition-all duration-200 text-sm"
        )
        if tooltip:
            btn.props(f"title={tooltip}")
        return btn
