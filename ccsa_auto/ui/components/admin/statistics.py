from nicegui import ui
from ccsa_auto.modules.admin.service import AdminService
from ccsa_auto.ui.components.admin.common import PageHeader, LoadingOverlay, Toast


def create_statistics():
    """创建数据统计页面 - 仪表盘增强版"""
    loading = LoadingOverlay("加载统计数据中...")

    header = PageHeader(
        title="数据统计",
        subtitle="平台运营数据概览和趋势分析",
        icon="insights",
    )
    header.render()

    with ui.row().classes("gap-4 mb-8"):
        refresh_btn = ui.button("刷新数据", icon="refresh").classes(
            "bg-blue-600 text-white px-6 py-3 rounded-xl font-medium text-lg "
            "shadow-lg shadow-blue-200 hover:shadow-blue-300 hover:scale-105 "
            "transition-all active:scale-95"
        )
        export_btn = ui.button("导出报表", icon="download").classes(
            "bg-white text-gray-700 px-6 py-3 rounded-xl font-medium text-lg "
            "border-2 border-gray-200 hover:border-blue-400 hover:text-blue-600 "
            "shadow-sm hover:shadow-md transition-all active:scale-95"
        )

    content_container = ui.column().classes("w-full")

    def show_statistics():
        content_container.clear()
        with content_container:
            loading.show()
            try:
                result = AdminService.get_statistics()
                if result["success"]:
                    data = result["data"]

                    # 用户统计卡片行
                    ui.label("用户数据概览").classes(
                        "text-xl font-bold text-gray-800 mb-4 block"
                    )
                    user_stats = data["users"]
                    with ui.row().classes("gap-5 mb-8 flex-wrap"):
                        stats_items = [
                            ("people", "总用户", str(user_stats["total"]), "blue"),
                            (
                                "how_to_reg",
                                "活跃用户",
                                str(user_stats["active"]),
                                "emerald",
                            ),
                            ("block", "封号用户", str(user_stats["banned"]), "red"),
                            (
                                "trending_up",
                                "本周新增",
                                str(user_stats["new_week"]),
                                "purple",
                            ),
                        ]
                        for icon_name, label, value, color in stats_items:
                            color_map = {
                                "blue": "from-blue-500 to-blue-600",
                                "emerald": "from-emerald-500 to-emerald-600",
                                "red": "from-red-500 to-red-600",
                                "purple": "from-purple-500 to-purple-600",
                            }
                            with ui.card().classes(
                                "flex-1 min-w-[240px] p-6 bg-white rounded-2xl border "
                                "border-gray-200 shadow-sm hover:shadow-lg hover:-translate-y-1 "
                                "transition-all duration-300"
                            ):
                                with ui.row().classes(
                                    "items-center justify-between w-full"
                                ):
                                    with ui.column().classes("items-start"):
                                        ui.label(label).classes(
                                            "text-sm font-semibold text-gray-500 uppercase tracking-wide"
                                        )
                                        ui.label(value).classes(
                                            "text-5xl font-bold text-gray-800 mt-2 tracking-tight"
                                        )
                                    with ui.row().classes(
                                        f"w-14 h-14 rounded-2xl bg-gradient-to-br {color_map[color]} "
                                        "flex items-center justify-center shadow-lg"
                                    ):
                                        ui.icon(icon_name).classes("w-7 h-7 text-white")

                    # 任务统计卡片行
                    ui.label("任务执行情况").classes(
                        "text-xl font-bold text-gray-800 mb-4 block"
                    )
                    task_stats = data["tasks"]
                    with ui.row().classes("gap-5 mb-8 flex-wrap"):
                        task_items = [
                            ("assignment", "总任务", str(task_stats["total"]), "cyan"),
                            (
                                "check_circle",
                                "已完成",
                                str(task_stats["completed"]),
                                "emerald",
                            ),
                            (
                                "play_circle",
                                "执行中",
                                str(task_stats["running"]),
                                "amber",
                            ),
                            ("error", "失败", str(task_stats["failed"]), "rose"),
                        ]
                        for icon_name, label, value, color in task_items:
                            color_map = {
                                "cyan": "from-cyan-500 to-cyan-600",
                                "emerald": "from-emerald-500 to-emerald-600",
                                "amber": "from-amber-500 to-amber-600",
                                "rose": "from-rose-500 to-rose-600",
                            }
                            with ui.card().classes(
                                "flex-1 min-w-[240px] p-6 bg-white rounded-2xl border "
                                "border-gray-200 shadow-sm hover:shadow-lg hover:-translate-y-1 "
                                "transition-all duration-300"
                            ):
                                with ui.row().classes(
                                    "items-center justify-between w-full"
                                ):
                                    with ui.column().classes("items-start"):
                                        ui.label(label).classes(
                                            "text-sm font-semibold text-gray-500 uppercase tracking-wide"
                                        )
                                        ui.label(value).classes(
                                            "text-5xl font-bold text-gray-800 mt-2 tracking-tight"
                                        )
                                    with ui.row().classes(
                                        f"w-14 h-14 rounded-2xl bg-gradient-to-br {color_map[color]} "
                                        "flex items-center justify-center shadow-lg"
                                    ):
                                        ui.icon(icon_name).classes("w-7 h-7 text-white")

                    # 公告统计
                    with ui.card().classes(
                        "w-full p-6 mb-8 bg-white rounded-2xl border border-gray-200 shadow-sm"
                    ):
                        with ui.row().classes("items-center justify-between"):
                            with ui.column().classes("items-start"):
                                ui.label("公告发布").classes(
                                    "text-sm font-semibold text-gray-500 uppercase tracking-wide"
                                )
                                ui.label(str(data["announcements"]["total"])).classes(
                                    "text-5xl font-bold text-gray-800 mt-2 tracking-tight"
                                )
                            with ui.row().classes(
                                "w-16 h-16 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 "
                                "flex items-center justify-center"
                            ):
                                ui.icon("campaign").classes("w-8 h-8 text-gray-600")

                    # 图表区域
                    ui.label("数据趋势分析").classes(
                        "text-xl font-bold text-gray-800 mb-4 block"
                    )

                    trend_result = AdminService.get_daily_stats(7)
                    if trend_result["success"]:
                        dates = [stat["date"] for stat in trend_result["stats"]]
                        new_users = [
                            stat["new_users"] for stat in trend_result["stats"]
                        ]
                        completed_tasks = [
                            stat["completed_tasks"] for stat in trend_result["stats"]
                        ]

                        # 趋势折线图
                        chart_id = "trend_chart_" + str(id(trend_result))
                        with ui.card().classes(
                            "w-full p-6 mb-6 bg-white rounded-2xl border border-gray-200 shadow-sm"
                        ):
                            ui.label("每日趋势（近7天）").classes(
                                "text-lg font-bold text-gray-800 mb-6 block"
                            )
                            ui.html(
                                f'<div id="{chart_id}" style="width: 100%; height: 350px;"></div>',
                                sanitize=False,
                            ).classes("w-full")

                            # 延迟执行图表脚本
                            def init_trend_chart():
                                js_code = f"""
                                    if (typeof echarts === 'undefined') {{
                                        var script = document.createElement('script');
                                        script.src = 'https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js';
                                        script.onload = function() {{ initChart_{chart_id}(); }};
                                        document.head.appendChild(script);
                                    }} else {{
                                        initChart_{chart_id}();
                                    }}
                                    function initChart_{chart_id}() {{
                                        var chartDom = document.getElementById('{chart_id}');
                                        if (!chartDom) return;
                                        var myChart = echarts.init(chartDom);
                                        var option = {{
                                            tooltip: {{
                                                trigger: 'axis',
                                                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                                borderColor: '#e5e7eb',
                                                borderWidth: 1,
                                                textStyle: {{ color: '#374151' }},
                                                padding: [12, 16],
                                                formatter: function(params) {{
                                                    var result = '<div style="font-weight: 600; margin-bottom: 8px;">' + params[0].axisValue + '</div>';
                                                    params.forEach(function(param) {{
                                                        result += '<div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">';
                                                        result += '<span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background:' + param.color + ';"></span>';
                                                        result += '<span>' + param.seriesName + ': </span>';
                                                        result += '<span style="font-weight: 600;">' + param.value + '</span>';
                                                        result += '</div>';
                                                    }});
                                                    return result;
                                                }}
                                            }},
                                            legend: {{
                                                data: ['新增用户', '完成任务'],
                                                bottom: 0,
                                                textStyle: {{ color: '#6b7280', fontSize: 13 }}
                                            }},
                                            grid: {{
                                                left: '3%',
                                                right: '4%',
                                                bottom: '12%',
                                                top: '5%',
                                                containLabel: true
                                            }},
                                            xAxis: {{
                                                type: 'category',
                                                boundaryGap: false,
                                                data: {dates},
                                                axisLine: {{ lineStyle: {{ color: '#e5e7eb' }} }},
                                                axisLabel: {{ color: '#6b7280', fontSize: 12 }}
                                            }},
                                            yAxis: {{
                                                type: 'value',
                                                axisLine: {{ show: false }},
                                                splitLine: {{ lineStyle: {{ color: '#f3f4f6', type: 'dashed' }} }},
                                                axisLabel: {{ color: '#6b7280', fontSize: 12 }}
                                            }},
                                            series: [
                                                {{
                                                    name: '新增用户',
                                                    type: 'line',
                                                    data: {new_users},
                                                    smooth: true,
                                                    symbol: 'circle',
                                                    symbolSize: 10,
                                                    lineStyle: {{ width: 3, color: '#3b82f6' }},
                                                    itemStyle: {{ color: '#3b82f6' }},
                                                    areaStyle: {{
                                                        color: {{
                                                            type: 'linear',
                                                            x: 0, y: 0, x2: 0, y2: 1,
                                                            colorStops: [{{offset: 0, color: 'rgba(59, 130, 246, 0.3)'}}, {{offset: 1, color: 'rgba(59, 130, 246, 0.05)'}}]
                                                        }}
                                                    }}
                                                }},
                                                {{
                                                    name: '完成任务',
                                                    type: 'line',
                                                    data: {completed_tasks},
                                                    smooth: true,
                                                    symbol: 'circle',
                                                    symbolSize: 10,
                                                    lineStyle: {{ width: 3, color: '#10b981' }},
                                                    itemStyle: {{ color: '#10b981' }},
                                                    areaStyle: {{
                                                        color: {{
                                                            type: 'linear',
                                                            x: 0, y: 0, x2: 0, y2: 1,
                                                            colorStops: [{{offset: 0, color: 'rgba(16, 185, 129, 0.3)'}}, {{offset: 1, color: 'rgba(16, 185, 129, 0.05)'}}]
                                                        }}
                                                    }}
                                                }}
                                            ]
                                        }};
                                        myChart.setOption(option);
                                        window.addEventListener('resize', function() {{
                                            myChart.resize();
                                        }});
                                    }}
                                """
                                ui.run_javascript(js_code)

                            ui.timer(0.1, init_trend_chart, once=True)

                        # 数据分布饼图
                        pie_chart_id = "pie_chart_" + str(id(trend_result))
                        with ui.row().classes("gap-6 flex-wrap"):
                            # 用户状态分布
                            with ui.card().classes(
                                "flex-1 min-w-[300px] p-6 bg-white rounded-2xl border border-gray-200 shadow-sm"
                            ):
                                ui.label("用户状态分布").classes(
                                    "text-lg font-bold text-gray-800 mb-4 block"
                                )
                                ui.html(
                                    f'<div id="{pie_chart_id}_users" style="width: 100%; height: 300px;"></div>',
                                    sanitize=False,
                                ).classes("w-full")

                                def init_user_pie():
                                    js_code = f"""
                                        if (typeof echarts === 'undefined') {{
                                            var script = document.createElement('script');
                                            script.src = 'https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js';
                                            script.onload = function() {{ initPie_{pie_chart_id}_users(); }};
                                            document.head.appendChild(script);
                                        }} else {{
                                            initPie_{pie_chart_id}_users();
                                        }}
                                        function initPie_{pie_chart_id}_users() {{
                                            var chartDom = document.getElementById('{pie_chart_id}_users');
                                            if (!chartDom) return;
                                            var myChart = echarts.init(chartDom);
                                            var option = {{
                                                tooltip: {{
                                                    trigger: 'item',
                                                    formatter: '{{b}}: {{c}} ({{d}}%)',
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
                                                series: [{{
                                                    name: '用户状态',
                                                    type: 'pie',
                                                    radius: ['45%', '70%'],
                                                    center: ['40%', '55%'],
                                                    avoidLabelOverlap: false,
                                                    itemStyle: {{
                                                        borderRadius: 8,
                                                        borderColor: '#fff',
                                                        borderWidth: 2
                                                    }},
                                                    label: {{ show: false }},
                                                    emphasis: {{
                                                        label: {{
                                                            show: true,
                                                            fontSize: 16,
                                                            fontWeight: 'bold'
                                                        }}
                                                    }},
                                                    data: [
                                                        {{ value: {user_stats["active"]}, name: '活跃用户', itemStyle: {{ color: '#10b981' }} }},
                                                        {{ value: {user_stats["banned"]}, name: '封号用户', itemStyle: {{ color: '#ef4444' }} }}
                                                    ]
                                                }}]
                                            }};
                                            myChart.setOption(option);
                                            window.addEventListener('resize', function() {{
                                                myChart.resize();
                                            }});
                                        }}
                                    """
                                    ui.run_javascript(js_code)

                                ui.timer(0.1, init_user_pie, once=True)

                            # 任务状态分布
                            with ui.card().classes(
                                "flex-1 min-w-[300px] p-6 bg-white rounded-2xl border border-gray-200 shadow-sm"
                            ):
                                ui.label("任务执行状态").classes(
                                    "text-lg font-bold text-gray-800 mb-4 block"
                                )
                                ui.html(
                                    f'<div id="{pie_chart_id}_tasks" style="width: 100%; height: 300px;"></div>',
                                    sanitize=False,
                                ).classes("w-full")

                                def init_task_pie():
                                    js_code = f"""
                                        if (typeof echarts === 'undefined') {{
                                            var script = document.createElement('script');
                                            script.src = 'https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js';
                                            script.onload = function() {{ initPie_{pie_chart_id}_tasks(); }};
                                            document.head.appendChild(script);
                                        }} else {{
                                            initPie_{pie_chart_id}_tasks();
                                        }}
                                        function initPie_{pie_chart_id}_tasks() {{
                                            var chartDom = document.getElementById('{pie_chart_id}_tasks');
                                            if (!chartDom) return;
                                            var myChart = echarts.init(chartDom);
                                            var option = {{
                                                tooltip: {{
                                                    trigger: 'item',
                                                    formatter: '{{b}}: {{c}} ({{d}}%)',
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
                                                series: [{{
                                                    name: '任务状态',
                                                    type: 'pie',
                                                    radius: ['45%', '70%'],
                                                    center: ['40%', '55%'],
                                                    avoidLabelOverlap: false,
                                                    itemStyle: {{
                                                        borderRadius: 8,
                                                        borderColor: '#fff',
                                                        borderWidth: 2
                                                    }},
                                                    label: {{ show: false }},
                                                    emphasis: {{
                                                        label: {{
                                                            show: true,
                                                            fontSize: 16,
                                                            fontWeight: 'bold'
                                                        }}
                                                    }},
                                                    data: [
                                                        {{ value: {task_stats["completed"]}, name: '已完成', itemStyle: {{ color: '#10b981' }} }},
                                                        {{ value: {task_stats["running"]}, name: '执行中', itemStyle: {{ color: '#f59e0b' }} }},
                                                        {{ value: {task_stats["total"] - task_stats["completed"] - task_stats["running"]}, name: '待执行', itemStyle: {{ color: '#3b82f6' }} }}
                                                    ]
                                                }}]
                                            }};
                                            myChart.setOption(option);
                                            window.addEventListener('resize', function() {{
                                                myChart.resize();
                                            }});
                                        }}
                                    """
                                    ui.run_javascript(js_code)

                                ui.timer(0.1, init_task_pie, once=True)

                else:
                    Toast.error(result.get("message", "获取统计数据失败"))
            except Exception as e:
                Toast.error(f"加载失败: {str(e)}")
            finally:
                loading.close()

    def export_report():
        result = AdminService.export_statistics_report()
        if result:
            Toast.success("报表导出成功")
            ui.download(result)
        else:
            Toast.error("导出失败")

    refresh_btn.on("click", show_statistics)
    export_btn.on("click", export_report)

    show_statistics()
