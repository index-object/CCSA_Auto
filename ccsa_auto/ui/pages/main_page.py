"""主页面模块"""
from nicegui import ui
from ccsa_auto.modules.auth.models import auth_state
from ccsa_auto.ui.components.profile_section import create_profile_section
from ccsa_auto.ui.components.task_section import create_task_section
from ccsa_auto.ui.components.announcement_section import create_announcement_section
from ccsa_auto.ui.pages.three_one_page import create_three_one_page


def create_main_page(navigate_to):
    """创建主页面
    
    Args:
        navigate_to: 导航函数，用于页面跳转
    """
    with ui.card().classes('w-full items-center justify-center'):
        ui.label('欢迎使用用户答题托管平台').classes('text-3xl font-extrabold text-center mb-8 text-gray-800')

        # 将个人中心、任务管理、公告垂直排列展示在主页面
        with ui.column().classes('w-full items-center justify-center'):
            create_announcement_section()
            create_profile_section()
            create_three_one_page()
            create_task_section()
           

        # 保留管理员入口按钮（针对管理员用户）
        if auth_state.user_info and auth_state.user_info.get('username') == 'admin':
            ui.button('管理后台', on_click=lambda: navigate_to('admin')).classes('mt-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg shadow')