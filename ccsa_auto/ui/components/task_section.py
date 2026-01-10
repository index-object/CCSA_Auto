"""任务信息区组件模块"""
from nicegui import ui
from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Task


def create_task_section():
    """在主页面中嵌入的任务信息区"""
    with ui.card().classes('w-full md:w-1/3 h-auto p-6 bg-white shadow-lg rounded-lg task-section'):
        ui.label('任务管理').classes('text-xl font-bold mb-4 text-gray-700')

        # 任务列表展示
        task_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id'},
                {'name': 'task_name', 'label': '任务名称', 'field': 'task_name'},
                {'name': 'task_type', 'label': '任务类型', 'field': 'task_type'},
                {'name': 'execution_status', 'label': '执行状态', 'field': 'execution_status'},
                {'name': 'next_run_time', 'label': '下次执行', 'field': 'next_run_time'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')

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
                    task_data.append({
                        'id': task.id,
                        'task_name': task.task_name or task.task_type,
                        'task_type': task.task_type,
                        'execution_status': task.execution_status,
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

        # 任务数量标签
        task_count_label = ui.label('当前任务数量: 0').classes('text-sm text-gray-600 mb-2')
        
        # 刷新按钮
        with ui.row().classes('w-full justify-between items-center mt-4'):
            ui.button('刷新任务', on_click=refresh_tasks).classes('bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded shadow')
            
            # 手动执行按钮（需要任务ID输入）
            with ui.input('任务ID', placeholder='输入任务ID').classes('w-24') as task_id_input:
                pass
            ui.button('执行', on_click=lambda: execute_task(task_id_input.value)).classes('bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-4 rounded shadow')
        
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