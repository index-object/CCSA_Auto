from nicegui import ui
from typing import Callable, Optional

from ccsa_auto.admin_v2.components.layout.sidebar import Sidebar


class AdminLayout:
    def __init__(
        self, render_content: Optional[Callable] = None, title: str = "Dashboard"
    ):
        self.sidebar = Sidebar()
        self.render_content = render_content
        self.title = title

    def render(self):
        ui.run_javascript("""
            (function() {
                var urlParams = new URLSearchParams(window.location.search);
                var sessionId = urlParams.get('session_id');
                if (sessionId && !document.cookie.includes('session_id=' + sessionId)) {
                    document.cookie = "session_id=" + sessionId + "; path=/; samesite=lax; max-age=" + (86400 * 7);
                }
                var localSessionId = localStorage.getItem('session_id');
                var sessionHostname = localStorage.getItem('session_hostname');
                var currentHostname = window.location.hostname;
                if (localSessionId && sessionHostname && sessionHostname !== currentHostname) {
                    document.cookie = "session_id=" + localSessionId + "; path=/; samesite=lax; max-age=" + (86400 * 7);
                    localStorage.setItem('session_hostname', currentHostname);
                }
            })();
        """)

        with ui.row().classes("w-full h-screen overflow-hidden"):
            self.sidebar.render()

            with ui.column().classes(
                "flex-1 overflow-auto bg-gradient-to-b from-[#f0fdf4] to-[#ecfdf5]"
            ):
                with ui.column().classes("w-full p-8 gap-6"):
                    if self.render_content:
                        self.render_content()
                    else:
                        ui.label("Content").classes("text-gray-600")
