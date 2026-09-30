"""应用主入口 - 基于NiceGUI会话隔离的重构版本"""

from nicegui import ui, app
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
import sys
import threading
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath("."))

from ccsa_auto.core import create_tables, init_admin
from ccsa_auto.core.config import Config
from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import AuthSession
from ccsa_auto.core.logger import (
    get_logger,
    bind_context,
    log_access,
    new_trace_id,
    reset_context,
    setup_logging,
    shutdown_logging,
    ensure_process_logging,
)
from ccsa_auto.modules.logging.service import LoggingService, current_client_ip
from ccsa_auto.modules.task.scheduler import init_scheduler, stop_scheduler
from ccsa_auto.modules.auth.session_manager import get_session_manager
from ccsa_auto.modules.auth.user_state import UserStateService

from ccsa_auto.ui.pages.login_page import create_login_page
from ccsa_auto.ui.pages.admin_login_page import create_admin_login_page
from ccsa_auto.ui.pages.admin_page import create_admin_page
from ccsa_auto.ui.pages.main_page import create_main_page

# Admin V2 imports
from ccsa_auto.admin_v2.pages.dashboard import create_dashboard_page
from ccsa_auto.admin_v2.pages.users import create_users_page
from ccsa_auto.admin_v2.pages.tasks import create_tasks_page
from ccsa_auto.admin_v2.pages.announcements import create_announcements_page
from ccsa_auto.admin_v2.pages.logs import create_logs_page
from ccsa_auto.admin_v2.pages.settings import create_settings_page
from ccsa_auto.admin_v2.components.layout.admin_layout import AdminLayout

logger = get_logger(__name__)

create_tables()
init_admin()

# 运行数据库表结构迁移
from ccsa_auto.modules.auth.session_manager import migrate_auth_session_schema

migrate_auth_session_schema()


@app.on_startup
def on_startup():
    """应用启动时的初始化"""
    setup_logging()
    logger.info(
        "应用启动 | pid={} reload={} log_dir={} level={}",
        os.getpid(),
        Config.APP_RELOAD,
        Config.LOG_DIR,
        Config.LOG_LEVEL,
    )
    LoggingService.log_system(
        "APP_START",
        f"应用启动 (pid={os.getpid()})",
        detail={"reload": Config.APP_RELOAD, "log_dir": Config.LOG_DIR},
    )

    init_scheduler()

    def startup_cleanup():
        try:
            session_manager = get_session_manager()
            count = session_manager.cleanup_expired_sessions()
            if count > 0:
                logger.info("启动时已清理 {} 个过期会话", count)
        except Exception as e:
            logger.exception("启动清理过期会话失败: {}", e)

    threading.Thread(target=startup_cleanup, daemon=True).start()


@app.on_shutdown
def on_shutdown():
    """应用关闭时的收尾"""
    logger.info("应用关闭 | pid={}", os.getpid())
    LoggingService.log_system("APP_STOP", f"应用关闭 (pid={os.getpid()})")
    try:
        stop_scheduler()
    except Exception as e:
        logger.exception("停止调度器失败: {}", e)
    shutdown_logging()

unrestricted_page_routes = {"/login", "/admin_login"}
admin_page_routes = {
    "/admin",
    "/admin_v2",
    "/admin_v2/users",
    "/admin_v2/tasks",
    "/admin_v2/announcements",
    "/admin_v2/logs",
    "/admin_v2/settings",
}


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


# 静态资源/内部通道不记录访问日志，避免刷屏与无谓的数据库写入
_ACCESS_SKIP_PREFIXES = ("/_nicegui", "/socket.io", "/_static", "/favicon", "/__nicegui")
_ACCESS_SKIP_SUFFIXES = (
    ".js",
    ".css",
    ".map",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
)

_page_routes_cache = None


def get_page_routes() -> set:
    """已注册页面路由集合（首次调用后缓存）。"""
    global _page_routes_cache
    if _page_routes_cache is None:
        _page_routes_cache = {
            route.path for route in app.routes if hasattr(route, "path")
        }
    return _page_routes_cache


def _should_log_access(path: str) -> bool:
    if not Config.LOG_ACCESS_ENABLED:
        return False
    if path.startswith(_ACCESS_SKIP_PREFIXES):
        return False
    return not path.lower().endswith(_ACCESS_SKIP_SUFFIXES)


def get_client_ip(request: Request) -> str:
    """获取客户端真实 IP（兼容反向代理）。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def _record_access(
    request: Request,
    request_id: str,
    path: str,
    status_code: int,
    user_id,
    client_ip: str,
    started: float,
) -> None:
    """写文件访问日志（access 渠道）；页面访问额外写一条数据库台账。"""
    try:
        duration_ms = (time.perf_counter() - started) * 1000
        user_agent = request.headers.get("user-agent")
        referer = request.headers.get("referer")
        is_page = path in get_page_routes()
        event = "page_view" if is_page else "api_access"
        session_id = getattr(request.state, "session_id", None)

        log_access(
            event=event,
            user_id=user_id,
            session_id=session_id,
            method=request.method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
            user_agent=user_agent,
            referer=referer,
            request_id=request_id,
        )

        if (
            Config.LOG_ACCESS_DB_ENABLED
            and is_page
            and request.method == "GET"
            and status_code < 400
        ):
            LoggingService.log_access(
                event=event,
                user_id=user_id,
                path=path,
                method=request.method,
                status_code=status_code,
                ip_address=client_ip,
                session_id=session_id,
                duration_ms=duration_ms,
            )
    except Exception as e:  # 访问日志失败绝不冒泡
        logger.error("记录访问日志失败 | path={} | error={}", path, e)


def _record_logout(session_id, user_info) -> None:
    """记录一次退出登录（文件 access 渠道 + 数据库认证台账）。"""
    try:
        user_id = (user_info or {}).get("id")
        client_ip = current_client_ip()
        log_access(
            event="logout",
            user_id=user_id,
            session_id=session_id,
            client_ip=client_ip,
        )
        LoggingService.log_auth(
            user_id=user_id,
            action="LOGOUT",
            success=True,
            ip_address=client_ip,
            detail=f"用户退出登录 (user_id={user_id})",
        )
    except Exception as e:  # 日志失败不影响退出
        logger.error("记录退出登录失败: {}", e)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """客户访问日志中间件（最外层）。

    为每个请求生成 request_id 并注入日志上下文，记录方法/路径/状态码/耗时/
    客户端IP/User-Agent，认证完成后补记用户ID。
    """

    async def dispatch(self, request: Request, call_next):
        ensure_process_logging()
        path = request.url.path
        if not _should_log_access(path):
            return await call_next(request)

        request_id = new_trace_id()
        client_ip = get_client_ip(request)
        started = time.perf_counter()
        token = bind_context(
            request_id=request_id,
            client_ip=client_ip,
            path=path,
            method=request.method,
        )

        status_code = 500
        response = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            try:
                response.headers["X-Request-ID"] = request_id
            except (AttributeError, TypeError):
                pass
            return response
        except Exception as e:
            logger.exception(
                "请求处理异常 | {} {} | client={} | error={}",
                request.method,
                path,
                client_ip,
                e,
            )
            _record_access(
                request, request_id, path, 500, None, client_ip, started
            )
            raise
        finally:
            reset_context(token)
            if response is not None:
                _record_access(
                    request,
                    request_id,
                    path,
                    status_code,
                    getattr(request.state, "user_id", None),
                    client_ip,
                    started,
                )


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件 - 限制对需要认证的页面的访问

    如果用户未登录且尝试访问需要认证的页面，则重定向到登录页面
    同时验证数据库会话的有效性（过期、无活动超时）
    """

    async def dispatch(self, request: Request, call_next):
        session_id, access_token = get_session_from_request(request)

        logger.debug(
            "认证中间件 | path={} | session_id={} | has_token={}",
            request.url.path,
            session_id,
            bool(access_token),
        )

        # 设置 session_id 到 ui.context，供页面使用
        if session_id:
            try:
                ui.context.session_id = session_id
            except (AttributeError, TypeError) as e:
                logger.debug("设置 ui.context.session_id 失败: {}", e)

        is_authenticated = False
        state = None
        if session_id:
            state = UserStateService.get_state(session_id)
            if state and state.get("authenticated"):
                is_authenticated = True
                request.state.session_id = session_id
                request.state.user_id = state.get("user_id")
                request.state.is_admin = state.get("is_admin")
                logger.debug(
                    "用户已认证 | session_id={} | user_id={} | is_admin={}",
                    session_id,
                    state.get("user_id"),
                    state.get("is_admin"),
                )
            else:
                logger.debug("用户未认证或状态无效 | session_id={}", session_id)

        if not is_authenticated:
            page_routes = get_page_routes()
            path = request.url.path

            if path in page_routes and path not in unrestricted_page_routes:
                # 管理员页面重定向到 admin_login，普通页面重定向到 login
                if path in admin_page_routes:
                    logger.debug("需要管理员认证的页面，重定向到 /admin_login")
                    if session_id:
                        UserStateService.set_referrer_path(session_id, path)
                    return RedirectResponse("/admin_login")
                logger.debug("需要认证的页面，重定向到 /login")
                if session_id:
                    UserStateService.set_referrer_path(session_id, path)
                return RedirectResponse("/login")
            logger.debug("放行请求: {}", path)
            return await call_next(request)

        if session_id and access_token:
            session_manager = get_session_manager()
            session_data = session_manager.validate_session(session_id, access_token)

            if session_data is None:
                logger.debug("会话验证失败，清除状态 | session_id={}", session_id)
                UserStateService.clear_state(session_id)

                path = request.url.path
                if (
                    path in get_page_routes()
                    and path not in unrestricted_page_routes
                ):
                    if session_id:
                        UserStateService.set_referrer_path(session_id, path)
                    return RedirectResponse("/login")
            else:
                logger.debug("会话验证成功，刷新会话 | session_id={}", session_id)
                session_manager.refresh_session(session_id)

        return await call_next(request)


app.add_middleware(AuthMiddleware)
# 最后添加 => 位于中间件栈最外层，能拿到认证中间件写入的 request.state.user_id
# 以及最终响应状态码，从而记录完整的客户访问日志。
app.add_middleware(AccessLogMiddleware)


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
        ui.navigate.to("/admin_v2")

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

    logger.debug("主页面 | user_id={} | is_admin={}", user_info.get("id"), user_info.get("is_admin"))

    if user_info.get("is_admin"):
        logger.debug("检测到管理员，重定向到 /admin_v2")
        ui.navigate.to("/admin_v2")
        return

    def navigate_to(page):
        """导航函数"""
        if page == "logout":
            if session_id:
                UserStateService.clear_state(session_id)
                session_manager.delete_session(session_id)
            _record_logout(session_id, user_info)
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
        _record_logout(session_id, user_info)
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
        _record_logout(session_id, user_info)
        ui.navigate.to("/admin_login")


# Admin V2 Routes
@ui.page("/admin_v2")
def admin_v2_page():
    """Admin V2 Dashboard"""
    session_manager = get_session_manager()
    session_id = session_manager.get_current_session_id()

    if not session_id:
        ui.navigate.to("/admin_login")
        return

    state = UserStateService.get_state(session_id)
    if not state or not state.get("authenticated"):
        ui.navigate.to("/admin_login")
        return

    user_info = state.get("user_info", {}) if state else {}
    if not user_info.get("is_admin"):
        ui.notify("需要管理员权限", type="warning")
        ui.navigate.to("/")
        return

    AdminLayout(render_content=create_dashboard_page, title="数据概览").render()


@ui.page("/admin_v2/users")
def admin_v2_users_page():
    """Admin V2 Users Management"""
    session_manager = get_session_manager()
    session_id = session_manager.get_current_session_id()

    if not session_id:
        ui.navigate.to("/admin_login")
        return

    state = UserStateService.get_state(session_id)
    if not state or not state.get("authenticated"):
        ui.navigate.to("/admin_login")
        return

    user_info = state.get("user_info", {}) if state else {}
    if not user_info.get("is_admin"):
        ui.notify("需要管理员权限", type="warning")
        ui.navigate.to("/")
        return

    AdminLayout(render_content=create_users_page, title="用户管理").render()


@ui.page("/admin_v2/tasks")
def admin_v2_tasks_page():
    """Admin V2 Tasks Management"""
    session_manager = get_session_manager()
    session_id = session_manager.get_current_session_id()

    if not session_id:
        ui.navigate.to("/admin_login")
        return

    state = UserStateService.get_state(session_id)
    if not state or not state.get("authenticated"):
        ui.navigate.to("/admin_login")
        return

    user_info = state.get("user_info", {}) if state else {}
    if not user_info.get("is_admin"):
        ui.notify("需要管理员权限", type="warning")
        ui.navigate.to("/")
        return

    AdminLayout(render_content=create_tasks_page, title="任务管理").render()


@ui.page("/admin_v2/announcements")
def admin_v2_announcements_page():
    """Admin V2 Announcements Management"""
    session_manager = get_session_manager()
    session_id = session_manager.get_current_session_id()

    if not session_id:
        ui.navigate.to("/admin_login")
        return

    state = UserStateService.get_state(session_id)
    if not state or not state.get("authenticated"):
        ui.navigate.to("/admin_login")
        return

    user_info = state.get("user_info", {}) if state else {}
    if not user_info.get("is_admin"):
        ui.notify("需要管理员权限", type="warning")
        ui.navigate.to("/")
        return

    AdminLayout(render_content=create_announcements_page, title="公告管理").render()


@ui.page("/admin_v2/logs")
def admin_v2_logs_page():
    """Admin V2 Operation Logs"""
    session_manager = get_session_manager()
    session_id = session_manager.get_current_session_id()

    if not session_id:
        ui.navigate.to("/admin_login")
        return

    state = UserStateService.get_state(session_id)
    if not state or not state.get("authenticated"):
        ui.navigate.to("/admin_login")
        return

    user_info = state.get("user_info", {}) if state else {}
    if not user_info.get("is_admin"):
        ui.notify("需要管理员权限", type="warning")
        ui.navigate.to("/")
        return

    AdminLayout(render_content=create_logs_page, title="操作日志").render()


@ui.page("/admin_v2/settings")
def admin_v2_settings_page():
    """Admin V2 Settings"""
    session_manager = get_session_manager()
    session_id = session_manager.get_current_session_id()

    if not session_id:
        ui.navigate.to("/admin_login")
        return

    state = UserStateService.get_state(session_id)
    if not state or not state.get("authenticated"):
        ui.navigate.to("/admin_login")
        return

    user_info = state.get("user_info", {}) if state else {}
    if not user_info.get("is_admin"):
        ui.notify("需要管理员权限", type="warning")
        ui.navigate.to("/")
        return

    AdminLayout(render_content=create_settings_page, title="系统设置").render()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="用户答题托管平台",
        port=8082,
        storage_secret="ccsa-auto-secret-key-2024",
        # 热重载会派生子进程，父子进程重复初始化调度器/日志文件。
        # 生产环境保持关闭；需要开发热重载时设置环境变量 CCSA_RELOAD=1。
        reload=Config.APP_RELOAD,
    )
