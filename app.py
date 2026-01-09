"""应用主入口 - 基于NiceGUI会话隔离的重构版本"""
from nicegui import ui, app
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from ccsa_auto.core import create_tables, init_admin
from ccsa_auto.modules.task.scheduler import init_scheduler

# 导入UI模块
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

# 定义无需认证即可访问的页面路由
unrestricted_page_routes = {'/login', '/register'}

class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件 - 限制对需要认证的页面的访问
    
    如果用户未登录且尝试访问需要认证的页面，则重定向到登录页面
    """
    
    async def dispatch(self, request: Request, call_next):
        # 检查用户是否已认证
        if not app.storage.user.get('authenticated', False):
            # 如果未登录，并且页面需要登录后可见，就重定向到login页面
            # 获取所有已注册的页面路由
            page_routes = set()
            for route in app.routes:
                if hasattr(route, 'path'):
                    page_routes.add(route.path)
            
            if request.url.path in page_routes and request.url.path not in unrestricted_page_routes:
                app.storage.user['referrer_path'] = request.url.path
                return RedirectResponse('/login')
        return await call_next(request)

# 挂载认证中间件
app.add_middleware(AuthMiddleware)
# 登录页面 - 无需认证
@ui.page('/login')
def login_page():
    """登录页面"""
    def navigate_to_main():
        # 登录成功后导航到主页面
        ui.navigate.to('/')
    
    create_login_page(navigate_to_main)

# 主页面 - 需要认证
@ui.page('/')
def main_page():
    """主页面"""
    # 检查用户是否已认证
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return
    
    # 获取用户信息
    user_info = app.storage.user.get('user_info', {})
    
    def navigate_to(page):
        """导航函数"""
        if page == 'logout':
            # 退出登录
            app.storage.user.clear()
            ui.navigate.to('/login')
        else:
            # 导航到其他页面
            ui.navigate.to(f'/{page}')
    
    with ui.column().classes('w-full'):
        # 顶部导航栏
        with ui.row().classes('w-full justify-between items-center p-4 bg-gray-100'):
            ui.label('用户答题托管平台').classes('text-xl font-bold')
            ui.button('退出登录', on_click=lambda: navigate_to('logout')).classes('bg-red-500 hover:bg-red-600 text-white font-medium py-1 px-3 rounded text-sm')
        
        # 主内容区
        create_main_page(navigate_to)

# 个人中心页面 - 需要认证
@ui.page('/profile')
def profile_page():
    """个人中心页面"""
    # 检查用户是否已认证
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return
    
    with ui.column().classes('w-full'):
        # 顶部导航栏
        with ui.row().classes('w-full justify-between items-center p-4 bg-gray-100'):
            ui.label('个人中心').classes('text-xl font-bold')
            ui.button('返回首页', on_click=lambda: ui.navigate.to('/')).classes('bg-blue-500 hover:bg-blue-600 text-white font-medium py-1 px-3 rounded text-sm')
        
        # 个人中心内容
        create_profile_page()

# 任务管理页面 - 需要认证
@ui.page('/task')
def task_page():
    """任务管理页面"""
    # 检查用户是否已认证
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return
    
    with ui.column().classes('w-full'):
        # 顶部导航栏
        with ui.row().classes('w-full justify-between items-center p-4 bg-gray-100'):
            ui.label('任务管理').classes('text-xl font-bold')
            ui.button('返回首页', on_click=lambda: ui.navigate.to('/')).classes('bg-blue-500 hover:bg-blue-600 text-white font-medium py-1 px-3 rounded text-sm')
        
        # 任务管理内容
        create_task_page()

# 公告页面 - 需要认证
@ui.page('/announcement')
def announcement_page():
    """公告页面"""
    # 检查用户是否已认证
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return
    
    with ui.column().classes('w-full'):
        # 顶部导航栏
        with ui.row().classes('w-full justify-between items-center p-4 bg-gray-100'):
            ui.label('公告管理').classes('text-xl font-bold')
            ui.button('返回首页', on_click=lambda: ui.navigate.to('/')).classes('bg-blue-500 hover:bg-blue-600 text-white font-medium py-1 px-3 rounded text-sm')
        
        # 公告内容
        create_announcement_page()

# 管理员页面 - 需要认证且需要管理员权限
@ui.page('/admin')
def admin_page():
    """管理员页面"""
    # 检查用户是否已认证
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return
    
    # 检查是否为管理员
    user_info = app.storage.user.get('user_info', {})
    if user_info.get('username') != 'admin':
        ui.notify('需要管理员权限', type='warning')
        ui.navigate.to('/')
        return
    
    with ui.column().classes('w-full'):
        # 顶部导航栏
        with ui.row().classes('w-full justify-between items-center p-4 bg-gray-100'):
            ui.label('管理员后台').classes('text-xl font-bold')
            ui.button('返回首页', on_click=lambda: ui.navigate.to('/')).classes('bg-blue-500 hover:bg-blue-600 text-white font-medium py-1 px-3 rounded text-sm')
        
        # 管理员内容
        create_admin_page()

# 三个一页面 - 需要认证
@ui.page('/three_one')
def three_one_page():
    """三个一页面"""
    # 检查用户是否已认证
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return
    
    with ui.column().classes('w-full'):
        # 顶部导航栏
        with ui.row().classes('w-full justify-between items-center p-4 bg-gray-100'):
            ui.label('三个一学习').classes('text-xl font-bold')
            ui.button('返回首页', on_click=lambda: ui.navigate.to('/')).classes('bg-blue-500 hover:bg-blue-600 text-white font-medium py-1 px-3 rounded text-sm')
        
        # 三个一内容
        create_three_one_page()

# 启动应用
if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='用户答题托管平台',
        port=8082,  # 使用8082端口避免冲突
        storage_secret="ccsa_auto_session_secret_2025"  # 会话存储密钥
    )
