"""公告信息区组件模块"""
from nicegui import ui
from ccsa_auto.modules.announcement.service import AnnouncementService


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