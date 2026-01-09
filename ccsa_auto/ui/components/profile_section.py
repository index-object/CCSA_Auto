"""个人信息区组件模块"""
from nicegui import ui
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.models import auth_state


def create_profile_section():
    """在主页面中嵌入的个人信息区"""
    with ui.card().classes('w-full md:w-1/3 h-auto p-6 bg-white shadow-lg rounded-lg profile-section'):
        ui.label('个人信息').classes('text-xl font-bold mb-4 text-gray-700')
        if auth_state.user_info:
            ui.label(f'账号: {auth_state.user_info.get("username")}').classes('text-gray-600')
            ui.label(f'公司: {auth_state.user_info.get("company_name") or "-"}').classes('text-gray-600')
        else:
            ui.label('未登录').classes('text-gray-500')
        ui.separator().classes('my-4')
        with ui.row().classes('justify-between'):
            with ui.column():
                ui.label('积分信息').classes('text-sm font-semibold text-gray-700')
                
                # 创建占位符标签，稍后更新
                total_score_label = ui.label('本年总积分: 加载中...').classes('text-gray-600')
                monthly_score_label = ui.label('当月积分: 加载中...').classes('text-gray-600')
                
                # 异步加载积分信息
                async def load_scores_embedded():
                    if auth_state.external_token:
                        scores = AuthService.get_scores(auth_state.external_token)
                        if scores:
                            total_score_label.text = f'本年总积分: {scores["total_score"]}'
                            monthly_score_label.text = f'当月积分: {scores["monthly_score"]}'
                        else:
                            total_score_label.text = '本年总积分: 加载失败'
                            monthly_score_label.text = '当月积分: 加载失败'
                    else:
                        total_score_label.text = '本年总积分: 无令牌'
                        monthly_score_label.text = '当月积分: 无令牌'
                
                ui.timer(0.1, lambda: load_scores_embedded(), once=True)