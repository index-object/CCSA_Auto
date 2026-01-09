"""应用主入口 - 模块化重构后的应用入口"""
from nicegui import ui
import json
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from ccsa_auto.core import create_tables, init_admin
from ccsa_auto.modules.auth.models import auth_state
from ccsa_auto.modules.task.scheduler import init_scheduler

# 导入UI模块
from ccsa_auto.ui.core.app_core import load_login_state, save_login_state, logout
from ccsa_auto.ui.pages.login_page import create_login_page
from ccsa_auto.ui.pages.profile_page import create_profile_page
from ccsa_auto.ui.pages.task_page import create_task_page
from ccsa_auto.ui.pages.announcement_page import create_announcement_page
from ccsa_auto.ui.pages.admin_page import create_admin_page
from ccsa_auto.ui.pages.three_one_page import create_three_one_page
from ccsa_auto.ui.pages.main_page import create_main_page

# 初始化应用
create_tables()
init_admin()
init_scheduler()

# 全局变量
current_page = 'login'
page_container = None


# 导航函数
def navigate_to(page):
    """导航到指定页面"""
    global current_page
    current_page = page
    
    # 保存登录状态
    save_login_state(page)
    
    # 刷新页面内容
    refresh_page()


# 刷新页面内容
def refresh_page():
    """刷新页面内容"""
    global page_container
    if page_container:
        # 清除现有内容
        page_container.clear()
        
        # 根据当前页面显示相应内容
        with page_container:
            if current_page == 'login':
                create_login_page(navigate_to)
            elif current_page == 'main':
                create_main_page(navigate_to)
            elif current_page == 'profile':
                create_profile_page()
            elif current_page == 'task':
                create_task_page()
            elif current_page == 'announcement':
                create_announcement_page()
            elif current_page == 'admin':
                create_admin_page()
            elif current_page == 'three_one':
                create_three_one_page()


# 主应用布局
def create_main_app():
    """创建主应用布局"""
    
    # 加载登录状态
    global current_page
    current_page = load_login_state()
    
    # 创建页面容器
    global page_container
    
    # 创建页面容器
    with ui.column().classes('w-full'):
        # 顶部导航栏
        if auth_state.is_authenticated:
            with ui.row().classes('row w-full'):
                ui.label('用户答题托管平台').classes('text-xl font-bold')
                ui.button('退出登录', on_click=lambda: navigate_to(logout())).classes('bg-red-500 hover:bg-red-600 text-white font-medium py-1 px-3 rounded text-sm')
        
        # 内容区
        with ui.column().classes('w-full') as container:
            page_container = container
            # 根据当前页面显示相应内容
            if current_page == 'login':
                create_login_page(navigate_to)
            elif current_page == 'main':
                create_main_page(navigate_to)
            elif current_page == 'profile':
                create_profile_page()
            elif current_page == 'task':
                create_task_page()
            elif current_page == 'announcement':
                create_announcement_page()
            elif current_page == 'admin':
                create_admin_page()
            elif current_page == 'three_one':
                create_three_one_page()


# 启动应用
if __name__ in {'__main__', '__mp_main__'}:
    create_main_app()
    ui.run(title='用户答题托管平台', port=8081)
