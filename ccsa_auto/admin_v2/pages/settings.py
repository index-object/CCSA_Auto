from nicegui import ui

from ccsa_auto.core.config import Config
from ccsa_auto.core.system_config import SystemConfigService


def create_settings_page():
    """Create the settings page"""
    settings_data = {
        "task_fixer_enabled": Config.TASK_FIXER_ENABLED,
        "log_level": Config.LOG_LEVEL,
        "log_retention_days": Config.LOG_RETENTION_DAYS,
        "session_timeout": Config.SESSION_TIMEOUT,
        "session_absolute_timeout": Config.SESSION_ABSOLUTE_TIMEOUT,
    }

    score_config = {
        "target": SystemConfigService.get_score_target(),
        "threshold": SystemConfigService.get_score_threshold(),
        "random_min": SystemConfigService.get("score_random_min", 0.30),
        "random_max": SystemConfigService.get("score_random_max", 1.00),
        "enabled": SystemConfigService.is_score_strategy_enabled(),
        "daily_deduction_enabled": SystemConfigService.is_daily_deduction_enabled(),
        "daily_deduction_min": SystemConfigService.get("daily_deduction_min", 1),
        "daily_deduction_max": SystemConfigService.get("daily_deduction_max", 2),
    }

    task_details = Config.TASK_DETAILS
    daily_hours = task_details.get("DAILY", {}).get("hour_range", (7, 11))
    weekly_hours = task_details.get("WEEKLY", {}).get("hour_range", (8, 11))
    monthly_hours = task_details.get("MONTHLY", {}).get("hour_range", (9, 15))

    def save_task_fixer_setting(enabled: bool):
        settings_data["task_fixer_enabled"] = enabled
        ui.notify(
            "任务修复器设置已保存（注意：部分设置需要重启服务生效）", type="positive"
        )

    def save_log_setting(level: str, retention: int):
        settings_data["log_level"] = level
        settings_data["log_retention_days"] = retention
        ui.notify("日志设置已保存", type="positive")

    def save_session_setting(timeout: int, absolute_timeout: int):
        settings_data["session_timeout"] = timeout
        settings_data["session_absolute_timeout"] = absolute_timeout
        ui.notify("会话设置已保存", type="positive")

    def save_score_config():
        SystemConfigService.set("score_target", score_config["target"], "int")
        SystemConfigService.set("score_threshold", score_config["threshold"], "int")
        SystemConfigService.set("score_random_min", score_config["random_min"], "float")
        SystemConfigService.set("score_random_max", score_config["random_max"], "float")
        SystemConfigService.set("score_strategy_enabled", score_config["enabled"], "bool")
        SystemConfigService.set("daily_deduction_enabled", score_config["daily_deduction_enabled"], "bool")
        SystemConfigService.set("daily_deduction_min", score_config["daily_deduction_min"], "int")
        SystemConfigService.set("daily_deduction_max", score_config["daily_deduction_max"], "int")
        ui.notify("控分策略配置已保存", type="positive")

    ui.label("系统设置").classes("text-2xl font-bold mb-6 text-[#1f2937]")

    with ui.element("div").classes("overflow-y-auto max-h-[calc(100vh-200px)] pr-2"):
        with ui.card().classes("p-6 mb-6 rounded-2xl shadow-sm bg-white"):
            ui.label("任务调度配置").classes(
                "text-xl font-semibold mb-4 text-[#1f2937]"
            )

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("每日任务执行时间范围:").classes("w-40 text-[#6b7280]")
                ui.label(f"{daily_hours[0]}:00 - {daily_hours[1]}:00").classes(
                    "text-[#1f2937]"
                )

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("每周任务执行时间范围:").classes("w-40 text-[#6b7280]")
                ui.label(f"每周二 {weekly_hours[0]}:00 - {weekly_hours[1]}:00").classes(
                    "text-[#1f2937]"
                )

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("每月任务执行时间范围:").classes("w-40 text-[#6b7280]")
                ui.label(
                    f"每月15日 {monthly_hours[0]}:00 - {monthly_hours[1]}:00"
                ).classes("text-[#1f2937]")

            ui.label("提示: 任务调度时间在代码中配置，如需修改请联系开发人员").classes(
                "text-sm text-[#9ca3af]"
            )

        with ui.card().classes("p-6 mb-6 rounded-2xl shadow-sm bg-white"):
            ui.label("任务修复器").classes("text-xl font-semibold mb-4 text-[#1f2937]")

            with ui.row().classes("items-center gap-4 w-full"):
                ui.label("自动修复过期任务:").classes("w-40 text-[#6b7280]")
                ui.switch(
                    value=settings_data["task_fixer_enabled"],
                    on_change=lambda e: save_task_fixer_setting(e.value),
                ).props("color=positive")

            ui.label(
                "任务修复器会在每天凌晨自动检查并修复过期的任务，确保任务能够正常执行"
            ).classes("text-sm text-[#9ca3af] mt-2")

        with ui.card().classes("p-6 mb-6 rounded-2xl shadow-sm bg-white"):
            ui.label("控分策略配置").classes("text-xl font-semibold mb-4 text-[#1f2937]")

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("启用控分策略:").classes("w-40 text-[#6b7280]")
                ui.switch(
                    value=score_config["enabled"],
                    on_change=lambda e: (
                        score_config.update({"enabled": e.value}),
                        save_score_config(),
                    ),
                ).props("color=positive")

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("目标分数:").classes("w-40 text-[#6b7280]")
                ui.number(
                    value=score_config["target"],
                    on_change=lambda e: score_config.update({"target": int(e.value)}),
                    format="%.0f",
                ).props("outlined dense").classes("w-24")
                ui.label("分").classes("text-[#6b7280]")

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("接近阈值:").classes("w-40 text-[#6b7280]")
                ui.number(
                    value=score_config["threshold"],
                    on_change=lambda e: score_config.update({"threshold": int(e.value)}),
                    format="%.0f",
                ).props("outlined dense").classes("w-24")
                ui.label("分").classes("text-[#6b7280]")

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("随机分数范围:").classes("w-40 text-[#6b7280]")
                ui.number(
                    value=score_config["random_min"],
                    on_change=lambda e: score_config.update({"random_min": e.value}),
                    format="%.2f",
                    min=0,
                    max=1,
                ).props("outlined dense").classes("w-20")
                ui.label(" ~ ").classes("text-[#6b7280]")
                ui.number(
                    value=score_config["random_max"],
                    on_change=lambda e: score_config.update({"random_max": e.value}),
                    format="%.2f",
                    min=0,
                    max=1,
                ).props("outlined dense").classes("w-20")

            ui.button("保存配置", on_click=save_score_config).props(
                "flat color=primary"
            ).classes("mt-2")

            ui.label(
                "策略说明: 当前分数 < 目标-阈值 时满分；达到阈值后随机得分"
            ).classes("text-sm text-[#9ca3af] mt-2")

            # 分隔线
            ui.separator().classes("my-4")

            ui.label("每日一题随机扣分").classes("text-lg font-semibold mb-3 text-[#1f2937]")

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("启用随机扣分:").classes("w-40 text-[#6b7280]")
                ui.switch(
                    value=score_config["daily_deduction_enabled"],
                    on_change=lambda e: (
                        score_config.update({"daily_deduction_enabled": e.value}),
                        save_score_config(),
                    ),
                ).props("color=positive")

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("随机答错题数:").classes("w-40 text-[#6b7280]")
                ui.number(
                    value=score_config["daily_deduction_min"],
                    on_change=lambda e: score_config.update({"daily_deduction_min": int(e.value)}),
                    format="%.0f",
                    min=0,
                    max=10,
                ).props("outlined dense").classes("w-20")
                ui.label(" ~ ").classes("text-[#6b7280]")
                ui.number(
                    value=score_config["daily_deduction_max"],
                    on_change=lambda e: score_config.update({"daily_deduction_max": int(e.value)}),
                    format="%.0f",
                    min=0,
                    max=10,
                ).props("outlined dense").classes("w-20")
                ui.label("题").classes("text-[#6b7280]")

            ui.label(
                "说明: 启用后，每日一题在未达到目标分数前也会随机答错1-2题（扣2-4分）"
            ).classes("text-sm text-[#9ca3af] mt-2")

        with ui.card().classes("p-6 mb-6 rounded-2xl shadow-sm bg-white"):
            ui.label("日志配置").classes("text-xl font-semibold mb-4 text-[#1f2937]")

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("日志级别:").classes("w-40 text-[#6b7280]")
                ui.select(
                    value=settings_data["log_level"],
                    options=["DEBUG", "INFO", "WARNING", "ERROR"],
                    on_change=lambda e: save_log_setting(
                        e.value, settings_data["log_retention_days"]
                    ),
                ).props("outlined dense").classes("w-32")

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("日志保留天数:").classes("w-40 text-[#6b7280]")
                with ui.row().classes("items-center gap-2"):
                    ui.input(
                        value=str(settings_data["log_retention_days"]),
                        on_change=lambda e: save_log_setting(
                            settings_data["log_level"],
                            int(e.value) if e.value.isdigit() else 60,
                        ),
                    ).props("outlined dense type=number").classes("w-24")
                    ui.label("天").classes("text-[#6b7280]")

            ui.label("日志文件存储在 logs 目录下").classes("text-sm text-[#9ca3af]")

        with ui.card().classes("p-6 mb-6 rounded-2xl shadow-sm bg-white"):
            ui.label("会话配置").classes("text-xl font-semibold mb-4 text-[#1f2937]")

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("无活动过期时间:").classes("w-40 text-[#6b7280]")
                with ui.row().classes("items-center gap-2"):
                    ui.input(
                        value=str(settings_data["session_timeout"] // 3600),
                        on_change=lambda e: save_session_setting(
                            int(e.value) * 3600 if e.value.isdigit() else 3600,
                            settings_data["session_absolute_timeout"],
                        ),
                    ).props("outlined dense type=number").classes("w-24")
                    ui.label("小时").classes("text-[#6b7280]")

            with ui.row().classes("items-center gap-4 w-full mb-4"):
                ui.label("强制过期时间:").classes("w-40 text-[#6b7280]")
                with ui.row().classes("items-center gap-2"):
                    ui.input(
                        value=str(settings_data["session_absolute_timeout"] // 86400),
                        on_change=lambda e: save_session_setting(
                            settings_data["session_timeout"],
                            int(e.value) * 86400 if e.value.isdigit() else 86400,
                        ),
                    ).props("outlined dense type=number").classes("w-24")
                    ui.label("天").classes("text-[#6b7280]")

            ui.label("会话配置用于控制用户登录状态的有效期").classes(
                "text-sm text-[#9ca3af]"
            )

        with ui.card().classes("p-6 rounded-2xl shadow-sm bg-white"):
            ui.label("系统信息").classes("text-xl font-semibold mb-4 text-[#1f2937]")

            with ui.row().classes("items-center gap-4 w-full mb-2"):
                ui.label("系统版本:").classes("w-40 text-[#6b7280]")
                ui.label("CCSA Auto v2.0").classes("text-[#1f2937]")

            with ui.row().classes("items-center gap-4 w-full mb-2"):
                ui.label("数据库:").classes("w-40 text-[#6b7280]")
                ui.label("SQLite").classes("text-[#1f2937]")

            with ui.row().classes("items-center gap-4 w-full mb-2"):
                ui.label("时区:").classes("w-40 text-[#6b7280]")
                ui.label("Asia/Shanghai (UTC+8)").classes("text-[#1f2937]")

            with ui.row().classes("items-center gap-4 w-full"):
                ui.label("框架:").classes("w-40 text-[#6b7280]")
                ui.label("NiceGUI + SQLAlchemy").classes("text-[#1f2937]")


def render():
    """Render the settings page"""
    create_settings_page()