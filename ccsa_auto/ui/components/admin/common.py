"""通用UI组件 - 现代化设计系统版本"""

from nicegui import ui
from typing import Callable, Optional


class ConfirmDialog:
    """确认对话框组件 - 现代化样式"""

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
            ui.card().classes(
                "w-96 max-w-full p-6 rounded-2xl shadow-2xl bg-white border border-gray-100"
            ),
        ):
            ui.label(self.title).classes("text-xl font-bold text-gray-900 mb-3")
            ui.label(self.message).classes(
                "text-gray-600 text-base leading-relaxed mb-6"
            )
            with ui.row().classes("justify-end gap-3"):
                ui.button(
                    self.cancel_text,
                    on_click=self._dialog.close,
                ).classes(
                    "px-5 py-2.5 rounded-lg text-gray-600 hover:bg-gray-100 "
                    "font-medium transition-colors"
                )
                ui.button(
                    self.confirm_text,
                    on_click=self._on_confirm,
                    color=self.confirm_color,
                ).classes(
                    "px-5 py-2.5 rounded-lg font-medium transition-colors shadow-sm"
                )
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
            title="确认删除",
            message=message,
            confirm_text="删除",
            cancel_text="取消",
            confirm_color="red",
            on_confirm=on_confirm,
        )
        dialog.show()


class LoadingOverlay:
    """加载遮罩层 - 现代化样式"""

    def __init__(self, text: str = "加载中..."):
        self.text = text
        self._spinner = None

    def show(self):
        """显示加载状态"""
        self._spinner = ui.dialog()
        with (
            self._spinner,
            ui.card().classes(
                "p-10 rounded-2xl shadow-2xl bg-white/95 backdrop-blur-sm border border-gray-100"
            ),
        ):
            ui.spinner("dots", size="2.5em", color="blue").classes("mb-4")
            ui.label(self.text).classes("text-gray-700 font-medium text-lg")

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
    """空状态组件 - 现代化样式"""

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
        with ui.column().classes(
            "items-center justify-center py-20 px-8 text-center w-full"
        ):
            ui.icon(self.icon).classes("w-24 h-24 text-gray-300 mb-5 opacity-60")
            ui.label(self.title).classes("text-2xl font-semibold text-gray-700 mb-3")
            ui.label(self.description).classes("text-gray-400 text-lg mb-8 max-w-md")
            if self.action_text and self.on_action:
                ui.button(
                    self.action_text,
                    icon=self.icon,
                    on_click=self.on_action,
                ).classes(
                    "bg-blue-600 text-white hover:bg-blue-700 px-8 py-3 "
                    "rounded-xl font-medium text-lg shadow-lg shadow-blue-200 "
                    "transition-all hover:scale-105"
                )

    @staticmethod
    def no_results(on_refresh: Callable = None):
        """快捷创建无结果空状态"""
        state = EmptyState(
            icon="search_off",
            title="未找到匹配结果",
            description="请尝试调整搜索条件或筛选条件后重试",
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
            description="点击按钮添加您的第一条数据记录",
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
                with ui.row().classes("items-center gap-4 mb-4"):
                    with ui.element("div").classes(
                        "w-72 h-12 bg-gray-200 rounded-xl animate-pulse"
                    ):
                        pass
                    with ui.element("div").classes(
                        "w-36 h-12 bg-gray-200 rounded-xl animate-pulse ml-auto"
                    ):
                        pass

            for _ in range(self.lines):
                with ui.row().classes("w-full items-center gap-4"):
                    for _ in range(4):
                        with (
                            ui.element("div")
                            .classes("h-10 bg-gray-200 rounded-lg animate-pulse")
                            .classes("w-1/4" if _ < 3 else "w-28")
                        ):
                            pass


class Toast:
    """Toast提示组件 - 现代化样式"""

    @staticmethod
    def success(message: str = "操作成功"):
        ui.notify(
            message,
            type="positive",
            position="top",
            close=True,
            classes="text-lg font-medium",
        )

    @staticmethod
    def error(message: str = "操作失败"):
        ui.notify(
            message,
            type="negative",
            position="top",
            close=True,
            classes="text-lg font-medium",
        )

    @staticmethod
    def warning(message: str = "请注意"):
        ui.notify(
            message,
            type="warning",
            position="top",
            close=True,
            classes="text-lg font-medium",
        )

    @staticmethod
    def info(message: str = "提示信息"):
        ui.notify(
            message,
            type="info",
            position="top",
            close=True,
            classes="text-lg font-medium",
        )


class Badge:
    """状态徽章组件 - 现代化样式"""

    @staticmethod
    def success(text: str, inline: bool = True):
        cls = "px-3 py-1 rounded-full text-sm font-semibold" if inline else ""
        ui.label(text).classes(
            f"bg-emerald-100 text-emerald-700 border border-emerald-200 {cls}"
        )

    @staticmethod
    def warning(text: str, inline: bool = True):
        cls = "px-3 py-1 rounded-full text-sm font-semibold" if inline else ""
        ui.label(text).classes(
            f"bg-amber-100 text-amber-700 border border-amber-200 {cls}"
        )

    @staticmethod
    def error(text: str, inline: bool = True):
        cls = "px-3 py-1 rounded-full text-sm font-semibold" if inline else ""
        ui.label(text).classes(f"bg-red-100 text-red-700 border border-red-200 {cls}")

    @staticmethod
    def info(text: str, inline: bool = True):
        cls = "px-3 py-1 rounded-full text-sm font-semibold" if inline else ""
        ui.label(text).classes(
            f"bg-blue-100 text-blue-700 border border-blue-200 {cls}"
        )

    @staticmethod
    def neutral(text: str, inline: bool = True):
        cls = "px-3 py-1 rounded-full text-sm font-semibold" if inline else ""
        ui.label(text).classes(
            f"bg-gray-100 text-gray-700 border border-gray-200 {cls}"
        )


class StatsCard:
    """统计卡片组件 - 现代化设计"""

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
                "border": "border-blue-100",
                "gradient_from": "from-blue-50",
                "gradient_to": "to-blue-100",
            },
            "green": {
                "bg": "bg-emerald-50",
                "icon": "text-emerald-500",
                "border": "border-emerald-100",
                "gradient_from": "from-emerald-50",
                "gradient_to": "to-emerald-100",
            },
            "yellow": {
                "bg": "bg-amber-50",
                "icon": "text-amber-500",
                "border": "border-amber-100",
                "gradient_from": "from-amber-50",
                "gradient_to": "to-amber-100",
            },
            "red": {
                "bg": "bg-red-50",
                "icon": "text-red-500",
                "border": "border-red-100",
                "gradient_from": "from-red-50",
                "gradient_to": "to-red-100",
            },
            "purple": {
                "bg": "bg-purple-50",
                "icon": "text-purple-500",
                "border": "border-purple-100",
                "gradient_from": "from-purple-50",
                "gradient_to": "to-purple-100",
            },
            "cyan": {
                "bg": "bg-cyan-50",
                "icon": "text-cyan-500",
                "border": "border-cyan-100",
                "gradient_from": "from-cyan-50",
                "gradient_to": "to-cyan-100",
            },
        }
        colors = color_map.get(self.color, color_map["blue"])

        with ui.card().classes(
            f"p-6 rounded-2xl border {colors['border']} bg-gradient-to-br "
            f"{colors['gradient_from']} {colors['gradient_to']} "
            "hover:shadow-lg hover:shadow-gray-200/50 transition-all duration-300 "
            "cursor-default group"
        ):
            with ui.row().classes("items-center justify-between"):
                with ui.column().classes("items-start"):
                    ui.label(self.title).classes(
                        "text-base text-gray-500 font-medium mb-1 group-hover:text-gray-600"
                    )
                    ui.label(self.value).classes(
                        "text-4xl font-bold text-gray-900 tracking-tight"
                    )
                    if self.trend:
                        with ui.row().classes("items-center gap-1.5 mt-2"):
                            ui.icon(
                                "trending_up" if self.trend_up else "trending_down"
                            ).classes(
                                f"w-5 h-5 {'text-emerald-500' if self.trend_up else 'text-red-500'}"
                            )
                            ui.label(self.trend).classes(
                                f"text-base font-medium {'text-emerald-600' if self.trend_up else 'text-red-600'}"
                            )
                ui.icon(self.icon).classes(
                    f"w-14 h-14 {colors['icon']} opacity-70 group-hover:opacity-90 transition-opacity"
                )


class PageHeader:
    """页面标题组件 - 现代化设计"""

    def __init__(
        self,
        title: str,
        subtitle: str = None,
        icon: str = None,
        actions: list = None,
        show_breadcrumb: bool = True,
    ):
        self.title = title
        self.subtitle = subtitle
        self.icon = icon
        self.actions = actions or []
        self.show_breadcrumb = show_breadcrumb

    def render(self):
        """渲染页面标题"""
        with ui.card().classes(
            "w-full p-6 mb-6 bg-white rounded-2xl border border-gray-100 "
            "shadow-sm hover:shadow-md transition-all duration-300"
        ):
            if self.show_breadcrumb:
                with ui.row().classes("items-center gap-2 mb-3"):
                    ui.label("首页").classes(
                        "text-sm text-gray-400 hover:text-blue-600 cursor-pointer transition-colors"
                    )
                    ui.icon("chevron_right").classes("w-4 h-4 text-gray-300")
                    ui.label(self.title).classes("text-sm text-gray-600 font-medium")

            with ui.row().classes("items-center justify-between flex-wrap gap-4"):
                with ui.column():
                    if self.icon:
                        with ui.row().classes("items-center gap-3"):
                            with ui.row().classes(
                                "w-12 h-12 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 "
                                "flex items-center justify-center border border-blue-200"
                            ):
                                ui.icon(self.icon).classes("w-6 h-6 text-blue-600")
                            ui.label(self.title).classes(
                                "text-3xl font-bold text-gray-900 tracking-tight"
                            )
                    else:
                        ui.label(self.title).classes(
                            "text-3xl font-bold text-gray-900 tracking-tight"
                        )
                    if self.subtitle:
                        ui.label(self.subtitle).classes(
                            "text-gray-500 text-lg mt-1 font-normal"
                        )

                if self.actions:
                    with ui.row().classes("items-center gap-3"):
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
                "px-6 py-3 rounded-xl font-medium text-lg shadow-lg shadow-blue-200 "
                "transition-all hover:scale-105 active:scale-95"
            )
        elif color == "secondary":
            btn.classes(
                "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 "
                "px-6 py-3 rounded-xl font-medium text-lg shadow-sm "
                "transition-all hover:scale-105 active:scale-95"
            )
        elif color == "danger":
            btn.classes(
                "bg-red-600 text-white hover:bg-red-700 "
                "px-6 py-3 rounded-xl font-medium text-lg shadow-lg shadow-red-200 "
                "transition-all hover:scale-105 active:scale-95"
            )
        return btn


class ChartContainer:
    """图表容器组件 - 用于集成ECharts"""

    def __init__(self, chart_id: str = None, height: str = "400px"):
        self.chart_id = chart_id or f"chart_{id(self)}"
        self.height = height
        self._container = None

    def render(self, chart_config: str = None):
        """渲染图表容器"""
        self._container = ui.html().classes("w-full")
        if chart_config:
            self._container.content = self._wrap_chart(chart_config)
        return self._container

    def update_chart(self, chart_config: str):
        """更新图表配置"""
        if self._container:
            self._container.content = self._wrap_chart(chart_config)

    def _wrap_chart(self, config: str) -> str:
        """包装图表配置为完整的HTML"""
        return f"""
        <div id="{self.chart_id}" style="width: 100%; height: {self.height};"></div>
        <script>
            if (window.{self.chart_id}_chart) {{
                window.{self.chart_id}_chart.dispose();
            }}
            {config}
        </script>
        """

    @staticmethod
    def create_bar_chart(
        title: str,
        labels: list,
        datasets: list,
        height: str = "350px",
    ) -> "ChartContainer":
        """创建柱状图配置"""
        container = ChartContainer(height=height)

        colors = [
            "#3b82f6",
            "#10b981",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
            "#ec4899",
            "#06b6d4",
            "#84cc16",
        ]

        data_series = []
        for i, dataset in enumerate(datasets):
            data_series.append(
                f"""
                {{
                    name: '{dataset["name"]}',
                    type: 'bar',
                    data: {dataset["data"]},
                    itemStyle: {{ color: '{colors[i % len(colors)]}' }},
                    barWidth: '60%',
                }}
                """
            )

        config = f"""
        var chartDom = document.getElementById('{container.chart_id}');
        var myChart = echarts.init(chartDom);
        window.{container.chart_id}_chart = myChart;

        var option = {{
            title: {{
                text: '{title}',
                left: 'center',
                textStyle: {{
                    fontSize: 16,
                    fontWeight: 'bold',
                    color: '#374151'
                }}
            }},
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{
                    type: 'shadow'
                }},
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: '#e5e7eb',
                textStyle: {{ color: '#374151' }}
            }},
            legend: {{
                data: {[d["name"] for d in datasets]},
                bottom: 0,
                textStyle: {{ color: '#6b7280' }}
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '15%',
                top: '15%',
                containLabel: true
            }},
            xAxis: {{
                type: 'category',
                data: {labels},
                axisLine: {{ lineStyle: {{ color: '#e5e7eb' }} }},
                axisLabel: {{ color: '#6b7280', fontSize: 12 }}
            }},
            yAxis: {{
                type: 'value',
                axisLine: {{ show: false }},
                splitLine: {{ lineStyle: {{ color: '#f3f4f6' }} }},
                axisLabel: {{ color: '#6b7280', fontSize: 12 }}
            }},
            series: [{",".join(data_series)}]
        }};

        myChart.setOption(option);
        window.addEventListener('resize', function() {{
            myChart.resize();
        }});
        """

        container._container = ui.html().classes("w-full")
        container._container.content = container._wrap_chart(config)
        return container

    @staticmethod
    def create_line_chart(
        title: str,
        labels: list,
        datasets: list,
        height: str = "350px",
    ) -> "ChartContainer":
        """创建折线图配置"""
        container = ChartContainer(height=height)

        colors = [
            "#3b82f6",
            "#10b981",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
        ]

        data_series = []
        for i, dataset in enumerate(datasets):
            data_series.append(
                f"""
                {{
                    name: '{dataset["name"]}',
                    type: 'line',
                    data: {dataset["data"]},
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 8,
                    lineStyle: {{ width: 3, color: '{colors[i % len(colors)]}' }},
                    itemStyle: {{ color: '{colors[i % len(colors)]}' }},
                    areaStyle: {{
                        color: {{
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [{{offset: 0, color: '{colors[i % len(colors)]}40'}}, {{offset: 1, color: '{colors[i % len(colors)]}05'}}]
                        }}
                    }}
                }}
                """
            )

        config = f"""
        var chartDom = document.getElementById('{container.chart_id}');
        var myChart = echarts.init(chartDom);
        window.{container.chart_id}_chart = myChart;

        var option = {{
            title: {{
                text: '{title}',
                left: 'center',
                textStyle: {{
                    fontSize: 16,
                    fontWeight: 'bold',
                    color: '#374151'
                }}
            }},
            tooltip: {{
                trigger: 'axis',
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: '#e5e7eb',
                textStyle: {{ color: '#374151' }}
            }},
            legend: {{
                data: {[d["name"] for d in datasets]},
                bottom: 0,
                textStyle: {{ color: '#6b7280' }}
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '15%',
                top: '15%',
                containLabel: true
            }},
            xAxis: {{
                type: 'category',
                boundaryGap: false,
                data: {labels},
                axisLine: {{ lineStyle: {{ color: '#e5e7eb' }} }},
                axisLabel: {{ color: '#6b7280', fontSize: 12 }}
            }},
            yAxis: {{
                type: 'value',
                axisLine: {{ show: false }},
                splitLine: {{ lineStyle: {{ color: '#f3f4f6' }} }},
                axisLabel: {{ color: '#6b7280', fontSize: 12 }}
            }},
            series: [{",".join(data_series)}]
        }};

        myChart.setOption(option);
        window.addEventListener('resize', function() {{
            myChart.resize();
        }});
        """

        container._container = ui.html().classes("w-full")
        container._container.content = container._wrap_chart(config)
        return container

    @staticmethod
    def create_pie_chart(
        title: str,
        data: dict,
        height: str = "350px",
    ) -> "ChartContainer":
        """创建饼图配置"""
        container = ChartContainer(height=height)

        colors = [
            "#3b82f6",
            "#10b981",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
            "#ec4899",
            "#06b6d4",
            "#84cc16",
        ]

        pie_data = []
        for i, (name, value) in enumerate(data.items()):
            pie_data.append(f"{{name: '{name}', value: {value}}}")

        config = f"""
        var chartDom = document.getElementById('{container.chart_id}');
        var myChart = echarts.init(chartDom);
        window.{container.chart_id}_chart = myChart;

        var option = {{
            title: {{
                text: '{title}',
                left: 'center',
                textStyle: {{
                    fontSize: 16,
                    fontWeight: 'bold',
                    color: '#374151'
                }}
            }},
            tooltip: {{
                trigger: 'item',
                formatter: '{{a}} <br/><b>{{b}}</b>: {{c}} ({{d}}%)',
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: '#e5e7eb',
                textStyle: {{ color: '#374151' }}
            }},
            legend: {{
                orient: 'vertical',
                right: '5%',
                top: 'center',
                textStyle: {{ color: '#6b7280' }}
            }},
            series: [
                {{
                    name: '数据',
                    type: 'pie',
                    radius: ['45%', '70%'],
                    center: ['40%', '55%'],
                    avoidLabelOverlap: false,
                    itemStyle: {{
                        borderRadius: 8,
                        borderColor: '#fff',
                        borderWidth: 2
                    }},
                    label: {{
                        show: false,
                        position: 'center'
                    }},
                    emphasis: {{
                        label: {{
                            show: true,
                            fontSize: 18,
                            fontWeight: 'bold',
                            color: '#374151'
                        }}
                    }},
                    labelLine: {{
                        show: false
                    }},
                    data: [{",".join(pie_data)}],
                    color: {colors}
                }}
            ]
        }};

        myChart.setOption(option);
        window.addEventListener('resize', function() {{
            myChart.resize();
        }});
        """

        container._container = ui.html().classes("w-full")
        container._container.content = container._wrap_chart(config)
        return container
