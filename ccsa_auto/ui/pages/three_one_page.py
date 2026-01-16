"""三个一任务完成情况页面模块 - 基于app.storage.user的会话隔离版本"""

from nicegui import ui, app
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.session_manager import get_session_manager
from ccsa_auto.modules.auth.user_state import UserStateService
import asyncio


def create_three_one_page():
    """创建三个一任务完成情况页面"""
    with ui.card().classes(
        "w-full h-auto p-5 md:p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300"
    ):
        with ui.row().classes(
            "items-center gap-3 mb-5 md:mb-6 pb-4 border-b-2 border-gray-100"
        ):
            ui.icon("task_alt", size="1.5rem md:1.8rem").classes("text-blue-600")
            ui.label("三个一任务完成情况").classes(
                "text-xl md:text-2xl font-bold text-blue-600"
            )

        with ui.grid(columns=3).classes("w-full gap-4 mb-6"):
            with ui.card().classes(
                "p-4 md:p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl text-center hover:shadow-md transition-shadow duration-300"
            ):
                ui.icon("today", size="2.2rem md:3rem").classes(
                    "text-blue-600 mb-3 md:mb-4"
                )
                ui.label("每日一题").classes(
                    "text-lg md:text-xl font-bold text-gray-800 mb-2 md:mb-3"
                )

                daily_status_label = ui.label("加载中...").classes(
                    "text-sm md:text-base mb-2 md:mb-3"
                )
                daily_obtained_label = ui.label("0 积分").classes(
                    "text-2xl md:text-3xl font-bold text-blue-700"
                )

                daily_name_label = ui.label("每日一题").classes("hidden")

            with ui.card().classes(
                "p-4 md:p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl text-center hover:shadow-md transition-shadow duration-300"
            ):
                ui.icon("date_range", size="2.2rem md:3rem").classes(
                    "text-purple-600 mb-3 md:mb-4"
                )
                ui.label("每周一课").classes(
                    "text-lg md:text-xl font-bold text-gray-800 mb-2 md:mb-3"
                )

                weekly_status_label = ui.label("加载中...").classes(
                    "text-sm md:text-base mb-2 md:mb-3"
                )
                weekly_obtained_label = ui.label("0 积分").classes(
                    "text-2xl md:text-3xl font-bold text-purple-700"
                )

                weekly_name_label = ui.label("每周一课").classes("hidden")

            with ui.card().classes(
                "p-4 md:p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-xl text-center hover:shadow-md transition-shadow duration-300"
            ):
                ui.icon("calendar_month", size="2.2rem md:3rem").classes(
                    "text-green-600 mb-3 md:mb-4"
                )
                ui.label("每月一考").classes(
                    "text-lg md:text-xl font-bold text-gray-800 mb-2 md:mb-3"
                )

                monthly_status_label = ui.label("加载中...").classes(
                    "text-sm md:text-base mb-2 md:mb-3"
                )
                monthly_obtained_label = ui.label("0 积分").classes(
                    "text-2xl md:text-3xl font-bold text-green-700"
                )

                monthly_name_label = ui.label("每月一考").classes("hidden")

        def refresh_task_status():
            """刷新任务完成情况"""
            session_manager = get_session_manager()
            session_id = session_manager.get_current_session_id()

            user_id = None
            if session_id:
                state = UserStateService.get_state(session_id)
                if state:
                    user_info = state.get("user_info", {})
                    user_id = user_info.get("id")

            if not user_id:
                ui.notify("未获取到用户信息，请重新登录", type="negative")
                return

            task_status = AuthService.get_task_status_with_retry(user_id)
            if task_status:
                daily = task_status.get("daily", {})
                daily_name_label.text = daily.get("name", "每日一题")
                daily_status = daily.get("status", "未知")
                daily_status_label.text = daily_status
                if daily_status == "已完成":
                    daily_status_label.classes("text-green-600 font-semibold")
                else:
                    daily_status_label.classes("text-orange-600 font-semibold")
                daily_obtained_label.text = f"{daily.get('obtained_score', 0)} 积分"

                weekly = task_status.get("weekly", {})
                weekly_name_label.text = weekly.get("name", "每周一课")
                weekly_status = weekly.get("status", "未知")
                weekly_status_label.text = weekly_status
                if weekly_status == "已完成":
                    weekly_status_label.classes("text-green-600 font-semibold")
                else:
                    weekly_status_label.classes("text-orange-600 font-semibold")
                weekly_obtained_label.text = f"{weekly.get('obtained_score', 0)} 积分"

                monthly = task_status.get("monthly", {})
                monthly_name_label.text = monthly.get("name", "每月一考")
                monthly_status = monthly.get("status", "未知")
                monthly_status_label.text = monthly_status
                if monthly_status == "已完成":
                    monthly_status_label.classes("text-green-600 font-semibold")
                else:
                    monthly_status_label.classes("text-orange-600 font-semibold")
                monthly_obtained_label.text = f"{monthly.get('obtained_score', 0)} 积分"

                from ccsa_auto.core.database import SessionLocal
                from ccsa_auto.core.models import User

                db = SessionLocal()
                try:
                    user = db.query(User).filter_by(id=user_id).first()
                    if user and user.external_token:
                        if session_id:
                            UserStateService.update_external_token(
                                session_id, user.external_token
                            )
                finally:
                    db.close()
            else:
                ui.notify("获取任务完成情况失败: 认证失败或网络错误", type="negative")

        with ui.row().classes("w-full justify-end"):
            # 创建按钮
            refresh_btn = ui.button("刷新任务状态", icon="refresh").classes(
                "bg-blue-50 hover:bg-blue-100 text-blue-600 font-medium py-1 md:py-2 px-3 md:px-4 rounded-lg shadow-sm text-sm md:text-base"
            )

            # 按照test_simple_loading.py的模式设置点击事件
            async def on_refresh_click():
                # 设置加载状态
                refresh_btn.props("loading")
                refresh_btn.disable()

                try:
                    # 添加1秒延迟确保用户能看到加载动画
                    await asyncio.sleep(1)

                    # 执行刷新函数
                    refresh_task_status()
                except Exception as e:
                    ui.notify(f"刷新失败: {str(e)}", type="negative")
                    raise
                finally:
                    # 恢复按钮状态
                    refresh_btn.enable()
                    refresh_btn.props(remove="loading")

            refresh_btn.on_click(on_refresh_click)

        # 初始加载任务状态
        ui.timer(0.1, lambda: refresh_task_status(), once=True)
