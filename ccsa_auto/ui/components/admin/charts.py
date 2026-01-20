from nicegui import ui, run
from typing import Dict, Any, Optional
import json


CHART_COLORS = {
    "primary": "#3b82f6",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#06b6d4",
    "purple": "#a855f7",
    "grid": "#334155",
    "text": "#94a3b8",
}


def get_dark_theme_config() -> Dict[str, Any]:
    """获取ECharts深色主题配置"""
    return {
        "color": [
            CHART_COLORS["primary"],
            CHART_COLORS["success"],
            CHART_COLORS["warning"],
            CHART_COLORS["danger"],
            CHART_COLORS["info"],
            CHART_COLORS["purple"],
        ],
        "backgroundColor": "transparent",
        "textStyle": {
            "color": CHART_COLORS["text"],
        },
        "title": {
            "textStyle": {
                "color": "#f1f5f9",
                "fontSize": 16,
                "fontWeight": "bold",
            },
            "subtextStyle": {
                "color": CHART_COLORS["text"],
            },
        },
        "legend": {
            "textStyle": {
                "color": CHART_COLORS["text"],
            },
        },
        "tooltip": {
            "backgroundColor": "#1e293b",
            "borderColor": "#334155",
            "textStyle": {
                "color": "#f1f5f9",
            },
        },
        "xAxis": {
            "axisLine": {
                "lineStyle": {
                    "color": CHART_COLORS["grid"],
                },
            },
            "axisLabel": {
                "color": CHART_COLORS["text"],
            },
            "splitLine": {
                "lineStyle": {
                    "color": "#1e293b",
                },
            },
        },
        "yAxis": {
            "axisLine": {
                "lineStyle": {
                    "color": CHART_COLORS["grid"],
                },
            },
            "axisLabel": {
                "color": CHART_COLORS["text"],
            },
            "splitLine": {
                "lineStyle": {
                    "color": CHART_COLORS["grid"],
                    "type": "dashed",
                },
            },
        },
        "grid": {
            "containLabel": True,
            "left": 10,
            "right": 10,
            "bottom": 10,
            "top": 40,
        },
    }


def init_line_chart(chart_id: str, data: Dict[str, Any], height: int = 300):
    """初始化折线图"""
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross",
                "crossStyle": {
                    "color": "#999",
                },
            },
        },
        "legend": {
            "data": list(data.get("series", {}).keys()),
            "top": 0,
        },
        "xAxis": {
            "type": "category",
            "data": data.get("categories", []),
            "axisPointer": {
                "type": "shadow",
            },
        },
        "yAxis": {
            "type": "value",
            "min": "dataMin",
            "max": "dataMax",
        },
        "series": [
            {
                "name": name,
                "type": "line",
                "data": values,
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 6,
                "lineStyle": {
                    "width": 3,
                },
                "itemStyle": {
                    "color": color,
                },
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0,
                        "y": 0,
                        "x2": 0,
                        "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": color + "40"},
                            {"offset": 1, "color": color + "05"},
                        ],
                    },
                },
            }
            for name, values, color in zip(
                data.get("series", {}).keys(),
                data.get("series", {}).values(),
                ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4"],
            )
        ],
    }

    ui.html(f'''
        <div id="{chart_id}" style="height: {height}px;"></div>
        <script>
            if (typeof echarts !== 'undefined') {{
                var chart = echarts.init(document.getElementById("{chart_id}"), 'dark');
                chart.setOption({json.dumps(option)});
                window.addEventListener('resize', function() {{
                    chart.resize();
                }});
            }}
        </script>
    ''')


def init_pie_chart(
    chart_id: str, data: Dict[str, Any], height: int = 300, donut: bool = True
):
    """初始化饼图"""
    option = {
        "tooltip": {
            "trigger": "item",
            "formatter": "{{b}}: {{c}} ({{d}}%)",
        },
        "legend": {
            "orient": "vertical",
            "right": 10,
            "top": "center",
        },
        "series": [
            {
                "type": "pie",
                "radius": ["40%", "70%"] if donut else ["0%", "70%"],
                "center": ["40%", "50%"],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 8,
                    "borderColor": "#1e293b",
                    "borderWidth": 2,
                },
                "label": {
                    "show": False,
                    "position": "center",
                },
                "emphasis": {
                    "label": {
                        "show": True,
                        "fontSize": 16,
                        "fontWeight": "bold",
                        "color": "#f1f5f9",
                    },
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)",
                    },
                },
                "labelLine": {
                    "show": False,
                },
                "data": [
                    {"value": value, "name": name}
                    for name, value in data.get("data", {}).items()
                ],
            }
        ],
    }

    ui.html(f'''
        <div id="{chart_id}" style="height: {height}px;"></div>
        <script>
            if (typeof echarts !== 'undefined') {{
                var chart = echarts.init(document.getElementById("{chart_id}"), 'dark');
                chart.setOption({json.dumps(option)});
                window.addEventListener('resize', function() {{
                    chart.resize();
                }});
            }}
        </script>
    ''')


def init_bar_chart(
    chart_id: str, data: Dict[str, Any], height: int = 300, horizontal: bool = False
):
    """初始化柱状图"""
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow",
            },
        },
        "legend": {
            "data": list(data.get("series", {}).keys()) if data.get("series") else [],
            "top": 0,
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True,
        },
        "xAxis": {
            "type": "value" if horizontal else "category",
            "data": data.get("categories", []) if not horizontal else None,
            "axisLabel": {
                "color": CHART_COLORS["text"],
            },
        },
        "yAxis": {
            "type": "category" if horizontal else "value",
            "data": data.get("categories", []) if horizontal else None,
            "axisLabel": {
                "color": CHART_COLORS["text"],
            },
        },
        "series": [
            {
                "name": name,
                "type": "bar",
                "data": values,
                "itemStyle": {
                    "color": color,
                    "borderRadius": [4, 4, 0, 0] if not horizontal else [0, 4, 4, 0],
                },
                "barWidth": "60%",
            }
            for name, values, color in zip(
                data.get("series", {}).keys() if data.get("series") else ["数据"],
                data.get("series", {}).values()
                if data.get("series")
                else [data.get("data", [])],
                ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444"],
            )
        ],
    }

    ui.html(f'''
        <div id="{chart_id}" style="height: {height}px;"></div>
        <script>
            if (typeof echarts !== 'undefined') {{
                var chart = echarts.init(document.getElementById("{chart_id}"), 'dark');
                chart.setOption({json.dumps(option)});
                window.addEventListener('resize', function() {{
                    chart.resize();
                }});
            }}
        </script>
    ''')


def init_gauge_chart(
    chart_id: str,
    value: float,
    title: str,
    min_value: float = 0,
    max_value: float = 100,
    height: int = 250,
):
    """初始化仪表盘"""
    option = {
        "series": [
            {
                "type": "gauge",
                "startAngle": 180,
                "endAngle": 0,
                "min": min_value,
                "max": max_value,
                "splitNumber": 5,
                "radius": "100%",
                "center": ["50%", "70%"],
                "axisLine": {
                    "lineStyle": {
                        "width": 12,
                        "color": [
                            [0.3, "#ef4444"],
                            [0.7, "#f59e0b"],
                            [1, "#22c55e"],
                        ],
                    },
                },
                "pointer": {
                    "icon": "path://M12.8,0.7l12,40.1H0.7L12.8,0.7z",
                    "length": "60%",
                    "width": 8,
                    "offsetCenter": [0, "-60%"],
                    "itemStyle": {
                        "color": "auto",
                    },
                },
                "axisTick": {
                    "length": 8,
                    "lineStyle": {
                        "color": "auto",
                        "width": 2,
                    },
                },
                "splitLine": {
                    "length": 15,
                    "lineStyle": {
                        "color": "auto",
                        "width": 3,
                    },
                },
                "axisLabel": {
                    "color": CHART_COLORS["text"],
                    "fontSize": 12,
                    "distance": -40,
                    "formatter": "{value}%",
                },
                "title": {
                    "offsetCenter": [0, "-20%"],
                    "fontSize": 14,
                    "color": CHART_COLORS["text"],
                },
                "detail": {
                    "fontSize": 30,
                    "offsetCenter": [0, "0%"],
                    "valueAnimation": True,
                    "formatter": "{value}%",
                    "color": "auto",
                },
                "data": [
                    {
                        "value": value,
                        "name": title,
                    }
                ],
            }
        ],
    }

    ui.html(f'''
        <div id="{chart_id}" style="height: {height}px;"></div>
        <script>
            if (typeof echarts !== 'undefined') {{
                var chart = echarts.init(document.getElementById("{chart_id}"), 'dark');
                chart.setOption({json.dumps(option)});
                window.addEventListener('resize', function() {{
                    chart.resize();
                }});
            }}
        </script>
    ''')


def chart_container(chart_id: str, title: str, subtitle: str = None):
    """图表容器"""
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
        ui.html(f'<div id="{chart_id}" class="w-full h-64"></div>').classes("p-4")
