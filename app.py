"""应用主入口 - 基于NiceGUI会话隔离的重构版本"""

from nicegui import ui, app
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
import sys
import threading
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath("."))

from ccsa_auto.core import create_tables, init_admin
from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import AuthSession
from ccsa_auto.modules.task.scheduler import init_scheduler
from ccsa_auto.modules.auth.session_manager import get_session_manager
from ccsa_auto.modules.auth.user_state import UserStateService

from ccsa_auto.ui.pages.login_page import create_login_page
from ccsa_auto.ui.pages.admin_login_page import create_admin_login_page
from ccsa_auto.ui.pages.admin_page import create_admin_page
from ccsa_auto.ui.pages.main_page import create_main_page

create_tables()
init_admin()
init_scheduler()

# 运行数据库表结构迁移
from ccsa_auto.modules.auth.session_manager import migrate_auth_session_schema

migrate_auth_session_schema()


def startup_cleanup():
    session_manager = get_session_manager()
    count = session_manager.cleanup_expired_sessions()
    if count > 0:
        print(f"启动时已清理 {count} 个过期会话")


threading.Thread(target=startup_cleanup, daemon=True).start()

unrestricted_page_routes = {"/login", "/admin_login"}


def get_session_from_request(request: Request):
    """从请求中获取 session_id 和 access_token

    优先级：
    1. URL 参数 session_id（用于登录后重定向）
    2. Cookie session_id（正常访问）
    """
    # 优先从 URL 参数获取，其次从 Cookie 获取
    session_id = request.query_params.get("session_id") or request.cookies.get(
        "session_id"
    )
    auth_header = request.headers.get("Authorization")
    access_token = auth_header.replace("Bearer ", "") if auth_header else None
    return session_id, access_token


def inject_session_retrieval_js():
    """注入 JavaScript 用于页面加载时从 localStorage 获取 session_id 并通过 API 同步"""
    ui.run_javascript("""
        (function() {
            var sessionId = localStorage.getItem('session_id');
            var sessionHostname = localStorage.getItem('session_hostname');
            var currentHostname = window.location.hostname;
            
            if (sessionId && sessionHostname && sessionHostname !== currentHostname) {
                document.cookie = "session_id=" + sessionId + "; path=/; secure=False; samesite=lax; max-age=" + (86400 * 7);
                localStorage.setItem('session_hostname', currentHostname);
            }
        })();
    """)


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件 - 限制对需要认证的页面的访问

    如果用户未登录且尝试访问需要认证的页面，则重定向到登录页面
    同时验证数据库会话的有效性（过期、无活动超时）
    """

    async def dispatch(self, request: Request, call_next):
        session_id, access_token = get_session_from_request(request)

        print(f"[认证中间件] 请求路径: {request.url.path}")
        print(f"[认证中间件] session_id: {session_id}")
        print(
            f"[认证中间件] access_token: {access_token[:20] + '...' if access_token else None}"
        )

        # 设置 session_id 到 ui.context，供页面使用
        if session_id:
            try:
                ui.context.session_id = session_id
                print(f"[认证中间件] 已设置 ui.context.session_id: {session_id}")
            except (AttributeError, TypeError) as e:
                print(f"[认证中间件] 设置 ui.context.session_id 失败: {e}")
                pass

        is_authenticated = False
        if session_id:
            state = UserStateService.get_state(session_id)
            print(f"[认证中间件] 用户状态: {state}")
            if state and state.get("authenticated"):
                is_authenticated = True
                print(f"[认证中间件] 用户已认证: session_id={session_id}")
            else:
                print(f"[认证中间件] 用户未认证或状态无效")

        if not is_authenticated:
            page_routes = set()
            for route in app.routes:
                if hasattr(route, "path"):
                    page_routes.add(route.path)

            if (
                request.url.path in page_routes
                and request.url.path not in unrestricted_page_routes
            ):
                print(f"[认证中间件] 需要认证的页面，重定向到 /login")
                if session_id:
                    UserStateService.set_referrer_path(session_id, request.url.path)
                return RedirectResponse("/login")
            print(f"[认证中间件] 放行请求: {request.url.path}")
            return await call_next(request)

        if session_id and access_token:
            session_manager = get_session_manager()
            session_data = session_manager.validate_session(session_id, access_token)

            if session_data is None:
                print(f"[认证中间件] 会话验证失败，清除状态")
                UserStateService.clear_state(session_id)
                page_routes = set()
                for route in app.routes:
                    if hasattr(route, "path"):
                        page_routes.add(route.path)

                if (
                    request.url.path in page_routes
                    and request.url.path not in unrestricted_page_routes
                ):
                    if session_id:
                        UserStateService.set_referrer_path(session_id, request.url.path)
                    return RedirectResponse("/login")
            else:
                print(f"[认证中间件] 会话验证成功，刷新会话")
                session_manager.refresh_session(session_id)

        return await call_next(request)


app.add_middleware(AuthMiddleware)


@ui.page("/login")
def login_page():
    """普通用户登录页面"""

    def navigate_to_main():
        ui.navigate.to("/")

    create_login_page(navigate_to_main)


@ui.page("/admin_login")
def admin_login_page():
    """管理员登录页面"""

    def navigate_to_admin(page=None):
        ui.navigate.to("/admin")

    create_admin_login_page(navigate_to_admin)


@ui.page("/")
def main_page():
    """主页面"""
    session_manager = get_session_manager()
    session_id = session_manager.get_current_session_id()

    if not session_id:
        ui.navigate.to("/login")
        return

    state = UserStateService.get_state(session_id)
    if not state or not state.get("authenticated"):
        ui.navigate.to("/login")
        return

    user_info = state.get("user_info", {}) if state else {}

    print(f"主页面: user_info={user_info}")
    print(f"主页面: is_admin={user_info.get('is_admin')}")

    if user_info.get("is_admin"):
        print("检测到管理员，重定向到/admin")
        ui.navigate.to("/admin")
        return

    def navigate_to(page):
        """导航函数"""
        if page == "logout":
            if session_id:
                UserStateService.clear_state(session_id)
                session_manager.delete_session(session_id)
            if user_info.get("is_admin"):
                ui.navigate.to("/admin_login")
            else:
                ui.navigate.to("/login")
        else:
            ui.navigate.to(f"/{page}")

    with ui.column().classes("w-full"):
        with ui.card().classes(
            "w-full bg-gradient-to-r from-blue-600 to-blue-900 text-white p-4 rounded-none shadow-lg mb-6 border-0"
        ):
            with ui.row().classes("w-full justify-between items-center"):
                with ui.row().classes("items-center gap-4"):
                    ui.icon("quiz", size="1.8rem").classes("text-white")
                    with ui.column().classes("gap-1"):
                        ui.label("用户答题托管平台").classes("text-xl font-bold")
                        ui.label("智能答题，高效学习").classes("text-xs opacity-90")

                with ui.row().classes("items-center gap-4"):
                    ui.button(
                        "退出登录",
                        on_click=lambda: navigate_to("logout"),
                        icon="logout",
                    ).classes(
                        "bg-white/20 hover:bg-white/30 text-white font-medium py-1 px-3 rounded text-sm"
                    )

        create_main_page(navigate_to)

    def logout():
        """退出登录"""
        if session_id:
            UserStateService.clear_state(session_id)
            session_manager.delete_session(session_id)
        ui.navigate.to("/login")


@ui.page("/admin")
def admin_page():
    """管理员页面"""
    session_manager = get_session_manager()
    session_id = session_manager.get_current_session_id()

    if not session_id:
        ui.navigate.to("/login")
        return

    state = UserStateService.get_state(session_id)
    if not state or not state.get("authenticated"):
        ui.navigate.to("/login")
        return

    user_info = state.get("user_info", {}) if state else {}
    if not user_info.get("is_admin"):
        ui.notify("需要管理员权限", type="warning")
        ui.navigate.to("/")
        return

    with ui.column().classes("w-full"):
        with ui.row().classes("w-full justify-between items-center p-4 bg-gray-100"):
            ui.label("管理员后台").classes("text-xl font-bold")
            ui.button("退出登录", on_click=lambda: logout()).classes(
                "bg-red-500 hover:bg-red-600 text-white font-medium py-1 px-3 rounded text-sm"
            )

        create_admin_page()

    def logout():
        """退出登录"""
        if session_id:
            UserStateService.clear_state(session_id)
            session_manager.delete_session(session_id)
        ui.navigate.to("/admin_login")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="用户答题托管平台",
        port=8082,
        storage_secret="ccsa_auto_session_secret_2025",
    )
