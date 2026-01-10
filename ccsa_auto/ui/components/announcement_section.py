"""公告信息区组件模块"""
from nicegui import ui
from ccsa_auto.modules.announcement.service import AnnouncementService


def create_announcement_section():
    """在主页面中嵌入的公告信息区"""
    with ui.card().classes('w-full h-auto p-5 md:p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300'):
        with ui.row().classes('items-center gap-3 mb-5 md:mb-6 pb-4 border-b-2 border-gray-100'):
            ui.icon('campaign', size='1.5rem md:1.8rem').classes('text-blue-600')
            ui.label('公告中心').classes('text-xl md:text-2xl font-bold text-blue-600')
        
        announcement_list = ui.column().classes('space-y-3 md:space-y-4')

        def load_announcements_embedded():
            result = AnnouncementService.get_announcements()
            if result['success']:
                announcements = result['announcements']
                announcement_list.clear()
                for ann in announcements[:5]:
                    with announcement_list:
                        with ui.row().classes('w-full p-4 md:p-5 items-center hover:bg-gray-50 rounded-lg transition-colors duration-200 flex-col md:flex-row'):
                            ui.icon('newspaper', size='1.2rem md:1.5rem').classes('text-blue-500 mr-0 md:mr-4 mb-2 md:mb-0')
                            with ui.column().classes('flex-1 w-full md:w-auto'):
                                ui.label(ann['title']).classes('text-base md:text-lg font-semibold text-gray-800')
                                ui.label(ann['content']).classes('text-sm md:text-base text-gray-600 line-clamp-2')
                            ui.label(ann['created_at'][5:10] if len(ann['created_at']) >= 10 else ann['created_at']).classes('text-sm text-gray-500 mt-2 md:mt-0')
            else:
                with announcement_list:
                    ui.label('暂无公告').classes('text-gray-500 text-center py-4 md:py-5')

        with ui.row().classes('w-full justify-end mt-4 md:mt-5'):
            ui.button('刷新公告', on_click=load_announcements_embedded, icon='refresh').classes('bg-blue-50 hover:bg-blue-100 text-blue-600 font-medium py-2 md:py-3 px-4 md:px-5 rounded-lg shadow-sm text-base')
        
        load_announcements_embedded()