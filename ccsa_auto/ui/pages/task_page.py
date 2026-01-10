"""任务管理页面模块"""
from nicegui import ui
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Task
from ccsa_auto.modules.task.service import TaskService


def create_task_page():
    """创建任务管理页面"""
    with ui.card().classes('w-full h-auto p-6 page-card task-page'):
        ui.label('任务管理').classes('text-2xl font-bold mb-6')
        
        # 获取当前用户ID
        user_info = ui.context.client.storage.user.get('user_info', {})
        user_id = user_info.get('id')
        
        if not user_id:
            ui.label('未获取到用户信息，请重新登录').classes('text-red-500 mb-4')
            return
        
        # 任务列表
        task_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id'},
                {'name': 'task_name', 'label': '任务名称', 'field': 'task_name'},
                {'name': 'task_type', 'label': '任务类型', 'field': 'task_type'},
                {'name': 'description', 'label': '描述', 'field': 'description'},
                {'name': 'cron_expression', 'label': '定时表达式', 'field': 'cron_expression'},
                {'name': 'is_active', 'label': '是否激活', 'field': 'is_active'},
                {'name': 'execution_status', 'label': '执行状态', 'field': 'execution_status'},
                {'name': 'external_status', 'label': '外部状态', 'field': 'external_status'},
                {'name': 'next_run_time', 'label': '下次运行时间', 'field': 'next_run_time'},
                {'name': 'executed_at', 'label': '上次执行时间', 'field': 'executed_at'},
                {'name': 'actions', 'label': '操作', 'field': 'actions'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        # 刷新任务列表
        def refresh_tasks():
            """刷新任务列表"""
            try:
                db = SessionLocal()
                tasks = db.query(Task).filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
                
                formatted_tasks = []
                for task in tasks:
                    formatted_task = task.to_dict()
                    
                    # 添加操作按钮
                    formatted_task['actions'] = [
                        {
                            'label': '立即执行',
                            'color': 'primary',
                            'handler': lambda task_id=task.id: execute_task(task_id)
                        },
                        {
                            'label': '激活/停用',
                            'color': 'warning',
                            'handler': lambda task_id=task.id, is_active=task.is_active: toggle_task_active(task_id, is_active)
                        }
                    ]
                    
                    formatted_tasks.append(formatted_task)
                
                task_table.rows = formatted_tasks
                ui.notify(f'已加载 {len(formatted_tasks)} 个任务', type='info')
                
            except Exception as e:
                ui.notify(f'加载任务失败: {str(e)}', type='error')
                task_table.rows = []
            finally:
                try:
                    db.close()
                except:
                    pass
        
        # 执行任务
        def execute_task(task_id):
            """执行任务"""
            try:
                db = SessionLocal()
                task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
                
                if not task:
                    ui.notify('任务不存在', type='warning')
                    return
                
                # 获取用户信息
                from ccsa_auto.core.models import User
                user = db.query(User).filter_by(id=user_id).first()
                
                if not user:
                    ui.notify('用户不存在', type='warning')
                    return
                
                # 更新任务状态为运行中
                task.execution_status = 'running'
                task.updated_at = datetime.utcnow()
                db.commit()
                
                # 执行任务
                ui.notify(f'开始执行任务: {task.task_name}', type='info')
                result = TaskService.execute_task(task, user)
                
                # 更新任务状态
                task.execution_status = 'completed' if result.get('success') else 'failed'
                task.external_status = 'success' if result.get('success') else 'failed'
                task.result = str(result)
                task.executed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()
                db.commit()
                
                if result.get('success'):
                    ui.notify(f'任务执行成功: {result.get("message")}', type='success')
                else:
                    ui.notify(f'任务执行失败: {result.get("message")}', type='error')
                
                # 刷新任务列表
                refresh_tasks()
                
            except Exception as e:
                ui.notify(f'执行任务失败: {str(e)}', type='error')
                
                # 更新任务状态为失败
                try:
                    if task:
                        task.execution_status = 'failed'
                        task.external_status = 'failed'
                        task.result = f"异常: {str(e)}"
                        task.executed_at = datetime.utcnow()
                        task.updated_at = datetime.utcnow()
                        db.commit()
                except:
                    pass
            finally:
                try:
                    db.close()
                except:
                    pass
        
        # 切换任务激活状态
        def toggle_task_active(task_id, current_active):
            """切换任务激活状态"""
            try:
                db = SessionLocal()
                task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
                
                if not task:
                    ui.notify('任务不存在', type='warning')
                    return
                
                task.is_active = not current_active
                db.commit()
                
                # 更新调度器
                from ccsa_auto.modules.task.scheduler import add_task_to_scheduler, remove_task_from_scheduler
                
                if task.is_active:
                    add_task_to_scheduler(task.id)
                    ui.notify(f'任务已激活: {task.task_name}', type='success')
                else:
                    remove_task_from_scheduler(task.id)
                    ui.notify(f'任务已停用: {task.task_name}', type='warning')
                
                # 刷新任务列表
                refresh_tasks()
                
            except Exception as e:
                ui.notify(f'切换任务状态失败: {str(e)}', type='error')
            finally:
                try:
                    db.close()
                except:
                    pass
        
        # 手动创建默认任务按钮
        def create_default_tasks():
            """手动创建默认任务"""
            try:
                ui.notify('正在创建默认任务...', type='info')
                tasks = TaskService.create_default_tasks_for_user(user_id)
                ui.notify(f'成功创建 {len(tasks)} 个默认任务', type='success')
                refresh_tasks()
            except Exception as e:
                ui.notify(f'创建默认任务失败: {str(e)}', type='error')
        
        # 按钮区域
        with ui.row().classes('w-full mb-4 gap-2'):
            ui.button('刷新任务', on_click=refresh_tasks, icon='refresh').classes('bg-blue-500 hover:bg-blue-600 text-white')
            ui.button('创建默认任务', on_click=create_default_tasks, icon='add').classes('bg-green-500 hover:bg-green-600 text-white')
        
        # 任务统计信息
        with ui.card().classes('w-full mb-4 p-4 bg-gray-50'):
            with ui.row().classes('w-full justify-between'):
                ui.label('任务统计').classes('text-lg font-semibold')
                
                def update_stats():
                    """更新统计信息"""
                    try:
                        db = SessionLocal()
                        total = db.query(Task).filter_by(user_id=user_id).count()
                        active = db.query(Task).filter_by(user_id=user_id, is_active=True).count()
                        completed = db.query(Task).filter_by(user_id=user_id, execution_status='completed').count()
                        failed = db.query(Task).filter_by(user_id=user_id, execution_status='failed').count()
                        
                        stats_label.set_text(f'总计: {total} | 激活: {active} | 完成: {completed} | 失败: {failed}')
                    except Exception as e:
                        stats_label.set_text(f'统计失败: {str(e)}')
                    finally:
                        try:
                            db.close()
                        except:
                            pass
                
                stats_label = ui.label('').classes('text-sm text-gray-600')
                update_stats()
        
        # 初始加载任务
        refresh_tasks()