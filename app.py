from nicegui import ui
import json
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from ccsa_auto.core import create_tables, init_admin
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.models import auth_state
from ccsa_auto.modules.announcement.service import AnnouncementService
from ccsa_auto.modules.admin.service import AdminService
from ccsa_auto.modules.task.scheduler import init_scheduler

# 初始化应用
create_tables()
init_admin()
init_scheduler()

# 全局变量
current_page = 'login'
page_container = None

# 加载保存的登录状态
def load_login_state():
    """加载登录状态"""
    if os.path.exists('session.json'):
        try:
            with open('session.json', 'r') as f:
                session_data = json.load(f)
                auth_state.set_auth(
                    session_data.get('token'),
                    session_data.get('user_info'),
                    session_data.get('external_token')
                )
                return session_data.get('current_page', 'login')
        except Exception as e:
            print(f"加载会话失败: {e}")
            return 'login'
    return 'login'

# 保存登录状态
def save_login_state(page):
    """保存登录状态"""
    with open('session.json', 'w') as f:
        json.dump({
            'token': auth_state.token,
            'external_token': auth_state.external_token,
            'user_info': auth_state.user_info,
            'current_page': page
        }, f)

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
                create_login_page()
            elif current_page == 'main':
                create_main_page()
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
           

# 登录页面
def create_login_page():
    """创建登录页面"""
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
                auth_state.set_auth(result['access_token'], result['user'], result.get('external_token'))
                # 导航到个人中心页面
                navigate_to('main')
            else:
                ui.notify(message, type='error')
        
        ui.button('登录', on_click=on_login).classes('w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded')

# 个人中心页面
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

# 任务管理页面
def create_task_page():
    """创建任务管理页面"""
    with ui.card().classes('w-full h-auto p-6 page-card task-page'):
        ui.label('任务管理').classes('text-2xl font-bold mb-6')
        
        # 任务列表
        task_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id'},
                {'name': 'task_type', 'label': '任务类型', 'field': 'task_type'},
                {'name': 'execution_status', 'label': '执行状态', 'field': 'execution_status'},
                {'name': 'external_status', 'label': '外部状态', 'field': 'external_status'},
                {'name': 'scheduled_time', 'label': '计划执行时间', 'field': 'scheduled_time'},
                {'name': 'executed_at', 'label': '实际执行时间', 'field': 'executed_at'},
                {'name': 'actions', 'label': '操作', 'field': 'actions'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        # 刷新任务列表
        def refresh_tasks():
            """刷新任务列表"""
            # 这里需要从数据库获取任务列表
            # 暂时返回模拟数据
            tasks = []
            task_table.rows = tasks
        
        # 执行任务
        def execute_task(task_id):
            """执行任务"""
            # 这里需要执行任务
            ui.notify('任务执行成功', type='success')
            refresh_tasks()
        
        # 刷新按钮
        ui.button('刷新任务', on_click=refresh_tasks).classes('mb-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded')
        
        # 初始加载任务
        refresh_tasks()

# 公告页面
def create_announcement_page():
    """创建公告页面"""
    with ui.card().classes('w-full h-auto p-6 page-card announcement-page'):
        ui.label('公告中心').classes('text-2xl font-bold mb-6')
        
        # 公告列表
        announcement_list = ui.row().classes('w-full')
        
        # 加载公告
        def load_announcements():
            """加载公告"""
            result = AnnouncementService.get_announcements()
            if result['success']:
                announcements = result['announcements']
                announcement_list.clear()
                
                for ann in announcements:
                    with announcement_list:
                        with ui.card().classes('w-full p-4 mb-4'):
                            ui.label(ann['title']).classes('text-lg font-semibold')
                            ui.label(ann['content']).classes('mb-2')
                            ui.label(f'发布时间: {ann["created_at"]}').classes('text-sm text-gray-500')
                            # 这里需要检查是否已读
                            ui.button('标记已读', on_click=lambda a=ann: mark_read(a['id'])).classes('mt-2 bg-blue-500 hover:bg-blue-600 text-white font-medium py-1 px-3 rounded')
        
        # 标记公告已读
        def mark_read(announcement_id):
            """标记公告已读"""
            if auth_state.user_info:
                result = AnnouncementService.mark_as_read(announcement_id, auth_state.user_info['id'])
                if result['success']:
                    ui.notify('标记已读成功', type='success')
                    load_announcements()
                else:
                    ui.notify(result['message'], type='error')
        
        # 初始加载公告
        load_announcements()

# 嵌入式个人信息区（用于主页面）
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

# 嵌入式任务区（用于主页面）
def create_task_section():
    """在主页面中嵌入的任务信息区"""
    with ui.card().classes('w-full md:w-1/3 h-auto p-6 bg-white shadow-lg rounded-lg task-section'):
        ui.label('任务管理').classes('text-xl font-bold mb-4 text-gray-700')

        # 简化版任务列表展示
        task_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id'},
                {'name': 'task_type', 'label': '任务类型', 'field': 'task_type'},
                {'name': 'execution_status', 'label': '执行状态', 'field': 'execution_status'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')

        def refresh_tasks():
            """刷新任务列表（嵌入区）"""
            # 从数据库或服务获取任务列表（保留占位）
            tasks = []
            task_table.rows = tasks

        ui.button('刷新任务', on_click=refresh_tasks).classes('mt-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded shadow')
        refresh_tasks()

# 嵌入式公告区（用于主页面）
def create_announcement_section():
    """在主页面中嵌入的公告信息区"""
    with ui.card().classes('w-full md:w-1/3 h-auto p-6 bg-white shadow-lg rounded-lg announcement-section'):
        ui.label('公告中心').classes('text-xl font-bold mb-4 text-gray-700')

        announcement_list = ui.column().classes('space-y-4')

        def load_announcements_embedded():
            result = AnnouncementService.get_announcements()
            if result['success']:
                announcements = result['announcements']
                announcement_list.clear()
                for ann in announcements[:5]:
                    with announcement_list:
                        with ui.card().classes('w-full p-4 bg-gray-50 rounded-lg shadow'):
                            ui.label(ann['title']).classes('text-lg font-semibold text-gray-800')
                            ui.label(ann['content']).classes('text-sm text-gray-600 mb-2')
                            ui.label(f'发布时间: {ann["created_at"]}').classes('text-xs text-gray-500')

        ui.button('刷新公告', on_click=load_announcements_embedded).classes('mt-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded shadow')
        load_announcements_embedded()

# 管理后台页面
def create_admin_page():
    """创建管理后台页面"""
    with ui.card().classes('w-full h-auto p-6 page-card admin-page'):
        ui.label('管理后台').classes('text-2xl font-bold mb-6')
        
        # 管理菜单
        with ui.row().classes('w-full mb-4') as tabs:
            users_tab = ui.button('用户管理')
            tasks_tab = ui.button('任务管理')
            announcements_tab = ui.button('公告管理')
            statistics_tab = ui.button('数据统计')
        
        # 用户管理
        with ui.card().classes('w-full page-card users-tab'):
            ui.label('用户管理').classes('text-xl font-bold mb-4')
            # 用户列表
            user_table = ui.table(
                columns=[
                    {'name': 'id', 'label': 'ID', 'field': 'id'},
                    {'name': 'username', 'label': '账号', 'field': 'username'},
                    {'name': 'company_name', 'label': '公司', 'field': 'company_name'},
                    {'name': 'status', 'label': '状态', 'field': 'status'},
                    {'name': 'created_at', 'label': '创建时间', 'field': 'created_at'},
                    {'name': 'actions', 'label': '操作', 'field': 'actions'}
                ],
                rows=[],
                row_key='id'
            ).classes('w-full')
            
            # 刷新用户列表
            def refresh_users():
                """刷新用户列表"""
                result = AdminService.get_users()
                if result['success']:
                    users = result['users']
                    for user in users:
                        # 转换状态显示
                        user['status'] = '正常' if user['status'] == 0 else '封号'
                        
                        # 添加操作按钮
                        user['actions'] = '编辑' if user['username'] != 'admin' else '无'
                    
                    user_table.rows = users
            
            # 刷新按钮
            ui.button('刷新用户', on_click=refresh_users).classes('mb-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded')
            
            # 初始加载用户
            refresh_users()
        
        # 任务管理
        with ui.card().classes('w-full page-card tasks-tab'):
            ui.label('任务管理').classes('text-xl font-bold mb-4')
            # 任务列表
            admin_task_table = ui.table(
                columns=[
                    {'name': 'id', 'label': 'ID', 'field': 'id'},
                    {'name': 'username', 'label': '用户', 'field': 'username'},
                    {'name': 'task_type', 'label': '任务类型', 'field': 'task_type'},
                    {'name': 'execution_status', 'label': '执行状态', 'field': 'execution_status'},
                    {'name': 'external_status', 'label': '外部状态', 'field': 'external_status'},
                    {'name': 'scheduled_time', 'label': '计划执行时间', 'field': 'scheduled_time'},
                    {'name': 'executed_at', 'label': '实际执行时间', 'field': 'executed_at'}
                ],
                rows=[],
                row_key='id'
            ).classes('w-full')
            
            # 刷新任务列表
            def refresh_admin_tasks():
                """刷新任务列表"""
                result = AdminService.get_all_tasks()
                if result['success']:
                    tasks = result['tasks']
                    for task in tasks:
                        # 转换任务类型显示
                        task_type_map = {
                            'daily': '每日一题',
                            'weekly': '每周一课',
                            'monthly': '每月一考'
                        }
                        task['task_type'] = task_type_map.get(task['task_type'], task['task_type'])
                        
                        # 转换执行状态显示
                        execution_status_map = {
                            'pending': '待执行',
                            'running': '执行中',
                            'completed': '已完成'
                        }
                        task['execution_status'] = execution_status_map.get(task['execution_status'], task['execution_status'])
                        
                        # 转换外部状态显示
                        external_status_map = {
                            'success': '成功',
                            'failed': '失败',
                            'unknown': '未知'
                        }
                        task['external_status'] = external_status_map.get(task['external_status'], task['external_status'])
                    
                    admin_task_table.rows = tasks
            
            # 刷新按钮
            ui.button('刷新任务', on_click=refresh_admin_tasks).classes('mb-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded')
            
            # 初始加载任务
            refresh_admin_tasks()
        
        # 公告管理
        with ui.card().classes('w-full page-card announcements-tab'):
            ui.label('公告管理').classes('text-xl font-bold mb-4')
            # 创建公告表单
            title = ui.input('标题').classes('w-full mb-4')
            content = ui.textarea('内容').classes('w-full mb-4')
            
            def create_announcement():
                """创建公告"""
                if title.value and content.value:
                    result = AnnouncementService.create_announcement(title.value, content.value)
                    if result['success']:
                        ui.notify('公告发布成功', type='success')
                        title.value = ''
                        content.value = ''
                    else:
                        ui.notify(result['message'], type='error')
                else:
                    ui.notify('标题和内容不能为空', type='error')
            
            ui.button('发布', on_click=create_announcement).classes('bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded')
        
        # 数据统计
        with ui.card().classes('w-full page-card statistics-tab'):
            ui.label('数据统计').classes('text-xl font-bold mb-4')
            # 统计数据
            def show_statistics():
                """显示统计数据"""
                result = AdminService.get_statistics()
                if result['success']:
                    data = result['data']
                    with ui.row().classes('gap-4'):
                        # 用户统计
                        with ui.card().classes('p-4'):
                            ui.label('用户统计').classes('text-lg font-semibold mb-2')
                            ui.label(f'总用户: {data["users"]["total"]}')
                            ui.label(f'活跃用户: {data["users"]["active"]}')
                            ui.label(f'封号用户: {data["users"]["banned"]}')
                        
                        # 任务统计
                        with ui.card().classes('p-4'):
                            ui.label('任务统计').classes('text-lg font-semibold mb-2')
                            ui.label(f'总任务: {data["tasks"]["total"]}')
                            ui.label(f'待执行: {data["tasks"]["pending"]}')
                            ui.label(f'已完成: {data["tasks"]["completed"]}')
                        
                        # 公告统计
                        with ui.card().classes('p-4'):
                            ui.label('公告统计').classes('text-lg font-semibold mb-2')
                            ui.label(f'总公告: {data["announcements"]["total"]}')
            
            # 初始加载统计数据
            show_statistics()

# 三个一任务完成情况页面
def create_three_one_page():
    """创建三个一任务完成情况页面"""
    with ui.card().classes('w-full h-auto p-6 page-card three-one-page'):
        ui.label('三个一任务完成情况').classes('text-2xl font-bold mb-6')
        
        # 创建三个任务卡片
        with ui.row().classes('w-full gap-6'):
            # 每日一题卡片
            with ui.card().classes('flex-1 p-4'):
                ui.label('每日一题').classes('text-xl font-semibold mb-4')
                
                # 创建占位符标签
                daily_name_label = ui.label('任务名称: 加载中...').classes('text-gray-600')
                daily_status_label = ui.label('完成状态: 加载中...').classes('text-gray-600')
                daily_score_label = ui.label('可获得积分: 加载中...').classes('text-gray-600')
                daily_obtained_label = ui.label('已获得积分: 加载中...').classes('text-gray-600')
            
            # 每周一课卡片
            with ui.card().classes('flex-1 p-4'):
                ui.label('每周一课').classes('text-xl font-semibold mb-4')
                
                weekly_name_label = ui.label('任务名称: 加载中...').classes('text-gray-600')
                weekly_status_label = ui.label('完成状态: 加载中...').classes('text-gray-600')
                weekly_score_label = ui.label('可获得积分: 加载中...').classes('text-gray-600')
                weekly_obtained_label = ui.label('已获得积分: 加载中...').classes('text-gray-600')
            
            # 每月一考卡片
            with ui.card().classes('flex-1 p-4'):
                ui.label('每月一考').classes('text-xl font-semibold mb-4')
                
                monthly_name_label = ui.label('任务名称: 加载中...').classes('text-gray-600')
                monthly_status_label = ui.label('完成状态: 加载中...').classes('text-gray-600')
                monthly_score_label = ui.label('可获得积分: 加载中...').classes('text-gray-600')
                monthly_obtained_label = ui.label('已获得积分: 加载中...').classes('text-gray-600')
        
        # 刷新按钮
        def refresh_task_status():
            """刷新任务完成情况"""
            if auth_state.external_token:
                task_status = AuthService.get_task_status(auth_state.external_token)
                if task_status:
                    # 更新每日一题信息
                    daily = task_status.get('daily', {})
                    daily_name_label.text = f'任务名称: {daily.get("name", "每日一题")}'
                    daily_status_label.text = f'完成状态: {daily.get("status", "未知")}'
                    daily_score_label.text = f'可获得积分: {daily.get("available_score", 0)}'
                    daily_obtained_label.text = f'已获得积分: {daily.get("obtained_score", 0)}'
                    
                    # 更新每周一课信息
                    weekly = task_status.get('weekly', {})
                    weekly_name_label.text = f'任务名称: {weekly.get("name", "每周一课")}'
                    weekly_status_label.text = f'完成状态: {weekly.get("status", "未知")}'
                    weekly_score_label.text = f'可获得积分: {weekly.get("available_score", 0)}'
                    weekly_obtained_label.text = f'已获得积分: {weekly.get("obtained_score", 0)}'
                    
                    # 更新每月一考信息
                    monthly = task_status.get('monthly', {})
                    monthly_name_label.text = f'任务名称: {monthly.get("name", "每月一考")}'
                    monthly_status_label.text = f'完成状态: {monthly.get("status", "未知")}'
                    monthly_score_label.text = f'可获得积分: {monthly.get("available_score", 0)}'
                    monthly_obtained_label.text = f'已获得积分: {monthly.get("obtained_score", 0)}'
                else:
                    ui.notify('获取任务完成情况失败', type='error')
            else:
                ui.notify('未获取到外部平台令牌', type='error')
        
        ui.button('刷新任务状态', on_click=refresh_task_status).classes('mt-6 bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded')
        
        # 初始加载任务状态
        ui.timer(0.1, lambda: refresh_task_status(), once=True)

# 主页面
def create_main_page():
    """创建主页面"""
    with ui.card().classes('w-full items-center justify-center'):
        ui.label('欢迎使用用户答题托管平台').classes('text-3xl font-extrabold text-center mb-8 text-gray-800')

        # 将个人中心、任务管理、公告垂直排列展示在主页面
        with ui.column().classes('w-full items-center justify-center'):
            create_profile_section()
            create_task_section()
            create_announcement_section()

        # 添加三个一任务完成情况按钮
        ui.button('三个一任务完成情况', on_click=lambda: navigate_to('three_one')).classes('mt-6 bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-6 rounded-lg shadow')
        
        # 保留管理员入口按钮（针对管理员用户）
        if auth_state.user_info and auth_state.user_info.get('username') == 'admin':
            ui.button('管理后台', on_click=lambda: navigate_to('admin')).classes('mt-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg shadow')

# 退出登录
def logout():
    """退出登录"""
    auth_state.clear_auth()
    
    # 清除会话文件
    if os.path.exists('session.json'):
        try:
            os.remove('session.json')
        except Exception as e:
            print(f"清除会话失败: {e}")
    
    # 导航到登录页面
    navigate_to('login')

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
                ui.button('退出登录', on_click=logout).classes('bg-red-500 hover:bg-red-600 text-white font-medium py-1 px-3 rounded text-sm')
        
        # 内容区
        with ui.column().classes('w-full') as container:
            page_container = container
            # 根据当前页面显示相应内容
            if current_page == 'login':
                create_login_page()
            elif current_page == 'main':
                create_main_page()
            elif current_page == 'profile':
                create_profile_page()
            elif current_page == 'task':
                create_task_page()
            elif current_page == 'announcement':
                create_announcement_page()
            elif current_page == 'admin':
                create_admin_page()

# 启动应用
if __name__ in {'__main__', '__mp_main__'}:
    create_main_app()
    ui.run(title='用户答题托管平台', port=8081)
