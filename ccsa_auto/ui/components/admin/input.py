from nicegui import ui
from typing import Optional, List, Callable


class AdminInput:
    """统一风格输入框"""

    @staticmethod
    def text(
        placeholder: str = "",
        value: str = None,
        width: str = "w-64",
        on_change: Callable = None,
    ):
        return ui.input(
            placeholder=placeholder, value=value, on_change=on_change
        ).classes(
            f"{width} bg-slate-700/80 text-white rounded-lg px-4 py-2.5 "
            "placeholder-slate-400 focus:outline-none focus:ring-2 "
            "focus:ring-blue-500/50 focus:bg-slate-700 "
            "border border-slate-600/50 hover:border-slate-500 "
            "transition-all duration-200"
        )

    @staticmethod
    def search(
        placeholder: str = "搜索...", width: str = "w-64", on_change: Callable = None
    ):
        with ui.row().classes(
            f"{width} items-center bg-slate-700/80 rounded-lg px-4 py-2 "
            "border border-slate-600/50 focus-within:ring-2 "
            "focus-within:ring-blue-500/50 focus-within:border-slate-500 "
            "transition-all duration-200"
        ):
            ui.icon("search").classes("w-5 h-5 text-slate-400")
            ui.input(placeholder=placeholder, on_change=on_change).classes(
                "flex-1 bg-transparent text-white text-sm "
                "placeholder-slate-400 focus:outline-none ml-2"
            )

    @staticmethod
    def number(
        placeholder: str = "",
        value: float = None,
        min_value: float = None,
        max_value: float = None,
        width: str = "w-24",
        on_change: Callable = None,
    ):
        return ui.number(
            placeholder=placeholder,
            value=value,
            min=min_value,
            max=max_value,
            on_change=on_change,
        ).classes(
            f"{width} bg-slate-700/80 text-white rounded-lg px-4 py-2.5 "
            "placeholder-slate-400 focus:outline-none focus:ring-2 "
            "focus:ring-blue-500/50 focus:bg-slate-700 "
            "border border-slate-600/50 hover:border-slate-500 "
            "transition-all duration-200"
        )

    @staticmethod
    def time(value: str = None, width: str = "w-28", on_change: Callable = None):
        return ui.time(value=value, on_change=on_change).classes(
            f"{width} bg-slate-700/80 text-white rounded-lg px-4 py-2.5 "
            "focus:outline-none focus:ring-2 "
            "focus:ring-blue-500/50 focus:bg-slate-700 "
            "border border-slate-600/50 hover:border-slate-500 "
            "transition-all duration-200"
        )


class AdminSelect:
    """统一样式下拉选择框"""

    @staticmethod
    def create(
        options: List[str],
        value: str = None,
        width: str = "w-40",
        on_change: Callable = None,
    ):
        return ui.select(options=options, value=value, on_change=on_change).classes(
            f"{width} bg-slate-700/80 text-white rounded-lg px-4 py-2.5 "
            "border border-slate-600/50 hover:border-slate-500 "
            "focus:outline-none focus:ring-2 focus:ring-blue-500/50 "
            "cursor-pointer appearance-none transition-all duration-200 "
            "[background-image:url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2716%27 height=%2716%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27%2394a3b8%27 stroke-width=%272%27%3E%3Cpath d=%27m6 9 6 6 6-6%27/%3E%3C/svg%3E')] "
            "[background-position:right_0.75rem_center] "
            "[background-size:1rem] "
            "[background-repeat:no-repeat]"
        )

    @staticmethod
    def filter(options: List[str], value: str = None, on_change: Callable = None):
        return ui.select(options=options, value=value, on_change=on_change).classes(
            "min-w-32 bg-slate-700/80 text-white rounded-lg px-3 py-2 "
            "border border-slate-600/50 hover:border-slate-500 "
            "focus:outline-none focus:ring-2 focus:ring-blue-500/50 "
            "cursor-pointer text-sm transition-all duration-200 "
            "[background-image:url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2716%27 height=%2716%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27%2394a3b8%27 stroke-width=%272%27%3E%3Cpath d=%27m6 9 6 6 6-6%27/%3E%3C/svg%3E')] "
            "[background-position:right_0.5rem_center] "
            "[background-size:0.875rem] "
            "[background-repeat:no-repeat]"
        )

    @staticmethod
    def small(options: List[str], value: str = None, on_change: Callable = None):
        return ui.select(options=options, value=value, on_change=on_change).classes(
            "w-28 bg-slate-700/80 text-white text-sm rounded-lg px-3 py-1.5 "
            "border border-slate-600/50 hover:border-slate-500 "
            "focus:outline-none focus:ring-2 focus:ring-blue-500/50 "
            "cursor-pointer transition-all duration-200 "
            "[background-image:url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2712%27 height=%2712%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27%2394a3b8%27 stroke-width=%272%27%3E%3Cpath d=%27m6 9 6 6 6-6%27/%3E%3C/svg%3E')] "
            "[background-position:right_0.5rem_center] "
            "[background-size:0.75rem] "
            "[background-repeat:no-repeat]"
        )


class AdminSwitch:
    """统一样式开关"""

    @staticmethod
    def create(value: bool = False, on_change: Callable = None):
        return ui.switch(value=value, on_change=on_change).classes("text-blue-500")


class AdminCheckbox:
    """统一样式复选框"""

    @staticmethod
    def create(text: str = "", value: bool = False, on_change: Callable = None):
        return ui.checkbox(text=text, value=value, on_change=on_change).classes(
            "text-slate-300"
        )
