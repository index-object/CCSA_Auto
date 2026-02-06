"""个人信息区组件模块 - 基于app.storage.user的会话隔离版本"""

from nicegui import ui, app
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.session_manager import get_session_manager
from ccsa_auto.modules.auth.user_state import UserStateService


def create_profile_section():
    """在主页面中嵌入的个人信息区"""
    session_manager = get_session_manager()
    session_id = session_manager.get_current_session_id()

    if session_id:
        state = UserStateService.get_state(session_id)
        user_info = state.get("user_info", {}) if state else {}
    else:
        user_info = {}

    username = user_info.get("username", "用户")
    avatar_text = username[0] if username else "用"

    with ui.card().classes(
        "w-full h-auto p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300 mb-6"
    ):
        with ui.row().classes(
            "items-center gap-2 mb-6 pb-4 border-b-2 border-gray-100"
        ):
            ui.icon("person", size="1.5rem").classes("text-blue-600")
            ui.label("个人信息").classes("text-xl font-bold text-blue-600")

        with ui.row().classes("w-full items-center gap-8"):
            with ui.column().classes("items-center"):
                with ui.card().classes(
                    "w-20 h-20 md:w-24 md:h-24 bg-gradient-to-br from-blue-400 to-blue-700 rounded-full flex items-center justify-center shadow-lg"
                ):
                    ui.label(avatar_text).classes(
                        "text-2xl md:text-3xl font-bold text-white"
                    )

            with ui.column().classes("flex-1 gap-3"):
                if user_info:
                    with ui.row().classes("items-center gap-3"):
                        ui.icon("badge", size="1.2rem").classes("text-gray-500")
                        ui.label(f"账号: {user_info.get('username', '未知')}").classes(
                            "text-gray-700 text-base"
                        )

                    with ui.row().classes("items-center gap-3"):
                        ui.icon("business", size="1.2rem").classes("text-gray-500")
                        ui.label(
                            f"公司: {user_info.get('company_name') or '-'}"
                        ).classes("text-gray-700 text-base")
                else:
                    ui.label("未登录").classes("text-gray-500 text-base")

    with ui.card().classes(
        "w-full h-auto p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300"
    ):
        with ui.row().classes(
            "items-center gap-2 mb-6 pb-4 border-b-2 border-gray-100"
        ):
            ui.icon("trending_up", size="1.8rem").classes("text-blue-600")
            ui.label("积分信息").classes("text-2xl font-bold text-blue-600")

        with ui.row().classes("w-full gap-6"):
            with ui.card().classes(
                "flex-1 p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl text-center hover:shadow-md transition-shadow duration-300"
            ):
                ui.label("本年积分").classes("text-lg text-gray-600 mb-3")
                total_score_label = ui.label("加载中...").classes(
                    "text-4xl font-bold text-blue-700 mb-2"
                )
                ui.label("本年总分").classes("text-sm text-gray-500")

            with ui.card().classes(
                "flex-1 p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-xl text-center hover:shadow-md transition-shadow duration-300"
            ):
                ui.label("本月积分").classes("text-lg text-gray-600 mb-3")
                monthly_score_label = ui.label("加载中...").classes(
                    "text-4xl font-bold text-green-700 mb-2"
                )
                ui.label("本月已获得").classes("text-sm text-gray-500")

        async def load_scores_embedded():
            external_token = None
            if session_id:
                state = UserStateService.get_state(session_id)
                if state:
                    external_token = state.get("external_token")

            if external_token:
                scores = AuthService.get_scores(external_token)
                if scores:
                    total_score_label.text = str(scores.get("total_score", 0))
                    monthly_score_label.text = str(scores.get("monthly_score", 0))
                else:
                    total_score_label.text = "0"
                    monthly_score_label.text = "0"
            else:
                total_score_label.text = "0"
                monthly_score_label.text = "0"

        ui.timer(0.1, lambda: load_scores_embedded(), once=True)

    # 控分策略状态卡片
    with ui.card().classes(
        "w-full h-auto p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300 mt-6"
    ):
        with ui.row().classes(
            "items-center gap-2 mb-6 pb-4 border-b-2 border-gray-100"
        ):
            ui.icon("analytics", size="1.8rem").classes("text-purple-600")
            ui.label("控分策略状态").classes("text-2xl font-bold text-purple-600")

        def load_score_control_status_embedded():
            if session_id:
                state = UserStateService.get_state(session_id)
                if state:
                    user_info = state.get("user_info", {})
                else:
                    user_info = {}
            else:
                user_info = {}

            if user_info and user_info.get("id"):
                from ccsa_auto.modules.auth.service import AuthService

                user_id = user_info.get("id")
                scores = AuthService.get_scores_with_retry(user_id)

                if scores:
                    current_monthly_score = scores.get("monthly_score", 0)
                    target_monthly_score = 570

                    # 计算进度百分比
                    progress_percentage = (
                        (current_monthly_score / target_monthly_score) * 100
                        if target_monthly_score > 0
                        else 0
                    )

                    # 确定状态
                    if current_monthly_score >= target_monthly_score:
                        status = "ahead"
                        status_text = "已达标"
                    else:
                        status = "on_track"
                        status_text = "正常进行中"

                    # 创建状态显示
                    with ui.row().classes("w-full justify-between items-center"):
                        # 进度显示
                        with ui.column().classes("flex-1"):
                            ui.label(f"本月进度: {progress_percentage:.1f}%").classes(
                                "text-sm text-gray-600 mb-2"
                            )
                            ui.label(
                                f"{current_monthly_score} / {target_monthly_score} 分"
                            ).classes("text-2xl font-bold mb-3")

                            # 进度条
                            progress_color = (
                                "bg-green-500" if status == "ahead" else "bg-blue-500"
                            )
                            with ui.row().classes(
                                "w-full h-4 bg-gray-200 rounded-full overflow-hidden"
                            ):
                                ui.row().classes(
                                    f"h-full {progress_color} rounded-full transition-all duration-300"
                                ).style(f"width: {min(progress_percentage, 100)}%")

                        # 状态标签
                        status_color = (
                            "bg-green-100 text-green-800"
                            if status == "ahead"
                            else "bg-blue-100 text-blue-800"
                        )
                        ui.label(status_text).classes(
                            f"px-4 py-2 rounded-full text-sm font-semibold {status_color}"
                        )

                    # 提示信息
                    with ui.row().classes("w-full mt-6"):
                        if status == "ahead":
                            ui.label(
                                "已达到本月目标，后续任务将保持最低得分比例（50%）"
                            ).classes(
                                "text-sm text-green-700 bg-green-50 px-4 py-2 rounded-lg"
                            )
                        else:
                            remaining = target_monthly_score - current_monthly_score
                            ui.label(
                                f"正常进行中，还需获得 {remaining} 分即可达标"
                            ).classes(
                                "text-sm text-blue-700 bg-blue-50 px-4 py-2 rounded-lg"
                            )
            else:
                ui.label("需要登录后查看控分策略状态").classes("text-gray-500")

        ui.timer(0.1, lambda: load_score_control_status_embedded(), once=True)
