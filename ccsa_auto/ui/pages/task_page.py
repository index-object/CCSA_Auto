"""任务管理页面模块"""
from nicegui import ui


def create_task_page():
    """创建任务管理页面"""
    with ui.card().classes('w-full h-auto p-6 page-card task-page'):
        ui.label('任务管理').classes('text-2xl font-bold mb-6')
        
        # 任务列表
        task_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id'},
                {'name': 'task_type', 'label': '任务类型', 'field': 'task_type'},
                {'name': 'execution_status', 'label': '执行状态', 'field': 'execution_status'},
                {'name': 'external_status', 'label': '外部状态', 'field': 'external_status'},
                {'name': 'scheduled_time', 'label': '计划执行时间', 'field': 'scheduled_time'},
                {'name': 'executed_at', 'label': '实际执行时间', 'field': 'executed_at'},
                {'name': 'actions', 'label': '操作', 'field': 'actions'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        # 刷新任务列表
        def refresh_tasks():
            """刷新任务列表"""
            # 这里需要从数据库获取任务列表
            # 暂时返回模拟数据
            tasks = []
            task_table.rows = tasks
        
        # 执行任务
        def execute_task(task_id):
            """执行任务"""
            # 这里需要执行任务
            ui.notify('任务执行成功', type='success')
            refresh_tasks()
        
        # 刷新按钮
        ui.button('刷新任务', on_click=refresh_tasks).classes('mb-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded')
        
        # 初始加载任务
        refresh_tasks()