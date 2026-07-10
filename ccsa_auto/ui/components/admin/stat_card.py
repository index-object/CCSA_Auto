from nicegui import ui
from typing import Optional, Callable


def stat_card(
    title: str,
    value: str,
    change: Optional[str] = None,
    change_type: Optional[str] = None,
    icon: str = "analytics",
    icon_color: str = "blue",
    subtitle: Optional[str] = None,
    on_click: Optional[Callable] = None,
):
    """统计卡片组件"""
    color_map = {
        "blue": "text-blue-400",
        "green": "text-green-400",
        "red": "text-red-400",
        "amber": "text-amber-400",
        "cyan": "text-cyan-400",
        "purple": "text-purple-400",
    }

    change_color_map = {
        "up": "text-green-400",
        "down": "text-red-400",
        "positive": "text-green-400",
        "negative": "text-red-400",
    }

    icon_class = color_map.get(icon_color, "text-blue-400")
    change_class = change_color_map.get(change_type or "", "text-slate-400")

    card_classes = (
        "bg-slate-800 rounded-xl p-6 border border-slate-700 "
        "hover:border-slate-600 hover:shadow-lg hover:shadow-blue-500/10 "
        "transition-all duration-300 cursor-pointer"
    )

    card = ui.card().classes(card_classes)

    with card:
        with ui.row().classes("items-center justify-between"):
            with ui.column().classes("flex-1"):
                ui.label(title).classes(
                    "text-slate-400 text-sm font-medium uppercase tracking-wide"
                )
                ui.label(value).classes("text-3xl font-bold text-white mt-2")

                if change:
                    with ui.row().classes("items-center gap-1 mt-2"):
                        icon_name = (
                            "trending_up"
                            if change_type in ["up", "positive"]
                            else "trending_down"
                            if change_type in ["down", "negative"]
                            else "remove"
                        )
                        ui.icon(icon_name).classes(f"w-4 h-4 {change_class}")
                        ui.label(change).classes(f"text-sm font-medium {change_class}")

                if subtitle:
                    ui.label(subtitle).classes("text-slate-500 text-xs mt-1")

            with ui.column().classes("items-center justify-center"):
                ui.icon(icon).classes(f"w-7 h-7 {icon_class}")


def stat_card_grid(cards: list):
    """统计卡片网格布局"""
    with ui.row().classes(
        "w-full grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"
    ):
        for card in cards:
            stat_card(
                title=card.get("title", ""),
                value=card.get("value", ""),
                change=card.get("change"),
                change_type=card.get("change_type"),
                icon=card.get("icon", "analytics"),
                icon_color=card.get("icon_color", "blue"),
                subtitle=card.get("subtitle"),
                on_click=card.get("on_click"),
            )


def chart_card(
    title: str,
    chart_id: str,
    subtitle: Optional[str] = None,
    actions: Optional[list] = None,
):
    """图表卡片组件"""
    with ui.card().classes(
        "bg-slate-800 rounded-xl border border-slate-700 "
        "hover:border-slate-600 transition-all duration-300 overflow-hidden"
    ):
        with ui.row().classes(
            "items-center justify-between px-6 py-4 border-b border-slate-700"
        ):
            with ui.column():
                ui.label(title).classes("text-white text-lg font-semibold")
                if subtitle:
                    ui.label(subtitle).classes("text-slate-400 text-sm")

            if actions:
                with ui.row().classes("gap-2"):
                    for action in actions:
                        ui.button(
                            action.get("icon", "more_vert"),
                            on_click=action.get("on_click"),
                        ).classes(
                            "bg-slate-700 text-slate-300 hover:text-white "
                            "hover:bg-slate-600 p-2 rounded-lg"
                        )

        ui.html(f'<div id="{chart_id}" class="w-full h-64"></div>', sanitize=False)


def data_table_card(
    title: str,
    columns: list,
    rows: list,
    actions: Optional[list] = None,
    searchable: bool = True,
    on_row_click: Optional[Callable] = None,
):
    """数据表格卡片"""
    with ui.card().classes(
        "bg-slate-800 rounded-xl border border-slate-700 "
        "hover:border-slate-600 transition-all duration-300 overflow-hidden"
    ):
        with ui.row().classes(
            "items-center justify-between px-6 py-4 border-b border-slate-700"
        ):
            ui.label(title).classes("text-white text-lg font-semibold")

            with ui.row().classes("items-center gap-3"):
                if searchable:
                    with ui.row().classes(
                        "items-center bg-slate-700 rounded-lg px-3 py-2 "
                        "focus-within:ring-2 focus-within:ring-blue-500"
                    ):
                        ui.icon("search").classes("w-4 h-4 text-slate-400")
                        ui.input(placeholder="搜索...").classes(
                            "bg-transparent text-white text-sm w-32 "
                            "placeholder-slate-400 focus:outline-none ml-2"
                        )

                if actions:
                    for action in actions:
                        ui.button(
                            action.get("label", ""),
                            icon=action.get("icon"),
                            on_click=action.get("on_click"),
                        ).classes(
                            f"bg-blue-600 text-white text-sm"
                            if action.get("primary")
                            else "bg-slate-700 text-white text-sm"
                        )

        with ui.table(columns=columns, rows=rows).classes("w-full text-white"):
            pass

        with ui.row().classes(
            "items-center justify-between px-6 py-4 border-t border-slate-700"
        ):
            ui.label(f"共 {len(rows)} 条记录").classes("text-slate-400 text-sm")
            with ui.row().classes("items-center gap-2"):
                ui.button("上一页").classes(
                    "bg-slate-700 text-white text-sm px-3 py-1.5 rounded-lg"
                )
                ui.label("1 / 10").classes("text-white text-sm")
                ui.button("下一页").classes(
                    "bg-slate-700 text-white text-sm px-3 py-1.5 rounded-lg"
                )
