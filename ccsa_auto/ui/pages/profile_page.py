"""个人中心页面模块"""

from nicegui import ui
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.models import auth_state


def create_profile_page():
    """创建个人中心页面"""
    with ui.card().classes("w-full h-auto p-6 page-card profile-page"):
        ui.label("个人中心").classes("text-2xl font-bold mb-6")

        with ui.row().classes("gap-6"):
            # 个人信息卡片
            with ui.card().classes("p-4"):
                ui.label("个人信息").classes("text-lg font-semibold mb-4")
                if auth_state.user_info:
                    ui.label(f"账号: {auth_state.user_info['username']}")
                    ui.label(f"公司: {auth_state.user_info['company_name']}")
                else:
                    ui.label("未登录")

            # 积分卡片
            with ui.card().classes("p-4"):
                ui.label("积分信息").classes("text-lg font-semibold mb-4")

                # 调用服务获取积分信息
                async def load_scores():
                    # 使用外部访问令牌获取积分信息
                    if auth_state.external_token:
                        scores = AuthService.get_scores(auth_state.external_token)
                        if scores:
                            ui.label(f"本年积分: {scores['total_score']}")
                            ui.label(f"当月积分: {scores['monthly_score']}")
                        else:
                            ui.label("积分信息加载失败")
                    else:
                        ui.label("未获取到外部平台令牌")

                # 异步加载积分信息 - 使用timer立即执行
                ui.timer(0.1, lambda: load_scores(), once=True)

        # 控分策略状态卡片
        with ui.card().classes("w-full p-6 mt-6"):
            ui.label("控分策略状态").classes("text-lg font-semibold mb-4")

            # 调用服务获取控分策略状态
            async def load_score_control_status():
                if auth_state.user_info and auth_state.user_info.get("id"):
                    from ccsa_auto.modules.task.score_tracker import ScoreTracker

                    user_id = auth_state.user_info["id"]
                    status = ScoreTracker.get_score_control_status(user_id)

                    # 创建状态显示
                    with ui.row().classes("w-full justify-between items-center"):
                        # 进度显示
                        with ui.column().classes("flex-1"):
                            ui.label(
                                f"本月进度: {status['progress_percentage']}%"
                            ).classes("text-sm text-gray-600")
                            ui.label(
                                f"{status['current_monthly_score']} / {status['target_monthly_score']} 分"
                            ).classes("text-2xl font-bold")

                            # 进度条
                            progress_color = (
                                "bg-green-500"
                                if status["status"] == "ahead"
                                else (
                                    "bg-blue-500"
                                    if status["status"] == "on_track"
                                    else "bg-red-500"
                                )
                            )
                            with ui.row().classes(
                                "w-full h-4 bg-gray-200 rounded-full overflow-hidden mt-2"
                            ):
                                ui.row().classes(
                                    f"h-full {progress_color} rounded-full transition-all duration-300"
                                ).style(
                                    f"width: {min(status['progress_percentage'], 100)}%"
                                )

                        # 状态标签
                        status_color = (
                            "bg-green-100 text-green-800"
                            if status["status"] == "ahead"
                            else (
                                "bg-blue-100 text-blue-800"
                                if status["status"] == "on_track"
                                else "bg-red-100 text-red-800"
                            )
                        )
                        ui.label(status["status_text"]).classes(
                            f"px-3 py-1 rounded-full text-sm font-semibold {status_color}"
                        )

                    # 分数明细
                    with ui.row().classes("w-full mt-6 gap-8"):
                        with ui.column().classes("flex-1 text-center"):
                            ui.label("每日一题").classes("text-sm text-gray-600")
                            ui.label(f"{status['breakdown']['daily']} 分").classes(
                                "text-xl font-semibold text-blue-600"
                            )

                        with ui.column().classes("flex-1 text-center"):
                            ui.label("每周一课").classes("text-sm text-gray-600")
                            ui.label(f"{status['breakdown']['weekly']} 分").classes(
                                "text-xl font-semibold text-purple-600"
                            )

                        with ui.column().classes("flex-1 text-center"):
                            ui.label("每月一考").classes("text-sm text-gray-600")
                            ui.label(f"{status['breakdown']['monthly']} 分").classes(
                                "text-xl font-semibold text-orange-600"
                            )

                    # 提示信息
                    with ui.row().classes("w-full mt-4"):
                        if status["status"] == "ahead":
                            ui.label(
                                "已达到本月目标，后续任务将保持最低得分比例（30%）"
                            ).classes(
                                "text-sm text-green-700 bg-green-50 px-4 py-2 rounded-lg"
                            )
                        elif status["status"] == "on_track":
                            remaining = status["remaining_potential"]
                            ui.label(
                                f"正常进行中，本月底还可能获得 {remaining} 分"
                            ).classes(
                                "text-sm text-blue-700 bg-blue-50 px-4 py-2 rounded-lg"
                            )
                        else:
                            ui.label(
                                "当前进度落后，后续任务将以更高得分比例追分"
                            ).classes(
                                "text-sm text-red-700 bg-red-50 px-4 py-2 rounded-lg"
                            )
                else:
                    ui.label("需要登录后查看控分策略状态").classes("text-gray-500")

            # 异步加载控分策略状态 - 使用timer立即执行
            ui.timer(0.1, lambda: load_score_control_status(), once=True)
