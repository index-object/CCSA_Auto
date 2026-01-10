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
from ccsa_auto.ui.pages.admin_login_page import create_admin_login_page
from ccsa_auto.ui.pages.admin_page import create_admin_page
from ccsa_auto.ui.pages.main_page import create_main_page

# 初始化应用
create_tables()
init_admin()
init_scheduler()

# 定义无需认证即可访问的页面路由
unrestricted_page_routes = {'/login', '/admin_login'}

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
# 普通用户登录页面 - 无需认证
@ui.page('/login')
def login_page():
    """普通用户登录页面"""
    def navigate_to_main():
        # 登录成功后导航到主页面
        ui.navigate.to('/')
    
    create_login_page(navigate_to_main)

# 管理员登录页面 - 无需认证
@ui.page('/admin_login')
def admin_login_page():
    """管理员登录页面"""
    def navigate_to_admin(page=None):
        # 登录成功后导航到管理后台
        # 如果传递了page参数，忽略它，直接跳转到/admin
        ui.navigate.to('/admin')
    
    create_admin_login_page(navigate_to_admin)

# 主页面 - 需要认证（普通用户）
@ui.page('/')
def main_page():
    """主页面"""
    # 检查用户是否已认证
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return
    
    # 获取用户信息
    user_info = app.storage.user.get('user_info', {})
    
    # 如果是管理员，重定向到管理后台
    if user_info.get('is_admin'):
        ui.navigate.to('/admin')
        return
    
    def navigate_to(page):
        """导航函数"""
        if page == 'logout':
            # 退出登录
            app.storage.user.clear()
            # 根据用户类型跳转到不同的登录页面
            if user_info.get('is_admin'):
                ui.navigate.to('/admin_login')
            else:
                ui.navigate.to('/login')
        else:
            # 导航到其他页面
            ui.navigate.to(f'/{page}')
    
    with ui.column().classes('w-full'):
        # 顶部导航栏 - 参考样式头部布局
        with ui.card().classes('w-full bg-gradient-to-r from-blue-600 to-blue-900 text-white p-4 rounded-none shadow-lg mb-6 border-0'):
            with ui.row().classes('w-full justify-between items-center'):
                # 左侧logo和标题区域
                with ui.row().classes('items-center gap-4'):
                    ui.icon('quiz', size='1.8rem').classes('text-white')
                    with ui.column().classes('gap-1'):
                        ui.label('用户答题托管平台').classes('text-xl font-bold')
                        ui.label('智能答题，高效学习').classes('text-xs opacity-90')
                
                # 右侧导航和退出按钮
                with ui.row().classes('items-center gap-4'):
                      
                    # 退出登录按钮
                    ui.button('退出登录', on_click=lambda: navigate_to('logout'), icon='logout').classes('bg-white/20 hover:bg-white/30 text-white font-medium py-1 px-3 rounded text-sm')
        
        # 主内容区
        create_main_page(navigate_to)


    
    def logout():
        """退出登录"""
        app.storage.user.clear()
        ui.navigate.to('/login')


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
    if not user_info.get('is_admin'):
        ui.notify('需要管理员权限', type='warning')
        ui.navigate.to('/')
        return
    
    with ui.column().classes('w-full'):
        # 顶部导航栏
        with ui.row().classes('w-full justify-between items-center p-4 bg-gray-100'):
            ui.label('管理员后台').classes('text-xl font-bold')
            ui.button('退出登录', on_click=lambda: logout()).classes('bg-red-500 hover:bg-red-600 text-white font-medium py-1 px-3 rounded text-sm')
        
        # 管理员内容
        create_admin_page()
    
    def logout():
        """退出登录"""
        app.storage.user.clear()
        ui.navigate.to('/admin_login')


# 启动应用
if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='用户答题托管平台',
        port=8082,  # 使用8082端口避免冲突
        storage_secret="ccsa_auto_session_secret_2025"  # 会话存储密钥
    )
