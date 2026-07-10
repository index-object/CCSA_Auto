from nicegui import ui
from typing import List, Dict, Any, Callable, Optional


class DataTable:
    def __init__(
        self,
        columns: List[Dict[str, Any]],
        data: List[Dict[str, Any]] = None,
        on_row_click: Optional[Callable] = None,
        selectable: bool = False,
    ):
        self.columns = columns
        self.data = data or []
        self.on_row_click = on_row_click
        self.selectable = selectable
        self.current_page = 1
        self.page_size = 20
        self._selected_rows = []

    def render(self):
        with ui.card().classes("rounded-2xl overflow-hidden"):
            with ui.table().classes("w-full"):
                with ui.thead():
                    with ui.tr():
                        if self.selectable:
                            ui.th("")
                        for col in self.columns:
                            ui.th(col.get("label", col.get("field", "")))

                with ui.tbody():
                    for row in self.data:
                        with ui.tr().classes("hover:bg-gray-50"):
                            if self.selectable:
                                with ui.td():

                                    def make_checkbox_handler(r=row):
                                        def handler(v):
                                            self._toggle_select(r, v)

                                        return handler

                                    ui.checkbox(
                                        value=row in self._selected_rows,
                                        on_change=make_checkbox_handler(row),
                                    )
                            for col in self.columns:
                                with ui.td():
                                    ui.label(str(row.get(col["field"], "")))

            with ui.row().classes("w-full justify-between items-center p-4"):
                ui.label(f"Total: {len(self.data)}")
                with ui.row():
                    ui.button("Previous", on_click=self._prev_page).props("flat")
                    ui.label(f"Page {self.current_page}")
                    ui.button("Next", on_click=self._next_page).props("flat")

    def _toggle_select(self, row, selected):
        if selected:
            self._selected_rows.append(row)
        else:
            self._selected_rows.remove(row)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1

    def _next_page(self):
        self.current_page += 1
