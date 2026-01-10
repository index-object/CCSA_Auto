"""公告信息区组件模块"""
from nicegui import ui
from ccsa_auto.modules.announcement.service import AnnouncementService


def create_announcement_section():
    """在主页面中嵌入的公告信息区"""
    with ui.card().classes('w-full h-auto p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300'):
        with ui.row().classes('items-center gap-2 mb-6 pb-4 border-b-2 border-gray-100'):
            ui.icon('campaign', size='1.5rem').classes('text-blue-600')
            ui.label('公告中心').classes('text-xl font-bold text-blue-600')
        
        announcement_list = ui.column().classes('space-y-3')

        def load_announcements_embedded():
            result = AnnouncementService.get_announcements()
            if result['success']:
                announcements = result['announcements']
                announcement_list.clear()
                for ann in announcements[:5]:
                    with announcement_list:
                        with ui.row().classes('w-full p-4 items-center hover:bg-gray-50 rounded-lg transition-colors duration-200'):
                            ui.icon('newspaper', size='1.2rem').classes('text-blue-500 mr-3')
                            with ui.column().classes('flex-1'):
                                ui.label(ann['title']).classes('text-base font-semibold text-gray-800')
                                ui.label(ann['content']).classes('text-sm text-gray-600')
                            ui.label(ann['created_at'][5:10] if len(ann['created_at']) >= 10 else ann['created_at']).classes('text-xs text-gray-500')
            else:
                with announcement_list:
                    ui.label('暂无公告').classes('text-gray-500 text-center py-4')

        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('刷新公告', on_click=load_announcements_embedded, icon='refresh').classes('bg-blue-50 hover:bg-blue-100 text-blue-600 font-medium py-2 px-4 rounded-lg shadow-sm')
        
        load_announcements_embedded()