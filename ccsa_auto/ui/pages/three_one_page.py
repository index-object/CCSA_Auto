"""三个一任务完成情况页面模块"""
from nicegui import ui
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.models import auth_state


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
            if auth_state.external_token:
                task_status = AuthService.get_task_status(auth_state.external_token)
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
                else:
                    ui.notify('获取任务完成情况失败', type='error')
            else:
                ui.notify('未获取到外部平台令牌', type='error')
        
        ui.button('刷新任务状态', on_click=refresh_task_status).classes('mt-6 bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded')
        
        # 初始加载任务状态
        ui.timer(0.1, lambda: refresh_task_status(), once=True)