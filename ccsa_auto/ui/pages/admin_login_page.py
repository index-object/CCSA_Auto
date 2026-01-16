"""管理员登录页面模块"""

from nicegui import ui, app
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.session_manager import get_session_manager
from ccsa_auto.modules.auth.user_state import UserStateService


def create_admin_login_page(navigate_to):
    """创建管理员登录页面

    Args:
        navigate_to: 导航函数，用于页面跳转
    """
    # 应用全局样式
    # 创建渐变背景容器
    with ui.element("div").classes(
        "w-full min-h-screen bg-gradient-to-br from-slate-50 via-red-50 to-pink-50 flex items-center justify-center p-4"
    ):
        with ui.card().classes("w-full max-w-md p-8 rounded-2xl shadow-2xl card-hover"):
            ui.label("管理员后台登录").classes(
                "text-3xl font-bold text-center text-gray-800 mb-2"
            )
            ui.label("请输入管理员账号信息").classes("text-center text-gray-600 mb-6")

            admin_username_input = ui.input(
                "管理员账号", placeholder="请输入管理员账号"
            ).classes(
                "w-full mb-4 px-4 py-3 rounded-lg border border-gray-300 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-200 transition-all"
            )

            admin_password_input = ui.input(
                "管理员密码", placeholder="请输入管理员密码", password=True
            ).classes(
                "w-full mb-6 px-4 py-3 rounded-lg border border-gray-300 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-200 transition-all"
            )

            # 登录处理
            async def handle_admin_login():
                """处理管理员登录"""
                print("handle_admin_login 函数被调用")
                try:
                    admin_username = admin_username_input.value.strip()
                    admin_password = admin_password_input.value.strip()

                    print(
                        f"获取到的用户名: {admin_username}, 密码长度: {len(admin_password)}"
                    )

                    if not admin_username or not admin_password:
                        ui.notify("请输入管理员账号和密码", type="warning")
                        return

                    print(f"尝试管理员登录: 用户名={admin_username}")
                    success, result, message = AuthService.login(
                        admin_username, admin_password
                    )
                    print(f"登录结果: success={success}, message={message}")

                    if success:
                        # 检查是否为管理员
                        if not result["user"].get("is_admin"):
                            ui.notify(
                                "非管理员账号，请使用普通用户登录", type="negative"
                            )
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
                        ui.notify("管理员登录成功", type="positive")

                        # 设置 session_id Cookie 并跳转到管理后台
                        ui.run_javascript(f"""
                            document.cookie = "session_id={session_id}; path=/; secure=False; samesite=lax; max-age={86400 * 7}";
                            window.location.href = "/admin";
                        """)
                        return
                    else:
                        ui.notify(message, type="negative")
                except Exception as e:
                    print(f"管理员登录过程中发生异常: {e}")
                    import traceback

                    traceback.print_exc()
                    ui.notify(f"登录失败: {str(e)}", type="negative")

            ui.button("管理员登录", on_click=handle_admin_login).classes(
                "w-full bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition-all duration-300 transform hover:scale-[1.02]"
            )

            # 普通用户登录链接
            with ui.row().classes("w-full justify-center mt-4"):
                ui.label("返回普通用户登录").classes("text-gray-600 mr-2")
                # 将链接目标设为字符串路径，避免把函数对象写入组件属性导致序列化失败
                ui.link("点击这里", "/login").classes(
                    "text-blue-600 hover:text-blue-800 font-medium transition-colors"
                )
