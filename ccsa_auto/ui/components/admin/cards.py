from nicegui import ui
from typing import Optional, Callable


def confirm_dialog(
    title: str,
    message: str,
    confirm_text: str = "确认",
    cancel_text: str = "取消",
    on_confirm: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
    destructive: bool = False,
):
    """确认对话框组件"""
    confirm_classes = (
        "bg-red-600 hover:bg-red-700"
        if destructive
        else "bg-blue-600 hover:bg-blue-700"
    )

    with ui.dialog() as dialog:
        with ui.card().classes(
            "bg-slate-800 rounded-xl p-6 border border-slate-700 max-w-md"
        ):
            with ui.column().classes("gap-4"):
                with ui.row().classes("items-center gap-3"):
                    ui.icon("warning" if destructive else "help_outline").classes(
                        f"w-8 h-8 {'text-red-400' if destructive else 'text-blue-400'}"
                    )
                    ui.label(title).classes("text-xl font-bold text-white")

                ui.label(message).classes("text-slate-300 text-sm leading-relaxed")

                with ui.row().classes("justify-end gap-3 mt-2"):
                    ui.button(
                        cancel_text,
                        on_click=lambda: (
                            dialog.close(),
                            on_cancel() if on_cancel else None,
                        ),
                    ).classes(
                        "bg-slate-700 text-white hover:bg-slate-600 px-4 py-2 rounded-lg"
                    )
                    ui.button(
                        confirm_text,
                        on_click=lambda: (
                            dialog.close(),
                            on_confirm() if on_confirm else None,
                        ),
                    ).classes(f"{confirm_classes} text-white px-4 py-2 rounded-lg")


def loading_overlay(message: str = "加载中..."):
    """加载覆盖层"""
    with ui.row().classes(
        "fixed inset-0 bg-slate-900/80 backdrop-blur-sm z-50 "
        "flex items-center justify-center"
    ):
        with ui.column().classes("items-center gap-4"):
            ui.spinner(size="lg", color="blue").classes()
            ui.label(message).classes("text-white text-sm")


def empty_state(
    icon: str = "inbox",
    title: str = "暂无数据",
    description: str = "",
    action_text: str = "",
    on_action: Optional[Callable] = None,
):
    """空状态组件"""
    with ui.column().classes("items-center justify-center py-12"):
        ui.icon(icon).classes("w-16 h-16 text-slate-600 mb-4")
        ui.label(title).classes("text-xl font-medium text-slate-300 mb-2")
        if description:
            ui.label(description).classes("text-slate-400 text-sm")
        if action_text and on_action:
            ui.button(action_text, on_click=on_action).classes(
                "bg-blue-600 text-white mt-4"
            )


def search_bar(
    placeholder: str = "搜索...",
    on_search: Optional[Callable] = None,
    filters: Optional[list] = None,
):
    """搜索栏组件"""
    with ui.row().classes("items-center gap-3 w-full"):
        with ui.row().classes(
            "flex-1 items-center bg-slate-700 rounded-lg px-4 py-2.5 "
            "focus-within:ring-2 focus-within:ring-blue-500"
        ):
            ui.icon("search").classes("w-5 h-5 text-slate-400")
            ui.input(placeholder=placeholder).classes(
                "flex-1 bg-transparent text-white text-sm "
                "placeholder-slate-400 focus:outline-none ml-2"
            )

        if filters:
            with ui.row().classes("gap-2"):
                for filter_item in filters:
                    ui.button(
                        filter_item.get("icon", "filter_list"),
                        on_click=filter_item.get("on_click"),
                    ).classes(
                        "bg-slate-700 text-slate-300 hover:text-white "
                        "hover:bg-slate-600 p-2 rounded-lg"
                    )


def breadcrumb(items: list):
    """面包屑导航"""
    with ui.row().classes("items-center gap-2 text-sm"):
        for i, item in enumerate(items):
            if i > 0:
                ui.icon("chevron_right").classes("w-4 h-4 text-slate-500")
            if item.get("route"):
                row = ui.row().classes("items-center cursor-pointer")
                row.on("click", lambda r=item["route"]: ui.navigate.to(r))
                with row:
                    ui.label(item["label"]).classes("text-slate-400 hover:text-white")
            else:
                ui.label(item["label"]).classes("text-white font-medium")
