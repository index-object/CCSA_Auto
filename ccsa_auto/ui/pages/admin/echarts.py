from nicegui import ui


@ui.page("/admin/echarts")
def echarts_resource():
    ui.add_head_html("""
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    """)
    with ui.column().classes("p-8"):
        ui.label("ECharts 已加载").classes("text-white text-xl")
