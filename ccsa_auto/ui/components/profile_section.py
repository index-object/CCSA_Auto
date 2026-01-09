"""个人信息区组件模块 - 基于app.storage.user的会话隔离版本"""
from nicegui import ui, app
from ccsa_auto.modules.auth.service import AuthService


def create_profile_section():
    """在主页面中嵌入的个人信息区"""
    with ui.card().classes('w-full md:w-1/3 h-auto p-6 bg-white shadow-lg rounded-lg profile-section'):
        
        # 使用水平布局包含两组信息
        with ui.row().classes('w-full justify-between items-start'):
            # 第一组：账号和公司信息（垂直排列）
            with ui.column().classes('flex-1'):
                ui.label('个人信息').classes('text-xl font-bold mb-4 text-gray-700')

                # 从app.storage.user获取用户信息
                user_info = app.storage.user.get('user_info', {})
                if user_info:
                    ui.label(f'账号: {user_info.get("username", "未知")}').classes('text-gray-600 text-sm')
                    ui.label(f'公司: {user_info.get("company_name") or "-"}').classes('text-gray-600 text-sm')
                else:
                    ui.label('未登录').classes('text-gray-500 text-sm')
            
            # 第二组：积分信息（垂直排列）
            with ui.column().classes('flex-1'):
                ui.label('积分信息').classes('text-xl font-bold mb-4 text-gray-700')
                
                # 创建占位符标签，稍后更新
                total_score_label = ui.label('本年总积分: 加载中...').classes('text-gray-600 text-sm')
                monthly_score_label = ui.label('当月积分: 加载中...').classes('text-gray-600 text-sm')
                
                # 异步加载积分信息
                async def load_scores_embedded():
                    # 从app.storage.user获取外部令牌
                    external_token = app.storage.user.get('external_token')
                    if external_token:
                        scores = AuthService.get_scores(external_token)
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