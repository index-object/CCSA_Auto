"""个人中心页面模块"""
from nicegui import ui
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.models import auth_state


def create_profile_page():
    """创建个人中心页面"""
    with ui.card().classes('w-full h-auto p-6 page-card profile-page'):
        ui.label('个人中心').classes('text-2xl font-bold mb-6')
        
        with ui.row().classes('gap-6'):
            # 个人信息卡片
            with ui.card().classes('p-4'):
                ui.label('个人信息').classes('text-lg font-semibold mb-4')
                if auth_state.user_info:
                    ui.label(f'账号: {auth_state.user_info["username"]}')
                    ui.label(f'公司: {auth_state.user_info["company_name"]}')
                else:
                    ui.label('未登录')
            
            # 积分卡片
            with ui.card().classes('p-4'):
                ui.label('积分信息').classes('text-lg font-semibold mb-4')
                
                # 调用服务获取积分信息
                async def load_scores():
                    # 使用外部访问令牌获取积分信息
                    if auth_state.external_token:
                        scores = AuthService.get_scores(auth_state.external_token)
                        if scores:
                            ui.label(f'本年总积分: {scores["total_score"]}')
                            ui.label(f'当月积分: {scores["monthly_score"]}')
                        else:
                            ui.label('积分信息加载失败')
                    else:
                        ui.label('未获取到外部平台令牌')
                
                # 异步加载积分信息 - 使用timer立即执行
                ui.timer(0.1, lambda: load_scores(), once=True)