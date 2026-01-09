"""公告页面模块"""
from nicegui import ui
from ccsa_auto.modules.announcement.service import AnnouncementService
from ccsa_auto.modules.auth.models import auth_state


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