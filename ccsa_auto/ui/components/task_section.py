"""任务信息区组件模块"""
from nicegui import ui


def create_task_section():
    """在主页面中嵌入的任务信息区"""
    with ui.card().classes('w-full md:w-1/3 h-auto p-6 bg-white shadow-lg rounded-lg task-section'):
        ui.label('任务管理').classes('text-xl font-bold mb-4 text-gray-700')

        # 简化版任务列表展示
        task_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id'},
                {'name': 'task_type', 'label': '任务类型', 'field': 'task_type'},
                {'name': 'execution_status', 'label': '执行状态', 'field': 'execution_status'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')

        def refresh_tasks():
            """刷新任务列表（嵌入区）"""
            # 从数据库或服务获取任务列表（保留占位）
            tasks = []
            task_table.rows = tasks

        ui.button('刷新任务', on_click=refresh_tasks).classes('mt-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded shadow')
        refresh_tasks()