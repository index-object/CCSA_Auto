"""登录页面模块 - 基于数据库存储的会话管理"""

import asyncio
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

    # 页面加载动画样式
    ui.run_javascript("""
        (function() {
            var style = document.createElement('style');
            style.textContent = `
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                @keyframes float {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-10px); }
                }
                .login-bg {
                    background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
                    min-height: 100vh;
                }
                .login-card {
                    backdrop-filter: blur(10px);
                    background: rgba(255, 255, 255, 0.95);
                    animation: fadeInUp 0.6s ease-out;
                }
                .login-input {
                    transition: all 0.3s ease;
                }
                .login-input:focus-within {
                    transform: scale(1.02);
                }
                .login-btn {
                    transition: all 0.3s ease;
                }
                .login-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(16, 185, 129, 0.3);
                }
                .login-btn:active {
                    transform: translateY(0);
                }
                .decor-circle {
                    position: absolute;
                    border-radius: 50%;
                    background: rgba(255, 255, 255, 0.15);
                    animation: float 6s ease-in-out infinite;
                }
                .decoration-1 { width: 300px; height: 300px; top: -100px; left: -100px; animation-delay: 0s; }
                .decoration-2 { width: 200px; height: 200px; bottom: -50px; right: -50px; animation-delay: 2s; }
                .decoration-3 { width: 150px; height: 150px; top: 50%; right: -75px; animation-delay: 4s; }
            `;
            document.head.appendChild(style);
        })();
    """)

    # 渐变背景容器
    with ui.element("div").classes(
        "w-full min-h-screen login-bg flex items-center justify-center p-4 relative overflow-hidden"
    ):
        # 装饰性圆形
        with ui.element("div").classes("decor-circle decoration-1"):
            pass
        with ui.element("div").classes("decor-circle decoration-2"):
            pass
        with ui.element("div").classes("decor-circle decoration-3"):
            pass

        # 登录卡片
        with ui.card().classes("login-card w-full max-w-sm p-8 rounded-2xl shadow-lg"):
            # 标题区域
            with ui.column().classes("w-full items-center mb-8"):
                ui.label("用户答题托管平台").classes(
                    "text-2xl font-bold text-center text-gray-800 mb-2"
                )
                ui.label("便捷答题，自动托管").classes(
                    "text-sm text-center text-gray-500"
                )

            # 输入框区域
            with ui.column().classes("w-full mb-6"):
                with ui.row().classes(
                    "w-full items-center mb-4 login-input bg-gray-50 rounded-xl px-4 py-3 border-2 border-transparent focus-within:border-emerald-400 transition-all"
                ):
                    ui.icon("person").classes("text-gray-400 text-xl mr-3")
                    username = ui.input("外部平台账号").classes(
                        "flex-1 bg-transparent border-none outline-none text-gray-700 placeholder-gray-400"
                    )

                with ui.row().classes(
                    "w-full items-center mb-2 login-input bg-gray-50 rounded-xl px-4 py-3 border-2 border-transparent focus-within:border-emerald-400 transition-all"
                ):
                    ui.icon("lock").classes("text-gray-400 text-xl mr-3")
                    password = ui.input("外部平台密码", password=True).classes(
                        "flex-1 bg-transparent border-none outline-none text-gray-700 placeholder-gray-400"
                    )

            # 登录按钮
            login_btn = ui.button("登 录").classes(
                "login-btn w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-semibold py-3 px-6 rounded-xl shadow-md"
            )

            # 底部链接
            with ui.row().classes("w-full justify-center mt-6"):
                ui.label("返回管理员登录").classes("text-white/70 mr-2")
                ui.link("点击这里", "/admin_login").classes(
                    "text-white hover:text-white/80 font-medium transition-colors"
                )

        # 登录处理
        async def on_login(e):
            """登录处理"""
            # 显示加载状态
            login_btn.props("loading")
            await asyncio.sleep(0.1)

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
                    login_btn.props("loading=False")
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
                login_btn.props("loading=False")
                ui.notify(message, type="negative")

        login_btn.on_click(on_login)
