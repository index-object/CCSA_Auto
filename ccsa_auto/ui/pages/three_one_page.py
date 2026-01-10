"""三个一任务完成情况页面模块 - 基于app.storage.user的会话隔离版本"""
from nicegui import ui, app
from ccsa_auto.modules.auth.service import AuthService


def create_three_one_page():
    """创建三个一任务完成情况页面"""
    with ui.card().classes('w-full h-auto p-5 md:p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300'):
        with ui.row().classes('items-center gap-3 mb-5 md:mb-6 pb-4 border-b-2 border-gray-100'):
            ui.icon('task_alt', size='1.5rem md:1.8rem').classes('text-blue-600')
            ui.label('三个一任务完成情况').classes('text-xl md:text-2xl font-bold text-blue-600')
        
        # 创建三个任务卡片 - 使用网格布局
        with ui.grid(columns=3).classes('w-full gap-4 mb-6'):
            # 每日一题卡片
            with ui.card().classes('p-4 md:p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl text-center hover:shadow-md transition-shadow duration-300'):
                ui.icon('today', size='2.2rem md:3rem').classes('text-blue-600 mb-3 md:mb-4')
                ui.label('每日一题').classes('text-lg md:text-xl font-bold text-gray-800 mb-2 md:mb-3')
                
                # 创建占位符标签
                daily_status_label = ui.label('加载中...').classes('text-sm md:text-base mb-2 md:mb-3')
                daily_obtained_label = ui.label('0 积分').classes('text-2xl md:text-3xl font-bold text-blue-700')
                
                # 存储标签引用
                daily_name_label = ui.label('每日一题').classes('hidden')
            
            # 每周一课卡片
            with ui.card().classes('p-4 md:p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl text-center hover:shadow-md transition-shadow duration-300'):
                ui.icon('date_range', size='2.2rem md:3rem').classes('text-purple-600 mb-3 md:mb-4')
                ui.label('每周一课').classes('text-lg md:text-xl font-bold text-gray-800 mb-2 md:mb-3')
                
                weekly_status_label = ui.label('加载中...').classes('text-sm md:text-base mb-2 md:mb-3')
                weekly_obtained_label = ui.label('0 积分').classes('text-2xl md:text-3xl font-bold text-purple-700')
                
                weekly_name_label = ui.label('每周一课').classes('hidden')
            
            # 每月一考卡片
            with ui.card().classes('p-4 md:p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-xl text-center hover:shadow-md transition-shadow duration-300'):
                ui.icon('calendar_month', size='2.2rem md:3rem').classes('text-green-600 mb-3 md:mb-4')
                ui.label('每月一考').classes('text-lg md:text-xl font-bold text-gray-800 mb-2 md:mb-3')
                
                monthly_status_label = ui.label('加载中...').classes('text-sm md:text-base mb-2 md:mb-3')
                monthly_obtained_label = ui.label('0 积分').classes('text-2xl md:text-3xl font-bold text-green-700')
                
                monthly_name_label = ui.label('每月一考').classes('hidden')
        
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
                daily_name_label.text = daily.get("name", "每日一题")
                daily_status = daily.get("status", "未知")
                daily_status_label.text = daily_status
                # 根据状态设置颜色
                if daily_status == "已完成":
                    daily_status_label.classes('text-green-600 font-semibold')
                else:
                    daily_status_label.classes('text-orange-600 font-semibold')
                daily_obtained_label.text = f'{daily.get("obtained_score", 0)} 积分'
                
                # 更新每周一课信息
                weekly = task_status.get('weekly', {})
                weekly_name_label.text = weekly.get("name", "每周一课")
                weekly_status = weekly.get("status", "未知")
                weekly_status_label.text = weekly_status
                if weekly_status == "已完成":
                    weekly_status_label.classes('text-green-600 font-semibold')
                else:
                    weekly_status_label.classes('text-orange-600 font-semibold')
                weekly_obtained_label.text = f'{weekly.get("obtained_score", 0)} 积分'
                
                # 更新每月一考信息
                monthly = task_status.get('monthly', {})
                monthly_name_label.text = monthly.get("name", "每月一考")
                monthly_status = monthly.get("status", "未知")
                monthly_status_label.text = monthly_status
                if monthly_status == "已完成":
                    monthly_status_label.classes('text-green-600 font-semibold')
                else:
                    monthly_status_label.classes('text-orange-600 font-semibold')
                monthly_obtained_label.text = f'{monthly.get("obtained_score", 0)} 积分'
                
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
        
        with ui.row().classes('w-full justify-end'):
            ui.button('刷新任务状态', on_click=refresh_task_status, icon='refresh').classes('bg-blue-50 hover:bg-blue-100 text-blue-600 font-medium py-1 md:py-2 px-3 md:px-4 rounded-lg shadow-sm text-sm md:text-base')
        
        # 初始加载任务状态
        ui.timer(0.1, lambda: refresh_task_status(), once=True)