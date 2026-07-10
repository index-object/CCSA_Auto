from nicegui import ui
from typing import List, Dict, Callable, Optional
from .button import AdminButton


class AdminTable:
    """统一风格数据表格 - 现代化增强版"""

    def __init__(
        self,
        columns: List[Dict],
        rows: List[Dict],
        title: str = "",
        on_row_click: Callable = None,
        searchable: bool = True,
        actions: List[Dict] = None,
        pagination: Dict = None,
        on_refresh: Callable = None,
        sortable: bool = True,
        striped: bool = True,
        hover: bool = True,
    ):
        self.columns = columns
        self.rows = rows
        self.title = title
        self.on_row_click = on_row_click
        self.searchable = searchable
        self.actions = actions
        self.pagination = pagination or {"page": 1, "per_page": 20, "total": len(rows)}
        self.on_refresh = on_refresh
        self.sortable = sortable
        self.striped = striped
        self.hover = hover
        self._table = None
        self._search_input = None

    def render(self):
        """渲染完整表格"""
        with ui.column().classes("w-full gap-4"):
            self._render_header()
            self._render_content()
            if self.pagination:
                self._render_pagination()

    def _render_header(self):
        with ui.row().classes(
            "items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200 rounded-t-lg"
        ):
            with ui.row().classes("items-center gap-4 flex-wrap"):
                if self.title:
                    ui.label(self.title).classes("text-lg font-semibold text-gray-800")
                if self.on_refresh:
                    ui.button(icon="refresh", on_click=self.on_refresh).classes(
                        "p-2 rounded-lg hover:bg-gray-200 text-gray-500 transition-colors"
                    ).props("flat round size='sm'")

            with ui.row().classes("items-center gap-3"):
                if self.searchable:
                    self._render_search()

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

    def _render_search(self):
        with ui.row().classes(
            "items-center gap-2 px-3 py-2 bg-white border border-gray-200 "
            "rounded-lg focus-within:ring-2 focus-within:ring-blue-500/20 "
            "focus-within:border-blue-400 transition-all"
        ):
            ui.icon("search").classes("w-4 h-4 text-gray-400")
            self._search_input = ui.input(placeholder="搜索...").classes(
                "w-48 text-sm bg-transparent focus:outline-none"
            )
            self._search_input.on("change", self._handle_search)

    def _handle_search(self):
        """处理搜索"""
        pass

    def _render_content(self):
        table_classes = (
            "w-full text-gray-700"
            + (" even:bg-gray-50" if self.striped else "")
            + (" hover:bg-gray-50" if self.hover else "")
        )

        self._table = ui.table(
            columns=self.columns,
            rows=self.rows,
            row_key=self.columns[0].get("field", "id") if self.columns else "id",
        ).classes(table_classes)

        if self.on_row_click:
            self._table.on("row-click", lambda e: self.on_row_click(e.args))

    def _render_pagination(self):
        total_pages = max(
            1,
            (self.pagination["total"] + self.pagination["per_page"] - 1)
            // self.pagination["per_page"],
        )

        with ui.row().classes(
            "items-center justify-between px-4 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg"
        ):
            ui.label(f"共 {self.pagination['total']} 条记录").classes(
                "text-gray-500 text-sm"
            )
            with ui.row().classes("items-center gap-2"):
                ui.button("首页", on_click=lambda: self._change_page(1)).classes(
                    "px-3 py-1.5 text-sm bg-white border border-gray-200 "
                    "text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                ).props("flat" if self.pagination["page"] == 1 else "")
                ui.button(
                    "上一页",
                    on_click=lambda: self._change_page(self.pagination["page"] - 1),
                ).classes(
                    "px-3 py-1.5 text-sm bg-white border border-gray-200 "
                    "text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                ).props("disable" if self.pagination["page"] == 1 else "flat")

                ui.label(f"{self.pagination['page']} / {total_pages}").classes(
                    "text-gray-700 text-sm font-medium px-3"
                )

                ui.button(
                    "下一页",
                    on_click=lambda: self._change_page(self.pagination["page"] + 1),
                ).classes(
                    "px-3 py-1.5 text-sm bg-white border border-gray-200 "
                    "text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                ).props("disable" if self.pagination["page"] >= total_pages else "flat")
                ui.button(
                    "末页", on_click=lambda: self._change_page(total_pages)
                ).classes(
                    "px-3 py-1.5 text-sm bg-white border border-gray-200 "
                    "text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                ).props("flat" if self.pagination["page"] >= total_pages else "")

    def _change_page(self, page: int):
        """切换页面"""
        if self.pagination.get("on_page_change"):
            self.pagination["on_page_change"](page)

    def update_rows(self, rows: List[Dict], total: int = None):
        """更新表格数据"""
        self.rows = rows
        self.pagination["total"] = total if total is not None else len(rows)
        if self._table:
            self._table.rows = rows

    @staticmethod
    def card(
        columns: List[Dict],
        rows: List[Dict],
        title: str = "数据列表",
        on_row_click: Callable = None,
        searchable: bool = True,
        actions: List[Dict] = None,
        pagination: Dict = None,
        on_refresh: Callable = None,
    ):
        """快捷创建表格卡片"""
        with ui.card().classes(
            "w-full bg-white rounded-xl border border-gray-200 "
            "shadow-sm overflow-hidden"
        ):
            table = AdminTable(
                columns=columns,
                rows=rows,
                title=title,
                on_row_click=on_row_click,
                searchable=searchable,
                actions=actions,
                pagination=pagination,
                on_refresh=on_refresh,
            )
            table.render()


class DataTableHelper:
    """表格辅助工具类"""

    @staticmethod
    def create_status_column() -> Dict:
        """创建状态列配置"""
        return {
            "name": "status",
            "label": "状态",
            "field": "status",
            "align": "center",
            "sortable": True,
        }

    @staticmethod
    def create_actions_column(actions: List[Dict]) -> Dict:
        """创建操作列配置"""
        return {
            "name": "actions",
            "label": "操作",
            "field": "actions",
            "align": "center",
        }

    @staticmethod
    def format_datetime(value: str) -> str:
        """格式化日期时间"""
        if not value:
            return "-"
        return value[:19] if len(value) > 19 else value

    @staticmethod
    def format_status(status: int, mapping: Dict[int, str] = None) -> str:
        """格式化状态显示"""
        if mapping:
            return mapping.get(status, "未知")
        return "正常" if status == 0 else "封号"


def data_table(
    columns: List[Dict],
    rows: List[Dict],
    title: str = "数据列表",
    on_row_click: Callable = None,
    searchable: bool = True,
    actions: List[Dict] = None,
    pagination: Dict = None,
    on_refresh: Callable = None,
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
        on_refresh=on_refresh,
    )
