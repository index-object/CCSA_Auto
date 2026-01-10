"""三个一任务完成情况页面模块 - 基于app.storage.user的会话隔离版本"""
from nicegui import ui, app
from ccsa_auto.modules.auth.service import AuthService


def create_three_one_page():
    """创建三个一任务完成情况页面"""
    with ui.card().classes('w-full h-auto p-6 page-card three-one-page'):
        ui.label('三个一任务完成情况').classes('text-2xl font-bold mb-6')
        
        # 创建三个任务卡片
        with ui.row().classes('w-full gap-6'):
            # 每日一题卡片
            with ui.card().classes('flex-1 p-4'):
                ui.label('每日一题').classes('text-xl font-semibold mb-4')
                
                # 创建占位符标签
                daily_name_label = ui.label('任务名称: 加载中...').classes('text-gray-600')
                daily_status_label = ui.label('完成状态: 加载中...').classes('text-gray-600')
                daily_obtained_label = ui.label('已获得积分: 加载中...').classes('text-gray-600')
            
            # 每周一课卡片
            with ui.card().classes('flex-1 p-4'):
                ui.label('每周一课').classes('text-xl font-semibold mb-4')
                
                weekly_name_label = ui.label('任务名称: 加载中...').classes('text-gray-600')
                weekly_status_label = ui.label('完成状态: 加载中...').classes('text-gray-600')
                weekly_obtained_label = ui.label('已获得积分: 加载中...').classes('text-gray-600')
            
            # 每月一考卡片
            with ui.card().classes('flex-1 p-4'):
                ui.label('每月一考').classes('text-xl font-semibold mb-4')
                
                monthly_name_label = ui.label('任务名称: 加载中...').classes('text-gray-600')
                monthly_status_label = ui.label('完成状态: 加载中...').classes('text-gray-600')
                monthly_obtained_label = ui.label('已获得积分: 加载中...').classes('text-gray-600')
        
        # 刷新按钮
        def refresh_task_status():
            """刷新任务完成情况"""
            # 从app.storage.user获取用户ID
            user_info = app.storage.user.get('user_info', {})
            user_id = user_info.get('id')
            
            if not user_id:
                ui.notify('未获取到用户信息，请重新登录', type='error')
                return
            
            # 使用带重试的方法获取任务状态
            task_status = AuthService.get_task_status_with_retry(user_id)
            if task_status:
                # 更新每日一题信息
                daily = task_status.get('daily', {})
                daily_name_label.text = f'任务名称: {daily.get("name", "每日一题")}'
                daily_status_label.text = f'完成状态: {daily.get("status", "未知")}'
                daily_obtained_label.text = f'已获得积分: {daily.get("obtained_score", 0)}'
                
                # 更新每周一课信息
                weekly = task_status.get('weekly', {})
                weekly_name_label.text = f'任务名称: {weekly.get("name", "每周一课")}'
                weekly_status_label.text = f'完成状态: {weekly.get("status", "未知")}'
                weekly_obtained_label.text = f'已获得积分: {weekly.get("obtained_score", 0)}'
                
                # 更新每月一考信息
                monthly = task_status.get('monthly', {})
                monthly_name_label.text = f'任务名称: {monthly.get("name", "每月一考")}'
                monthly_status_label.text = f'完成状态: {monthly.get("status", "未知")}'
                monthly_obtained_label.text = f'已获得积分: {monthly.get("obtained_score", 0)}'
                
                # 如果成功获取，更新存储的外部令牌（可能已被刷新）
                # 注意：get_task_status_with_retry内部已经更新了数据库中的令牌
                # 但app.storage.user中的令牌可能需要更新
                # 我们可以从数据库获取最新令牌
                from ccsa_auto.core.database import SessionLocal
                from ccsa_auto.core.models import User
                db = SessionLocal()
                try:
                    user = db.query(User).filter_by(id=user_id).first()
                    if user and user.external_token:
                        app.storage.user['external_token'] = user.external_token
                finally:
                    db.close()
                    
            else:
                ui.notify('获取任务完成情况失败: 认证失败或网络错误', type='error')
        
        ui.button('刷新任务状态', on_click=refresh_task_status).classes('mt-6 bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded')
        
        # 初始加载任务状态
        ui.timer(0.1, lambda: refresh_task_status(), once=True)