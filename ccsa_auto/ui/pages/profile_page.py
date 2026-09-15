"""个人中心页面模块"""

from nicegui import ui
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.modules.auth.models import auth_state
from ccsa_auto.core.user_score_config import get_user_score_config


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

        # 控分策略状态卡片（只读）
        with ui.card().classes("w-full p-6 mt-6"):
            ui.label("控分策略状态").classes("text-lg font-semibold mb-4")

            async def load_score_control_status():
                if auth_state.user_info and auth_state.user_info.get("id"):
                    user_id = auth_state.user_info["id"]
                    scores = AuthService.get_scores(auth_state.external_token) if auth_state.external_token else None
                    cfg = get_user_score_config(user_id)

                    current_monthly_score = scores.get("monthly_score", 0) if scores else 0
                    target = cfg["score_target"]
                    enabled = cfg["score_strategy_enabled"]

                    progress_percentage = (
                        (current_monthly_score / target) * 100 if target > 0 else 0
                    )

                    if not enabled:
                        status_text = "未启用"
                        status_color = "bg-gray-100 text-gray-800"
                        progress_color = "bg-gray-400"
                    elif current_monthly_score >= target:
                        status_text = "已达标"
                        status_color = "bg-green-100 text-green-800"
                        progress_color = "bg-green-500"
                    else:
                        status_text = "正常进行中"
                        status_color = "bg-blue-100 text-blue-800"
                        progress_color = "bg-blue-500"

                    with ui.row().classes("w-full justify-between items-center"):
                        with ui.column().classes("flex-1"):
                            ui.label(f"本月进度: {progress_percentage:.1f}%").classes(
                                "text-sm text-gray-600"
                            )
                            ui.label(
                                f"{current_monthly_score} / {target} 分"
                            ).classes("text-2xl font-bold")

                            with ui.row().classes(
                                "w-full h-4 bg-gray-200 rounded-full overflow-hidden mt-2"
                            ):
                                ui.row().classes(
                                    f"h-full {progress_color} rounded-full transition-all duration-300"
                                ).style(f"width: {min(progress_percentage, 100)}%")

                        ui.label(status_text).classes(
                            f"px-3 py-1 rounded-full text-sm font-semibold {status_color}"
                        )

                    # 分数明细
                    if scores:
                        with ui.row().classes("w-full mt-6 gap-8"):
                            with ui.column().classes("flex-1 text-center"):
                                ui.label("每日一题").classes("text-sm text-gray-600")
                                ui.label(f"{scores.get('daily_score', 0)} 分").classes(
                                    "text-xl font-semibold text-blue-600"
                                )
                            with ui.column().classes("flex-1 text-center"):
                                ui.label("每周一课").classes("text-sm text-gray-600")
                                ui.label(f"{scores.get('weekly_score', 0)} 分").classes(
                                    "text-xl font-semibold text-purple-600"
                                )
                            with ui.column().classes("flex-1 text-center"):
                                ui.label("每月一考").classes("text-sm text-gray-600")
                                ui.label(f"{scores.get('monthly_score', 0)} 分").classes(
                                    "text-xl font-semibold text-orange-600"
                                )

                    # 提示信息
                    with ui.row().classes("w-full mt-4"):
                        if not enabled:
                            ui.label("控分策略未启用").classes(
                                "text-sm text-gray-700 bg-gray-50 px-4 py-2 rounded-lg"
                            )
                        elif current_monthly_score >= target:
                            ui.label(
                                "已达到本月目标，后续任务将保持最低得分比例"
                            ).classes(
                                "text-sm text-green-700 bg-green-50 px-4 py-2 rounded-lg"
                            )
                        else:
                            remaining = target - current_monthly_score
                            ui.label(
                                f"正常进行中，还需获得 {remaining} 分即可达标"
                            ).classes(
                                "text-sm text-blue-700 bg-blue-50 px-4 py-2 rounded-lg"
                            )
                else:
                    ui.label("需要登录后查看控分策略状态").classes("text-gray-500")

            ui.timer(0.1, lambda: load_score_control_status(), once=True)
