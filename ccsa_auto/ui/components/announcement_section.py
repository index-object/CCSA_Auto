"""公告信息区组件模块"""
from nicegui import ui
from ccsa_auto.modules.announcement.service import AnnouncementService
from ccsa_auto.ui.utils.loading_utils import create_loading_button


def create_announcement_section():
    """在主页面中嵌入的公告信息区"""
    with ui.card().classes('w-full h-auto p-3 md:p-4 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300'):
        with ui.row().classes('items-center gap-2 mb-3 md:mb-4 pb-2 border-b-2 border-gray-100'):
            ui.icon('campaign', size='1.3rem md:1.5rem').classes('text-blue-600')
            ui.label('公告中心').classes('text-base md:text-lg font-bold text-blue-600')
        
        # 使用滚动区域包裹list控件，确保有滚动效果
        with ui.scroll_area().classes('w-full max-h-64 md:max-h-72 overflow-y-auto'):
            announcement_list = ui.list().props('bordered separator').classes('w-full')

            def load_announcements_embedded():
                result = AnnouncementService.get_announcements()
                if result['success']:
                    announcements = result['announcements']
                    announcement_list.clear()
                    # 显示所有公告，滚动区域限制高度，最多显示3个公告
                    for ann in announcements:
                        # 必须在announcement_list上下文中添加item
                        with announcement_list:
                            with ui.item().classes('hover:bg-gray-50 transition-colors duration-200 min-h-0'):
                                with ui.item_section().props('avatar'):
                                    ui.icon('newspaper').classes('text-blue-500')
                                with ui.item_section():
                                    # 标题：完整显示，不截断
                                    ui.item_label(ann['title']).classes('text-sm md:text-base font-semibold text-gray-800 break-words')
                                    # 内容：完整显示，不使用line-clamp限制
                                    ui.item_label(ann['content']).props('caption').classes('text-xs md:text-sm text-gray-600 break-words')
                                with ui.item_section().props('side'):
                                    ui.label(ann['created_at'][5:10] if len(ann['created_at']) >= 10 else ann['created_at']).classes('text-xs text-gray-500 whitespace-nowrap')
                else:
                    with announcement_list:
                        ui.item_label('暂无公告').classes('text-gray-500 text-center py-3 md:py-4')

        with ui.row().classes('w-full justify-end mt-2 md:mt-3'):
            create_loading_button(
                '刷新公告',
                on_click=load_announcements_embedded,
                icon='refresh'
            ).classes('bg-blue-50 hover:bg-blue-100 text-blue-600 font-medium py-1 md:py-1.5 px-2.5 md:px-3 rounded-lg shadow-sm text-xs')
        
        load_announcements_embedded()