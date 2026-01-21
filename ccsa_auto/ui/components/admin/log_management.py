from nicegui import ui
from ccsa_auto.modules.logging.service import LoggingService


def create_log_management():
    with ui.column().classes("w-full"):
        with ui.row().classes("items-center gap-4 mb-4"):
            log_type_select = ui.select(
                {
                    "all": "全部",
                    "operation": "操作日志",
                    "task": "任务日志",
                    "auth": "认证日志",
                    "error": "错误日志",
                },
                label="日志类型",
                value="all",
            ).classes("w-32")
            log_user_input = ui.input("用户ID").classes("w-32")

        log_table = ui.table(
            columns=[
                {"name": "created_at", "label": "时间", "field": "created_at"},
                {"name": "log_type", "label": "类型", "field": "log_type"},
                {"name": "operation", "label": "操作", "field": "operation"},
                {"name": "content", "label": "内容", "field": "content"},
                {"name": "user_id", "label": "用户ID", "field": "user_id"},
                {"name": "status", "label": "状态", "field": "status"},
            ],
            rows=[],
            row_key="id",
        ).classes("w-full")

        log_page = ui.label("第 1 页").classes("text-center text-gray-600")

        def refresh_logs():
            result = LoggingService.get_logs(
                log_type=log_type_select.value
                if log_type_select.value != "all"
                else None,
                user_id=int(log_user_input.value) if log_user_input.value else None,
                page=1,
                page_size=20,
            )
            if result["success"]:
                log_type_map = {
                    "operation": "操作",
                    "task": "任务",
                    "auth": "认证",
                    "system": "系统",
                    "error": "错误",
                }
                for log in result["logs"]:
                    log["log_type"] = log_type_map.get(log.get("log_type"), "")
                log_table.rows = result["logs"]
                log_page.text = (
                    f"第 {result['page']} 页 / 共 {(result['total'] + 19) // 20} 页"
                )

        def change_page(delta):
            current_page = int(log_page.text.split(" ")[1])
            new_page = current_page + delta
            if new_page < 1:
                return
            result = LoggingService.get_logs(
                log_type=log_type_select.value
                if log_type_select.value != "all"
                else None,
                user_id=int(log_user_input.value) if log_user_input.value else None,
                page=new_page,
                page_size=20,
            )
            if result["success"]:
                log_type_map = {
                    "operation": "操作",
                    "task": "任务",
                    "auth": "认证",
                    "system": "系统",
                    "error": "错误",
                }
                for log in result["logs"]:
                    log["log_type"] = log_type_map.get(log.get("log_type"), "")
                log_table.rows = result["logs"]
                log_page.text = (
                    f"第 {new_page} 页 / 共 {(result['total'] + 19) // 20} 页"
                )

        def export_logs():
            filepath = LoggingService.export_to_xlsx(
                log_type=log_type_select.value
                if log_type_select.value != "all"
                else None
            )
            if filepath:
                ui.notify(f"日志已导出", type="positive")
                ui.download(filepath)
            else:
                ui.notify("导出失败", type="negative")

        with ui.row().classes("gap-3 mt-4"):
            ui.button("筛选", on_click=refresh_logs).classes(
                "bg-blue-600 text-white hover:bg-blue-700"
            )
            ui.button("导出XLSX", on_click=export_logs).classes(
                "bg-green-600 text-white hover:bg-green-700"
            )

        with ui.row().classes("justify-center mt-4 gap-4"):
            ui.button("上一页", on_click=lambda: change_page(-1)).classes(
                "bg-gray-200 text-gray-700 hover:bg-gray-300"
            )
            log_page
            ui.button("下一页", on_click=lambda: change_page(1)).classes(
                "bg-gray-200 text-gray-700 hover:bg-gray-300"
            )

        refresh_logs()
