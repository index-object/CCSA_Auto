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
    
    # 主内容区域 - 使用响应式网格布局
    with ui.grid(columns='1fr 2fr').classes('w-full gap-6'):
        # 左侧区域
        with ui.column().classes('gap-6'):
            create_announcement_section()
            create_profile_section()
        
        # 右侧区域
        with ui.column().classes('gap-6'):
            create_three_one_page()
            create_task_section()
    
    # 响应式布局：在小屏幕上改为单列布局
    ui.query('.nicegui-grid').classes('lg:grid-cols-1 md:grid-cols-2')
    
    # 底部区域
    with ui.card().classes('w-full mt-8 text-center text-gray-600 text-sm bg-gray-50 p-4 rounded-lg shadow-sm'):
        ui.label('陕西精益化工有限公司 用户答题托管平台 © 2026 | 数据更新时间: ' + datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    # 保留管理员入口按钮（针对管理员用户）
    if user_info.get('username') == 'admin':
        with ui.row().classes('w-full justify-center mt-6'):
            ui.button('管理后台', on_click=lambda: navigate_to('admin')).classes('bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg shadow-lg')