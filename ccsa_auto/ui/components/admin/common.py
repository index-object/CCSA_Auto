"""通用UI组件 - 确认对话框、加载状态、空状态"""

from nicegui import ui
from typing import Callable, Optional


class ConfirmDialog:
    """确认对话框组件"""

    def __init__(
        self,
        title: str = "确认操作",
        message: str = "确定要执行此操作吗？",
        confirm_text: str = "确定",
        cancel_text: str = "取消",
        confirm_color: str = "negative",
        on_confirm: Callable = None,
    ):
        self.title = title
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.confirm_color = confirm_color
        self.on_confirm = on_confirm
        self._dialog = None

    def show(self):
        """显示对话框"""
        self._dialog = ui.dialog()
        with (
            self._dialog,
            ui.card().classes("w-96 max-w-full p-6 rounded-xl shadow-2xl"),
        ):
            ui.label(self.title).classes("text-xl font-bold text-gray-800 mb-4")
            ui.label(self.message).classes("text-gray-600 mb-6")
            with ui.row().classes("justify-end gap-3"):
                ui.button(
                    self.cancel_text,
                    on_click=self._dialog.close,
                ).classes("px-4 py-2")
                ui.button(
                    self.confirm_text,
                    on_click=self._on_confirm,
                    color=self.confirm_color,
                ).classes("px-4 py-2")
        self._dialog.open()

    def _on_confirm(self):
        if self.on_confirm:
            self.on_confirm()
        self._dialog.close()

    @staticmethod
    def danger(
        message: str = "确定要删除此项目吗？此操作不可恢复。",
        on_confirm: Callable = None,
    ):
        """快速创建危险操作确认框"""
        dialog = ConfirmDialog(
            title="⚠️ 危险操作",
            message=message,
            confirm_text="删除",
            cancel_text="取消",
            confirm_color="red",
            on_confirm=on_confirm,
        )
        dialog.show()


class LoadingOverlay:
    """加载遮罩层"""

    def __init__(self, text: str = "加载中..."):
        self.text = text
        self._spinner = None

    def show(self):
        """显示加载状态"""
        self._spinner = ui.dialog()
        with (
            self._spinner,
            ui.card().classes("p-8 rounded-xl shadow-2xl bg-white/90 backdrop-blur"),
        ):
            ui.spinner("dots", size="3em", color="blue").classes("mb-4")
            ui.label(self.text).classes("text-gray-600 font-medium")

    def close(self):
        """关闭加载状态"""
        if self._spinner:
            self._spinner.close()
            self._spinner = None

    def __enter__(self):
        self.show()
        return self

    def __exit__(self, *args):
        self.close()


class EmptyState:
    """空状态组件"""

    def __init__(
        self,
        icon: str = "inbox",
        title: str = "暂无数据",
        description: str = "没有找到相关记录",
        action_text: str = None,
        on_action: Callable = None,
    ):
        self.icon = icon
        self.title = title
        self.description = description
        self.action_text = action_text
        self.on_action = on_action

    def render(self):
        """渲染空状态"""
        with ui.column().classes("items-center justify-center py-16 px-4 text-center"):
            ui.icon(self.icon).classes("w-20 h-20 text-gray-300 mb-4")
            ui.label(self.title).classes("text-xl font-semibold text-gray-600 mb-2")
            ui.label(self.description).classes("text-gray-400 mb-6")
            if self.action_text and self.on_action:
                ui.button(
                    self.action_text,
                    icon=self.icon,
                    on_click=self.on_action,
                ).classes(
                    "bg-blue-600 text-white hover:bg-blue-700 px-6 py-2 rounded-lg"
                )

    @staticmethod
    def no_results(on_refresh: Callable = None):
        """快捷创建无结果空状态"""
        state = EmptyState(
            icon="search_off",
            title="未找到匹配结果",
            description="请尝试调整搜索条件或筛选条件",
            action_text="清除筛选",
            on_action=on_refresh,
        )
        state.render()

    @staticmethod
    def no_data(on_create: Callable = None):
        """快捷创建无数据空状态"""
        state = EmptyState(
            icon="add_circle_outline",
            title="暂无数据",
            description="点击按钮添加第一条数据",
            action_text="添加数据",
            on_action=on_create,
        )
        state.render()


class SkeletonLoader:
    """骨架屏加载组件"""

    def __init__(self, lines: int = 5, show_header: bool = True):
        self.lines = lines
        self.show_header = show_header

    def render(self):
        """渲染骨架屏"""
        with ui.column().classes("w-full gap-4 p-4"):
            if self.show_header:
                with ui.row().classes("items-center gap-4 mb-2"):
                    with ui.element("div").classes(
                        "w-64 h-10 bg-gray-200 rounded-lg animate-pulse"
                    ):
                        pass
                    with ui.element("div").classes(
                        "w-32 h-10 bg-gray-200 rounded-lg animate-pulse ml-auto"
                    ):
                        pass

            for _ in range(self.lines):
                with ui.row().classes("w-full items-center gap-4"):
                    for _ in range(4):
                        with (
                            ui.element("div")
                            .classes("h-8 bg-gray-200 rounded animate-pulse")
                            .classes("w-1/4" if _ < 3 else "w-24")
                        ):
                            pass


class Toast:
    """Toast提示组件"""

    @staticmethod
    def success(message: str = "操作成功"):
        ui.notify(message, type="positive", position="top right")

    @staticmethod
    def error(message: str = "操作失败"):
        ui.notify(message, type="negative", position="top right")

    @staticmethod
    def warning(message: str = "请注意"):
        ui.notify(message, type="warning", position="top right")

    @staticmethod
    def info(message: str = "提示信息"):
        ui.notify(message, type="info", position="top right")


class Badge:
    """状态徽章组件"""

    @staticmethod
    def success(text: str, inline: bool = True):
        cls = "px-2 py-0.5 rounded-full text-xs font-medium" if inline else ""
        ui.label(text).classes(f"bg-green-100 text-green-700 {cls}")

    @staticmethod
    def warning(text: str, inline: bool = True):
        cls = "px-2 py-0.5 rounded-full text-xs font-medium" if inline else ""
        ui.label(text).classes(f"bg-yellow-100 text-yellow-700 {cls}")

    @staticmethod
    def error(text: str, inline: bool = True):
        cls = "px-2 py-0.5 rounded-full text-xs font-medium" if inline else ""
        ui.label(text).classes(f"bg-red-100 text-red-700 {cls}")

    @staticmethod
    def info(text: str, inline: bool = True):
        cls = "px-2 py-0.5 rounded-full text-xs font-medium" if inline else ""
        ui.label(text).classes(f"bg-blue-100 text-blue-700 {cls}")

    @staticmethod
    def neutral(text: str, inline: bool = True):
        cls = "px-2 py-0.5 rounded-full text-xs font-medium" if inline else ""
        ui.label(text).classes(f"bg-gray-100 text-gray-700 {cls}")


class StatsCard:
    """统计卡片组件"""

    def __init__(
        self,
        title: str,
        value: str,
        icon: str,
        color: str = "blue",
        trend: str = None,
        trend_up: bool = True,
    ):
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        self.trend = trend
        self.trend_up = trend_up

    def render(self):
        """渲染统计卡片"""
        color_map = {
            "blue": {
                "bg": "bg-blue-50",
                "icon": "text-blue-500",
                "border": "border-blue-200",
            },
            "green": {
                "bg": "bg-green-50",
                "icon": "text-green-500",
                "border": "border-green-200",
            },
            "yellow": {
                "bg": "bg-yellow-50",
                "icon": "text-yellow-500",
                "border": "border-yellow-200",
            },
            "red": {
                "bg": "bg-red-50",
                "icon": "text-red-500",
                "border": "border-red-200",
            },
            "purple": {
                "bg": "bg-purple-50",
                "icon": "text-purple-500",
                "border": "border-purple-200",
            },
        }
        colors = color_map.get(self.color, color_map["blue"])

        with ui.card().classes(
            f"p-5 rounded-xl border {colors['border']} {colors['bg']} "
            "hover:shadow-md transition-shadow duration-300"
        ):
            with ui.row().classes("items-center justify-between"):
                with ui.column():
                    ui.label(self.title).classes(
                        "text-sm text-gray-500 font-medium mb-1"
                    )
                    ui.label(self.value).classes("text-3xl font-bold text-gray-800")
                    if self.trend:
                        with ui.row().classes("items-center gap-1 mt-1"):
                            ui.icon(
                                "trending_up" if self.trend_up else "trending_down"
                            ).classes(
                                f"w-4 h-4 {'text-green-500' if self.trend_up else 'text-red-500'}"
                            )
                            ui.label(self.trend).classes(
                                f"text-sm {'text-green-600' if self.trend_up else 'text-red-600'}"
                            )
                ui.icon(self.icon).classes(f"w-12 h-12 {colors['icon']} opacity-80")


class PageHeader:
    """页面标题组件"""

    def __init__(
        self,
        title: str,
        subtitle: str = None,
        icon: str = None,
        actions: list = None,
    ):
        self.title = title
        self.subtitle = subtitle
        self.icon = icon
        self.actions = actions or []

    def render(self):
        """渲染页面标题"""
        with ui.row().classes("items-center justify-between mb-6 flex-wrap gap-4"):
            with ui.column():
                with ui.row().classes("items-center gap-3"):
                    if self.icon:
                        ui.icon(self.icon).classes("w-8 h-8 text-blue-600")
                    ui.label(self.title).classes("text-2xl font-bold text-gray-800")
                if self.subtitle:
                    ui.label(self.subtitle).classes("text-gray-500 text-sm mt-1")

            if self.actions:
                with ui.row().classes("items-center gap-2"):
                    for action in self.actions:
                        action()

    def action_button(
        self,
        text: str,
        icon: str = None,
        on_click: Callable = None,
        color: str = "primary",
    ):
        """添加操作按钮"""
        btn = ui.button(text=text, icon=icon, on_click=on_click)
        if color == "primary":
            btn.classes(
                "bg-blue-600 text-white hover:bg-blue-700 "
                "px-4 py-2 rounded-lg transition-colors"
            )
        elif color == "secondary":
            btn.classes(
                "bg-gray-100 text-gray-700 hover:bg-gray-200 "
                "px-4 py-2 rounded-lg transition-colors"
            )
        elif color == "danger":
            btn.classes(
                "bg-red-600 text-white hover:bg-red-700 "
                "px-4 py-2 rounded-lg transition-colors"
            )
        return btn
