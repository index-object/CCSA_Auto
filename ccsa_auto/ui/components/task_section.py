"""任务信息区组件模块"""
from nicegui import ui
from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Task


def create_task_section():
    """在主页面中嵌入的任务信息区"""
    with ui.card().classes('w-full h-auto p-4 md:p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300'):
        with ui.row().classes('items-center gap-2 mb-4 md:mb-6 pb-3 md:pb-4 border-b-2 border-gray-100'):
            ui.icon('list_alt', size='1.2rem md:1.5rem').classes('text-blue-600')
            ui.label('任务管理').classes('text-lg md:text-xl font-bold text-blue-600')
        
        # 任务数量标签
        task_count_label = ui.label('当前任务数量: 0').classes('text-base md:text-lg font-semibold text-gray-800 mb-3 md:mb-4')
        
        # 任务列表展示 - 使用响应式表格
        task_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'center', 'sortable': True},
                {'name': 'task_name', 'label': '任务名称', 'field': 'task_name', 'align': 'left', 'sortable': True},
                {'name': 'task_type', 'label': '任务类型', 'field': 'task_type', 'align': 'center', 'sortable': True},
                {'name': 'execution_status', 'label': '执行状态', 'field': 'execution_status', 'align': 'center', 'sortable': True},
                {'name': 'next_run_time', 'label': '下次执行时间', 'field': 'next_run_time', 'align': 'center', 'sortable': True}
            ],
            rows=[],
            row_key='id',
            pagination=5,
            selection='single'
        ).classes('w-full rounded-lg border border-gray-200 text-sm md:text-base').props('flat bordered dense')

        def refresh_tasks():
            """刷新任务列表（嵌入区）"""
            # 从数据库获取当前用户的任务列表
            db = SessionLocal()
            try:
                # 尝试从app.storage.user获取当前用户ID
                from nicegui import app
                
                # 尝试多种方式获取用户ID
                user_id = None
                
                # 方式1: 从user_info获取
                user_info = app.storage.user.get('user_info', {})
                if user_info and 'id' in user_info:
                    user_id = user_info.get('id')
                
                # 方式2: 直接从user_id字段获取
                if not user_id:
                    user_id = app.storage.user.get('user_id')
                
                # 检查用户是否已认证
                is_authenticated = app.storage.user.get('authenticated', False)
                
                if user_id and is_authenticated:
                    tasks = db.query(Task).filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
                else:
                    # 如果没有用户ID或未认证，显示所有任务（仅用于调试）
                    tasks = db.query(Task).order_by(Task.created_at.desc()).limit(10).all()
                    if not is_authenticated:
                        ui.notify('用户未登录，显示所有任务（调试模式）', type='warning')
                
                # 格式化任务数据
                task_data = []
                for task in tasks:
                    next_run = task.next_run_time.strftime('%Y-%m-%d %H:%M') if task.next_run_time else '未设置'
                    
                    # 根据任务类型设置显示文本
                    task_type_display = task.task_type
                    if task.task_type == 'daily':
                        task_type_display = '每日任务'
                    elif task.task_type == 'weekly':
                        task_type_display = '每周任务'
                    elif task.task_type == 'monthly':
                        task_type_display = '每月任务'
                    
                    # 根据执行状态设置显示文本
                    status_display = task.execution_status
                    if task.execution_status == 'completed':
                        status_display = '已完成'
                    elif task.execution_status == 'failed':
                        status_display = '失败'
                    elif task.execution_status == 'pending':
                        status_display = '待执行'
                    elif task.execution_status == 'running':
                        status_display = '执行中'
                    
                    task_data.append({
                        'id': task.id,
                        'task_name': task.task_name or task.task_type,
                        'task_type': task_type_display,
                        'execution_status': status_display,
                        'next_run_time': next_run
                    })
                
                task_table.rows = task_data
                
                # 显示任务数量
                task_count_label.text = f'当前任务数量: {len(task_data)}'
                
            except Exception as e:
                ui.notify(f'获取任务失败: {str(e)}', type='negative')
                task_table.rows = []
            finally:
                db.close()

        # 操作按钮区域 - 响应式布局
        with ui.column().classes('w-full gap-3 md:gap-0 md:flex-row md:justify-between md:items-center mt-4 md:mt-6'):
            with ui.row().classes('gap-2 flex-wrap'):
                ui.button('刷新任务', on_click=refresh_tasks, icon='refresh').classes('bg-blue-50 hover:bg-blue-100 text-blue-600 font-medium py-1 md:py-2 px-3 md:px-4 rounded-lg shadow-sm text-sm md:text-base')
                
                # 手动执行按钮
                task_id_input = ui.input('任务ID', placeholder='输入任务ID').classes('w-24 md:w-32 text-sm')
                ui.button('执行任务', on_click=lambda: execute_task(task_id_input.value), icon='play_arrow').classes('bg-green-50 hover:bg-green-100 text-green-600 font-medium py-1 md:py-2 px-3 md:px-4 rounded-lg shadow-sm text-sm md:text-base')
            
            # 快速操作按钮
            with ui.row().classes('gap-2'):
                ui.button('查看全部', icon='visibility').classes('bg-gray-50 hover:bg-gray-100 text-gray-700 font-medium py-1 md:py-2 px-3 md:px-4 rounded-lg shadow-sm text-sm md:text-base')
        
        def execute_task(task_id):
            """手动执行任务"""
            if not task_id:
                ui.notify('请输入任务ID', type='warning')
                return
            
            try:
                from ccsa_auto.modules.task.service import TaskService
                from ccsa_auto.core.database import SessionLocal
                from ccsa_auto.core.models import Task, User
                
                db = SessionLocal()
                task = db.query(Task).filter_by(id=int(task_id)).first()
                if not task:
                    ui.notify(f'任务 {task_id} 不存在', type='negative')
                    return
                
                user = db.query(User).filter_by(id=task.user_id).first()
                if not user:
                    ui.notify(f'用户 {task.user_id} 不存在', type='negative')
                    return
                
                # 执行任务
                result = TaskService.execute_task(task, user)
                
                if result.get('success'):
                    ui.notify(f'任务 {task_id} 执行成功: {result.get("message")}', type='positive')
                else:
                    ui.notify(f'任务 {task_id} 执行失败: {result.get("message")}', type='negative')
                
                # 刷新任务列表
                refresh_tasks()
                
            except Exception as e:
                ui.notify(f'执行任务失败: {str(e)}', type='negative')
            finally:
                db.close()
        
        # 初始加载任务
        refresh_tasks()