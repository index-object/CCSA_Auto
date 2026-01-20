from nicegui import ui
from typing import List, Dict, Callable, Optional
from .button import AdminButton


class AdminTable:
    """统一风格数据表格"""

    def __init__(
        self,
        columns: List[Dict],
        rows: List[Dict],
        title: str = "",
        on_row_click: Callable = None,
        searchable: bool = True,
        actions: List[Dict] = None,
        pagination: Dict = None,
    ):
        self.columns = columns
        self.rows = rows
        self.title = title
        self.on_row_click = on_row_click
        self.searchable = searchable
        self.actions = actions
        self.pagination = pagination or {"page": 1, "per_page": 20, "total": len(rows)}

    def render(self):
        with ui.column().classes("w-full"):
            self._render_header()
            self._render_content()
            if self.pagination:
                self._render_pagination()

    def _render_header(self):
        with ui.row().classes(
            "items-center justify-between px-6 py-4 border-b border-slate-700"
        ):
            with ui.row().classes("items-center gap-4 flex-wrap"):
                if self.title:
                    ui.label(self.title).classes("text-white text-lg font-semibold")

            with ui.row().classes("items-center gap-3"):
                if self.searchable:
                    from .input import AdminInput

                    AdminInput.search("搜索...", "w-64")

                if self.actions:
                    for action in self.actions:
                        btn = AdminButton.sm(
                            text=action.get("label", ""),
                            icon=action.get("icon"),
                            on_click=action.get("on_click"),
                        )
                        if action.get("primary"):
                            btn.classes(
                                "bg-blue-600 hover:bg-blue-500 text-white text-sm "
                                "rounded px-3 py-1.5 transition-all duration-200"
                            )

    def _render_content(self):
        with ui.table(columns=self.columns, rows=self.rows).classes(
            "w-full text-white"
        ):
            pass

    def _render_pagination(self):
        total_pages = (
            self.pagination["total"] + self.pagination["per_page"] - 1
        ) // self.pagination["per_page"]

        with ui.row().classes(
            "items-center justify-between px-6 py-4 border-t border-slate-700"
        ):
            ui.label(f"共 {self.pagination['total']} 条记录").classes(
                "text-slate-400 text-sm"
            )
            with ui.row().classes("items-center gap-2"):
                ui.button("上一页").classes(
                    "bg-slate-700 text-white text-sm px-3 py-1.5 rounded-lg "
                    "hover:bg-slate-600 transition-colors"
                )
                ui.label(f"{self.pagination['page']} / {total_pages}").classes(
                    "text-white text-sm"
                )
                ui.button("下一页").classes(
                    "bg-slate-700 text-white text-sm px-3 py-1.5 rounded-lg "
                    "hover:bg-slate-600 transition-colors"
                )

    @staticmethod
    def card(
        columns: List[Dict],
        rows: List[Dict],
        title: str = "数据列表",
        on_row_click: Callable = None,
        searchable: bool = True,
        actions: List[Dict] = None,
        pagination: Dict = None,
    ):
        with ui.card().classes(
            "w-full bg-slate-800 rounded-xl border border-slate-700 "
            "hover:border-slate-600 transition-all duration-300 overflow-hidden"
        ):
            table = AdminTable(
                columns=columns,
                rows=rows,
                title=title,
                on_row_click=on_row_click,
                searchable=searchable,
                actions=actions,
                pagination=pagination,
            )
            table.render()


def data_table(
    columns: List[Dict],
    rows: List[Dict],
    title: str = "数据列表",
    on_row_click: Callable = None,
    searchable: bool = True,
    actions: List[Dict] = None,
    pagination: Dict = None,
):
    """快捷创建表格"""
    AdminTable.card(
        columns=columns,
        rows=rows,
        title=title,
        on_row_click=on_row_click,
        searchable=searchable,
        actions=actions,
        pagination=pagination,
    )
