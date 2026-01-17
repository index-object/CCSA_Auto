"""登录页面模块 - 基于数据库存储的会话管理"""

from fastapi.responses import RedirectResponse
from nicegui import ui
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.session_manager import get_session_manager
from ccsa_auto.modules.auth.user_state import UserStateService


def create_login_page(navigate_to):
    """创建登录页面

    Args:
        navigate_to: 导航函数，用于页面跳转
    """

    # 页面加载时同步 session_id（从 URL 参数同步到 Cookie）
    # 用于解决从不同 IP 登录时的 session_id 传递问题
    ui.run_javascript("""
        (function() {
            // 从 URL 参数获取 session_id
            var urlParams = new URLSearchParams(window.location.search);
            var sessionId = urlParams.get('session_id');

            if (sessionId) {
                console.log('[登录同步] 从 URL 参数获取到 session_id:', sessionId);
                // 如果 Cookie 中没有该 session_id，则设置 Cookie
                if (!document.cookie.includes('session_id=' + sessionId)) {
                    console.log('[登录同步] Cookie 中没有该 session_id，同步到 Cookie');
                    document.cookie = "session_id=" + sessionId + "; path=/; samesite=lax; max-age=" + (86400 * 7);
                    console.log('[登录同步] Cookie 已设置:', document.cookie);
                } else {
                    console.log('[登录同步] Cookie 已存在该 session_id');
                }
            } else {
                // 如果 URL 参数中没有 session_id，尝试从 localStorage 同步
                var localSessionId = localStorage.getItem('session_id');
                var sessionHostname = localStorage.getItem('session_hostname');
                var currentHostname = window.location.hostname;

                if (localSessionId && sessionHostname && sessionHostname !== currentHostname) {
                    console.log('[登录同步] 从 localStorage 同步 session_id:', localSessionId);
                    document.cookie = "session_id=" + localSessionId + "; path=/; samesite=lax; max-age=" + (86400 * 7);
                    localStorage.setItem('session_hostname', currentHostname);
                    console.log('[登录同步] Cookie 已设置');
                }
            }
        })();
    """)

    with ui.card().classes(
        "w-96 h-auto mx-auto my-auto p-6 shadow-lg rounded-lg page-card login-page"
    ):
        ui.label("用户答题托管平台").classes("text-2xl font-bold text-center mb-6")

        username = ui.input("外部平台账号").classes("w-full mb-4")
        password = ui.input("外部平台密码", password=True).classes("w-full mb-6")

        async def on_login(e):
            """登录处理"""
            data = {"username": username.value, "password": password.value}

            # 调用认证服务
            success, result, message = AuthService.login(
                data["username"], data["password"]
            )
            if success:
                # 创建数据库会话并获取 session_id
                session_manager = get_session_manager()
                session_id = session_manager.create_db_session(
                    user_id=result["user"]["id"],
                    access_token=result["access_token"],
                    user_info=result["user"],
                    is_admin=False,
                    external_token=result.get("external_token"),
                )

                if not session_id:
                    ui.notify("创建会话失败", type="negative")
                    return

                # 保存用户状态到数据库
                UserStateService.save_state(
                    session_id,
                    {
                        "authenticated": True,
                        "is_admin": False,
                        "user_info": result["user"],
                        "access_token": result["access_token"],
                        "external_token": result.get("external_token"),
                        "user_id": result["user"]["id"],
                    },
                )

                print(
                    f"用户 {result['user']['username']} 登录成功，会话ID: {session_id}"
                )
                print(f"[登录] 重定向到 /?session_id={session_id}")

                # 使用 NiceGUI 导航跳转，URL 中携带 session_id 参数
                # 认证中间件会从 URL 参数获取 session_id
                ui.navigate.to(f"/?session_id={session_id}")
            else:
                ui.notify(message, type="negative")

        ui.button("登录", on_click=on_login).classes(
            "w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded"
        )
