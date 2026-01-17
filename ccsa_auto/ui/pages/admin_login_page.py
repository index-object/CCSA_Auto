"""管理员登录页面模块"""

import asyncio
from nicegui import ui, app
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.session_manager import get_session_manager
from ccsa_auto.modules.auth.user_state import UserStateService


def create_admin_login_page(navigate_to):
    """创建管理员登录页面

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
                console.log('[管理员登录同步] 从 URL 参数获取到 session_id:', sessionId);
                // 如果 Cookie 中没有该 session_id，则设置 Cookie
                if (!document.cookie.includes('session_id=' + sessionId)) {
                    console.log('[管理员登录同步] Cookie 中没有该 session_id，同步到 Cookie');
                    document.cookie = "session_id=" + sessionId + "; path=/; samesite=lax; max-age=" + (86400 * 7);
                    console.log('[管理员登录同步] Cookie 已设置:', document.cookie);
                } else {
                    console.log('[管理员登录同步] Cookie 已存在该 session_id');
                }
            } else {
                // 如果 URL 参数中没有 session_id，尝试从 localStorage 同步
                var localSessionId = localStorage.getItem('session_id');
                var sessionHostname = localStorage.getItem('session_hostname');
                var currentHostname = window.location.hostname;

                if (localSessionId && sessionHostname && sessionHostname !== currentHostname) {
                    console.log('[管理员登录同步] 从 localStorage 同步 session_id:', localSessionId);
                    document.cookie = "session_id=" + localSessionId + "; path=/; samesite=lax; max-age=" + (86400 * 7);
                    localStorage.setItem('session_hostname', currentHostname);
                    console.log('[管理员登录同步] Cookie 已设置');
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
                .admin-bg {
                    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 50%, #a7f3d0 100%);
                    min-height: 100vh;
                }
                .admin-card {
                    backdrop-filter: blur(10px);
                    background: rgba(255, 255, 255, 0.95);
                    animation: fadeInUp 0.6s ease-out;
                }
                .admin-input {
                    transition: all 0.3s ease;
                }
                .admin-input:focus-within {
                    transform: scale(1.02);
                }
                .admin-btn {
                    transition: all 0.3s ease;
                }
                .admin-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(16, 185, 129, 0.3);
                }
                .admin-btn:active {
                    transform: translateY(0);
                }
                .admin-decor {
                    position: absolute;
                    border-radius: 50%;
                    background: rgba(16, 185, 129, 0.15);
                    animation: float 6s ease-in-out infinite;
                }
                .admin-decor-1 { width: 250px; height: 250px; top: -80px; right: -80px; animation-delay: 0s; }
                .admin-decor-2 { width: 180px; height: 180px; bottom: -40px; left: -40px; animation-delay: 2s; }
                .admin-decor-3 { width: 120px; height: 120px; top: 40%; left: -60px; animation-delay: 4s; }
            `;
            document.head.appendChild(style);
        })();
    """)

    # 应用全局样式
    # 创建渐变背景容器
    with ui.element("div").classes(
        "w-full min-h-screen admin-bg flex items-center justify-center p-4 relative overflow-hidden"
    ):
        # 装饰性圆形
        with ui.element("div").classes("admin-decor admin-decor-1"):
            pass
        with ui.element("div").classes("admin-decor admin-decor-2"):
            pass
        with ui.element("div").classes("admin-decor admin-decor-3"):
            pass

        with ui.card().classes("admin-card w-full max-w-sm p-8 rounded-2xl shadow-lg"):
            # 标题区域
            with ui.column().classes("w-full items-center mb-2"):
                ui.label("管理员后台登录").classes(
                    "text-2xl font-bold text-center text-gray-800 mb-2"
                )
                ui.label("请输入管理员账号信息").classes(
                    "text-sm text-center text-gray-500"
                )

            # 输入框区域
            with ui.column().classes("w-full mb-5 mt-4"):
                with ui.row().classes(
                    "w-full items-center mb-4 admin-input bg-gray-50 rounded-xl px-4 py-3 border-2 border-transparent focus-within:border-emerald-400 transition-all"
                ):
                    ui.icon("admin_panel_settings").classes(
                        "text-emerald-500 text-xl mr-3"
                    )
                    admin_username_input = ui.input("管理员账号").classes(
                        "flex-1 bg-transparent border-none outline-none text-gray-700 placeholder-gray-400"
                    )

                with ui.row().classes(
                    "w-full items-center mb-2 admin-input bg-gray-50 rounded-xl px-4 py-3 border-2 border-transparent focus-within:border-emerald-400 transition-all"
                ):
                    ui.icon("lock").classes("text-emerald-500 text-xl mr-3")
                    admin_password_input = ui.input(
                        "管理员密码", password=True
                    ).classes(
                        "flex-1 bg-transparent border-none outline-none text-gray-700 placeholder-gray-400"
                    )

            # 登录按钮
            login_btn = ui.button("管理员登录").classes(
                "admin-btn w-full bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-semibold py-3 px-6 rounded-xl shadow-md"
            )

            # 普通用户登录链接
            with ui.row().classes("w-full justify-center mt-6"):
                ui.label("返回普通用户登录").classes("text-gray-500 mr-2")
                ui.link("点击这里", "/login").classes(
                    "text-emerald-500 hover:text-emerald-700 font-medium transition-colors"
                )

        # 登录处理
        async def handle_admin_login():
            """处理管理员登录"""
            # 显示加载状态
            login_btn.props("loading")
            await asyncio.sleep(0.1)

            try:
                admin_username = admin_username_input.value.strip()
                admin_password = admin_password_input.value.strip()

                if not admin_username or not admin_password:
                    login_btn.props("loading=False")
                    ui.notify("请输入管理员账号和密码", type="warning")
                    return

                success, result, message = AuthService.login(
                    admin_username, admin_password
                )

                if success:
                    # 检查是否为管理员
                    if not result["user"].get("is_admin"):
                        login_btn.props("loading=False")
                        ui.notify("非管理员账号，请使用普通用户登录", type="negative")
                        return

                    # 创建数据库会话并获取 session_id
                    session_manager = get_session_manager()
                    session_id = session_manager.create_db_session(
                        user_id=result["user"]["id"],
                        access_token=result["access_token"],
                        user_info=result["user"],
                        is_admin=True,
                        external_token=result.get("external_token"),
                    )

                    if not session_id:
                        login_btn.props("loading=False")
                        ui.notify("创建会话失败", type="negative")
                        return

                    # 保存管理员状态到数据库
                    UserStateService.save_state(
                        session_id,
                        {
                            "authenticated": True,
                            "is_admin": True,
                            "user_info": result["user"],
                            "access_token": result["access_token"],
                            "user_id": result["user"]["id"],
                            "external_token": result.get("external_token"),
                        },
                    )

                    print(
                        f"管理员 {result['user']['username']} 登录成功，会话ID: {session_id}"
                    )
                    print(f"[管理员登录] 重定向到 /admin?session_id={session_id}")
                    ui.notify("管理员登录成功", type="positive")

                    # 使用 NiceGUI 导航跳转，URL 中携带 session_id 参数
                    # 认证中间件会从 URL 参数获取 session_id
                    ui.navigate.to(f"/admin?session_id={session_id}")
                else:
                    login_btn.props("loading=False")
                    ui.notify(message, type="negative")
            except Exception as e:
                login_btn.props("loading=False")
                print(f"管理员登录过程中发生异常: {e}")
                import traceback

                traceback.print_exc()
                ui.notify(f"登录失败: {str(e)}", type="negative")

        login_btn.on_click(handle_admin_login)
