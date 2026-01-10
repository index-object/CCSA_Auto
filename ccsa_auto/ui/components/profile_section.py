"""个人信息区组件模块 - 基于app.storage.user的会话隔离版本"""
from nicegui import ui, app
from ccsa_auto.modules.auth.service import AuthService


def create_profile_section():
    """在主页面中嵌入的个人信息区"""
    with ui.card().classes('w-full h-auto p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300'):
        with ui.row().classes('items-center gap-2 mb-6 pb-4 border-b-2 border-gray-100'):
            ui.icon('person', size='1.5rem').classes('text-blue-600')
            ui.label('个人信息').classes('text-xl font-bold text-blue-600')
        
        # 用户头像和信息区域
        with ui.row().classes('w-full items-center gap-6 mb-6'):
            # 头像区域
            with ui.column().classes('items-center'):
                user_info = app.storage.user.get('user_info', {})
                username = user_info.get('username', '用户')
                avatar_text = username[0] if username else '用'
                
                with ui.card().classes('w-20 h-20 bg-gradient-to-br from-blue-400 to-blue-700 rounded-full flex items-center justify-center shadow-md'):
                    ui.label(avatar_text).classes('text-2xl font-bold text-white')
                
                ui.label(username).classes('text-lg font-semibold text-gray-800 mt-2')
            
            # 用户详细信息
            with ui.column().classes('flex-1 gap-3'):
                if user_info:
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('badge', size='1rem').classes('text-gray-500')
                        ui.label(f'账号: {user_info.get("username", "未知")}').classes('text-gray-700')
                    
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('business', size='1rem').classes('text-gray-500')
                        ui.label(f'公司: {user_info.get("company_name") or "-"}').classes('text-gray-700')
                else:
                    ui.label('未登录').classes('text-gray-500')
        
        # 积分信息卡片
        with ui.row().classes('w-full gap-4 mb-4'):
            # 本年总积分卡片
            with ui.card().classes('flex-1 p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg text-center'):
                ui.label('本年总积分').classes('text-sm text-gray-600 mb-2')
                total_score_label = ui.label('加载中...').classes('text-3xl font-bold text-blue-700')
            
            # 当月积分卡片
            with ui.card().classes('flex-1 p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg text-center'):
                ui.label('当月积分').classes('text-sm text-gray-600 mb-2')
                monthly_score_label = ui.label('加载中...').classes('text-3xl font-bold text-green-700')
        
        # 异步加载积分信息
        async def load_scores_embedded():
            # 从app.storage.user获取外部令牌
            external_token = app.storage.user.get('external_token')
            if external_token:
                scores = AuthService.get_scores(external_token)
                if scores:
                    total_score_label.text = str(scores.get('total_score', 0))
                    monthly_score_label.text = str(scores.get('monthly_score', 0))
                else:
                    total_score_label.text = '0'
                    monthly_score_label.text = '0'
            else:
                total_score_label.text = '0'
                monthly_score_label.text = '0'
        
        ui.timer(0.1, lambda: load_scores_embedded(), once=True)