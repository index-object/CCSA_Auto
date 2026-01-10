"""登录页面模块 - 基于app.storage.user的会话隔离版本"""
from nicegui import ui, app
from ccsa_auto.modules.auth.service import AuthService


def create_login_page(navigate_to):
    """创建登录页面
    
    Args:
        navigate_to: 导航函数，用于页面跳转
    """
    with ui.card().classes('w-96 h-auto mx-auto my-auto p-6 shadow-lg rounded-lg page-card login-page'):
        ui.label('用户答题托管平台').classes('text-2xl font-bold text-center mb-6')
        
        username = ui.input('外部平台账号').classes('w-full mb-4')
        password = ui.input('外部平台密码', password=True).classes('w-full mb-6')
        
        async def on_login(e):
            """登录处理"""
            data = {
                'username': username.value,
                'password': password.value
            }
            
            # 调用认证服务
            success, result, message = AuthService.login(data['username'], data['password'])
            if success:
                # 将用户信息存储到app.storage.user中
                app.storage.user.update({
                    'authenticated': True,
                    'is_admin': False,  # 明确设置为非管理员
                    'user_info': result['user'],
                    'access_token': result['access_token'],
                    'external_token': result.get('external_token'),
                    'user_id': result['user']['id']
                })
                
                print(f"用户 {result['user']['username']} 登录成功")
                
                # 导航到主页面
                navigate_to()
            else:
                ui.notify(message, type='error')
        
        ui.button('登录', on_click=on_login).classes('w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded')