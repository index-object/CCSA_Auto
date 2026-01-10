"""主页面模块 - 基于app.storage.user的会话隔离版本"""
from nicegui import ui, app
from ccsa_auto.ui.components.profile_section import create_profile_section
from ccsa_auto.ui.components.task_section import create_task_section
from ccsa_auto.ui.components.announcement_section import create_announcement_section
from ccsa_auto.ui.pages.three_one_page import create_three_one_page
from datetime import datetime


def create_main_page(navigate_to):
    """创建主页面
    
    Args:
        navigate_to: 导航函数，用于页面跳转
    """
    # 获取用户信息
    user_info = app.storage.user.get('user_info', {})
    username = user_info.get('username', '用户')
    
    # 头部区域 - 参考样式中的header（使用卡片而不是header布局元素）
    with ui.card().classes('w-full bg-gradient-to-r from-blue-600 to-blue-900 text-white p-6 rounded-xl shadow-lg mb-8 border-0'):
        with ui.row().classes('w-full justify-between items-center'):
            # 左侧logo和标题区域
            with ui.row().classes('items-center gap-4'):
                ui.icon('school', size='2rem').classes('text-white')
                with ui.column().classes('gap-1'):
                    ui.label('员工学习平台').classes('text-2xl font-bold')
                    ui.label('知识积累，积分成长').classes('text-sm opacity-90')
            
            # 右侧日期信息
            with ui.column().classes('text-right'):
                current_date = datetime.now().strftime('%Y年%m月%d日 %A')
                ui.label(current_date).classes('text-lg font-semibold')
                ui.label('数据实时更新').classes('text-sm opacity-90')
    
    # 主内容区域 - 使用网格布局
    with ui.row().classes('w-full gap-6'):
        # 左侧区域 - 占1/3宽度
        with ui.column().classes('w-full md:w-1/3 gap-6'):
            create_announcement_section()
            create_profile_section()
        
        # 右侧区域 - 占2/3宽度
        with ui.column().classes('w-full md:w-2/3 gap-6'):
            create_three_one_page()
            create_task_section()
    
    # 底部区域（使用卡片而不是footer布局元素）
    with ui.card().classes('w-full mt-8 text-center text-gray-600 text-sm bg-gray-50 p-4 rounded-lg shadow-sm'):
        ui.label('陕西精益化工有限公司 员工学习平台 © 2026 | 数据更新时间: ' + datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    # 保留管理员入口按钮（针对管理员用户）
    if user_info.get('username') == 'admin':
        with ui.row().classes('w-full justify-center mt-6'):
            ui.button('管理后台', on_click=lambda: navigate_to('admin')).classes('bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg shadow-lg')