"""登录页面模块 - 基于数据库存储的会话管理"""

from nicegui import ui
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.session_manager import get_session_manager
from ccsa_auto.modules.auth.user_state import UserStateService


def create_login_page(navigate_to):
    """创建登录页面

    Args:
        navigate_to: 导航函数，用于页面跳转
    """
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

                # 设置 session_id Cookie
                ui.run_javascript(f"""
                    document.cookie = "session_id={session_id}; path=/; secure=False; samesite=lax; max-age={86400 * 7}";
                    window.location.href = "/";
                """)
                return
            else:
                ui.notify(message, type="negative")

        ui.button("登录", on_click=on_login).classes(
            "w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded"
        )
