"""管理员登录页面模块"""
from nicegui import ui, app
from ccsa_auto.modules.auth.service import AuthService


def create_admin_login_page(navigate_to):
    """创建管理员登录页面
    
    Args:
        navigate_to: 导航函数，用于页面跳转
    """
    # 应用全局样式
   # 创建渐变背景容器
    with ui.element('div').classes('w-full min-h-screen bg-gradient-to-br from-slate-50 via-red-50 to-pink-50 flex items-center justify-center p-4'):
        with ui.card().classes('w-full max-w-md p-8 rounded-2xl shadow-2xl card-hover'):
            ui.label('管理员后台登录').classes('text-3xl font-bold text-center text-gray-800 mb-2')
            ui.label('请输入管理员账号信息').classes('text-center text-gray-600 mb-6')
            
            admin_username_input = ui.input('管理员账号', placeholder='请输入管理员账号').classes(
                'w-full mb-4 px-4 py-3 rounded-lg border border-gray-300 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-200 transition-all'
            )
            
            admin_password_input = ui.input('管理员密码', placeholder='请输入管理员密码', password=True).classes(
                'w-full mb-6 px-4 py-3 rounded-lg border border-gray-300 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-200 transition-all'
            )
            
            # 登录处理
            async def handle_admin_login():
                """处理管理员登录"""
                admin_username = admin_username_input.value.strip()
                admin_password = admin_password_input.value.strip()
                
                if not admin_username or not admin_password:
                    ui.notify('请输入管理员账号和密码', type='warning')
                    return
                
                success, result, message = AuthService.login(admin_username, admin_password)
                if success:
                    # 检查是否为管理员
                    if not result['user'].get('is_admin'):
                        ui.notify('非管理员账号，请使用普通用户登录', type='error')
                        return
                    
                    # 存储管理员信息到会话
                    app.storage.user.update({
                        'authenticated': True,
                        'is_admin': True,
                        'user_info': result['user'],
                        'access_token': result['access_token'],
                        'user_id': result['user']['id'],
                        'external_token': result.get('external_token')
                    })
                    
                    print(f"管理员 {result['user']['username']} 登录成功")
                    ui.notify('管理员登录成功', type='success')
                    navigate_to('admin')
                else:
                    ui.notify(message, type='error')
            
            ui.button('管理员登录', on_click=handle_admin_login).classes(
                'w-full bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition-all duration-300 transform hover:scale-[1.02]'
            )
            
            # 普通用户登录链接
            with ui.row().classes('w-full justify-center mt-4'):
                ui.label('返回普通用户登录').classes('text-gray-600 mr-2')
                # 将链接目标设为字符串路径，避免把函数对象写入组件属性导致序列化失败
                ui.link('点击这里', '/login').classes(
                    'text-blue-600 hover:text-blue-800 font-medium transition-colors'
                )