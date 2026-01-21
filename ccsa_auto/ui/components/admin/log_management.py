from nicegui import ui
from ccsa_auto.modules.logging.service import LoggingService
from ccsa_auto.ui.components.admin.common import (
    PageHeader,
    LoadingOverlay,
    ConfirmDialog,
    Toast,
)


def create_log_management():
    """创建操作日志页面 - 现代化增强版"""
    loading = LoadingOverlay("加载日志数据中...")
    current_page = [1]

    # 页面标题
    header = PageHeader(
        title="操作日志",
        subtitle="查看系统操作记录和审计日志",
        icon="receipt_long",
    )
    header.render()

    # 筛选工具栏
    with ui.row().classes(
        "items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 "
        "shadow-sm mb-4 flex-wrap"
    ):
        log_type_select = ui.select(
            {
                "all": "全部类型",
                "operation": "操作日志",
                "task": "任务日志",
                "auth": "认证日志",
                "error": "错误日志",
            },
            label="日志类型",
            value="all",
        ).classes(
            "w-36 px-4 py-2.5 bg-gray-50 border border-gray-200 "
            "rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        )
        log_user_input = ui.input("用户ID").classes(
            "w-32 px-4 py-2.5 bg-gray-50 border border-gray-200 "
            "rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        )

        filter_btn = ui.button("筛选").classes(
            "bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        )
        export_btn = ui.button("导出XLSX").classes(
            "bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
        )

    # 日志表格
    log_table = ui.table(
        columns=[
            {
                "name": "created_at",
                "label": "时间",
                "field": "created_at",
                "sortable": True,
            },
            {
                "name": "log_type",
                "label": "类型",
                "field": "log_type",
                "sortable": True,
            },
            {"name": "operation", "label": "操作", "field": "operation"},
            {"name": "content", "label": "内容", "field": "content"},
            {"name": "user_id", "label": "用户ID", "field": "user_id"},
            {"name": "status", "label": "状态", "field": "status", "align": "center"},
        ],
        rows=[],
        row_key="id",
    ).classes(
        "w-full bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden"
    )

    # 分页信息
    page_info = ui.label("第 1 页").classes("text-center text-gray-600")

    # 分页控制
    with ui.row().classes("justify-center items-center mt-4 gap-4"):
        prev_btn = ui.button("上一页").classes(
            "px-4 py-2 bg-white border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50"
        )
        page_info
        next_btn = ui.button("下一页").classes(
            "px-4 py-2 bg-white border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50"
        )

    # 定义函数
    def refresh_logs():
        loading.show()
        try:
            result = LoggingService.get_logs(
                log_type=log_type_select.value
                if log_type_select.value != "all"
                else None,
                user_id=int(log_user_input.value) if log_user_input.value else None,
                page=current_page[0],
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
                logs = result["logs"]
                for log in logs:
                    log["log_type"] = log_type_map.get(log.get("log_type"), "")
                log_table.rows = logs
                total_pages = (result["total"] + 19) // 20
                page_info.text = f"第 {current_page[0]} 页 / 共 {total_pages} 页"
            else:
                Toast.error(result.get("message", "获取日志失败"))
        except Exception as e:
            Toast.error(f"加载失败: {str(e)}")
        finally:
            loading.close()

    def change_page(delta: int):
        new_page = current_page[0] + delta
        if new_page < 1:
            return
        current_page[0] = new_page
        refresh_logs()

    def export_logs():
        result = LoggingService.export_to_xlsx(
            log_type=log_type_select.value if log_type_select.value != "all" else None
        )
        if result:
            Toast.success("日志导出成功")
            ui.download(result)
        else:
            Toast.error("导出失败")

    # 绑定事件
    filter_btn.on("click", refresh_logs)
    export_btn.on("click", export_logs)
    prev_btn.on("click", lambda: change_page(-1))
    next_btn.on("click", lambda: change_page(1))

    # 初始加载
    refresh_logs()
