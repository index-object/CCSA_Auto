"""任务信息区组件模块"""

from nicegui import ui
from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Task
from ccsa_auto.ui.utils.loading_utils import create_loading_button
from ccsa_auto.ui.utils.safe_notify import (
    safe_notify,
    safe_notify_success,
    safe_notify_error,
)
from ccsa_auto.utils.timezone import format_datetime_short
import logging

logger = logging.getLogger(__name__)


def create_task_section():
    """在主页面中嵌入的任务信息区"""
    with ui.card().classes(
        "w-full h-auto p-5 md:p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow duration-300"
    ):
        with ui.row().classes(
            "items-center gap-3 mb-5 md:mb-6 pb-4 border-b-2 border-gray-100"
        ):
            ui.icon("list_alt", size="1.5rem md:1.8rem").classes("text-blue-600")
            ui.label("任务管理").classes("text-xl md:text-2xl font-bold text-blue-600")

        # 任务数量标签
        task_count_label = ui.label("当前任务数量: 0").classes(
            "text-lg md:text-xl font-semibold text-gray-800 mb-4 md:mb-5"
        )

        # 任务列表容器 - 使用ui.list控件
        task_list = ui.list().classes("w-full").props("bordered separator")
        task_list_container = task_list

        def execute_task(task_id):
            """手动执行任务"""
            logger.info(f"[UI] execute_task 被调用, task_id={task_id}")
            if not task_id:
                safe_notify("请输入任务ID", type="warning")
                return

            try:
                from ccsa_auto.modules.task.service import TaskService
                from ccsa_auto.core.database import SessionLocal
                from ccsa_auto.core.models import Task, User

                db = SessionLocal()
                task = db.query(Task).filter_by(id=int(task_id)).first()
                logger.info(
                    f"[UI] 查询任务: task_id={task_id}, 找到={task is not None}"
                )
                if not task:
                    safe_notify_error(f"任务 {task_id} 不存在")
                    return

                user = db.query(User).filter_by(id=task.user_id).first()
                logger.info(
                    f"[UI] 查询用户: user_id={task.user_id}, 找到={user is not None}"
                )
                if not user:
                    safe_notify_error(f"用户 {task.user_id} 不存在")
                    return

                # 执行任务
                logger.info(
                    f"[UI] 开始执行任务: task_id={task_id}, task_type={task.task_type}"
                )
                result = TaskService.execute_task(task, user)
                logger.info(
                    f"[UI] 任务执行完成: success={result.get('success')}, message={result.get('message')}"
                )

                if result.get("success"):
                    safe_notify_success(
                        f"任务 {task_id} 执行成功: {result.get('message')}"
                    )
                else:
                    safe_notify_error(
                        f"任务 {task_id} 执行失败: {result.get('message')}"
                    )

                # 刷新任务列表
                refresh_tasks()

            except Exception as e:
                logger.exception(f"[UI] 执行任务异常: {str(e)}")
                safe_notify_error(f"执行任务失败: {str(e)}")
            finally:
                try:
                    db.close()
                except:
                    pass

        def execute_task_immediately(task_id):
            """立即执行任务（用于表格中的按钮）"""
            logger.info(f"[UI] execute_task_immediately 被调用, task_id={task_id}")
            execute_task(str(task_id))

        def refresh_tasks():
            """刷新任务列表（嵌入区）"""
            # 从数据库获取当前用户的任务列表
            db = SessionLocal()
            try:
                from ccsa_auto.modules.auth.session_manager import get_session_manager
                from ccsa_auto.modules.auth.user_state import UserStateService

                session_manager = get_session_manager()
                session_id = session_manager.get_current_session_id()

                user_id = None
                is_authenticated = False

                if session_id:
                    state = UserStateService.get_state(session_id)
                    if state:
                        user_info = state.get("user_info", {})
                        if user_info and "id" in user_info:
                            user_id = user_info.get("id")
                        if not user_id:
                            user_id = state.get("user_id")
                        is_authenticated = state.get("authenticated", False)

                if user_id and is_authenticated:
                    tasks = (
                        db.query(Task)
                        .filter_by(user_id=user_id)
                        .order_by(Task.created_at.desc())
                        .all()
                    )
                else:
                    # 如果没有用户ID或未认证，显示所有任务（仅用于调试）
                    tasks = (
                        db.query(Task).order_by(Task.created_at.desc()).limit(10).all()
                    )
                    if not is_authenticated:
                        safe_notify(
                            "用户未登录，显示所有任务（调试模式）", type="warning"
                        )

                # 清除现有列表内容
                task_list.clear()

                # 显示任务数量
                task_count_label.text = f"当前任务数量: {len(tasks)}"

                # 为每个任务创建列表项
                for task in tasks:
                    next_run = format_datetime_short(task.next_run_time)

                    # 根据任务类型设置显示文本
                    task_type_display = task.task_type
                    if task.task_type == "daily":
                        task_type_display = "每日任务"
                    elif task.task_type == "weekly":
                        task_type_display = "每周任务"
                    elif task.task_type == "monthly":
                        task_type_display = "每月任务"

                    # 根据执行状态设置显示文本
                    status_display = task.execution_status
                    if task.execution_status == "completed":
                        status_display = "已完成"
                    elif task.execution_status == "failed":
                        status_display = "失败"
                    elif task.execution_status == "pending":
                        status_display = "待执行"
                    elif task.execution_status == "running":
                        status_display = "执行中"

                    # 创建列表项
                    with task_list:
                        with ui.item().classes("w-full"):
                            with ui.item_section().classes("w-full"):
                                with ui.row().classes(
                                    "w-full items-center justify-between"
                                ):
                                    # 左侧任务信息
                                    with ui.column().classes("flex-1"):
                                        with ui.row().classes("items-center gap-3"):
                                            ui.label(f"ID: {task.id}").classes(
                                                "text-sm font-medium text-gray-600"
                                            )
                                            ui.label(
                                                task.task_name or task.task_type
                                            ).classes(
                                                "text-lg font-semibold text-gray-800"
                                            )
                                        with ui.row().classes(
                                            "items-center gap-4 mt-2"
                                        ):
                                            ui.label(
                                                f"类型: {task_type_display}"
                                            ).classes("text-sm text-gray-600")
                                            ui.label(f"状态: {status_display}").classes(
                                                "text-sm text-gray-600"
                                            )
                                            ui.label(f"下次执行: {next_run}").classes(
                                                "text-sm text-gray-600"
                                            )

                                    # 右侧操作按钮
                                    with ui.row().classes("items-center gap-2"):
                                        # 创建带加载动画的立即执行按钮
                                        # 使用默认参数解决闭包问题
                                        def create_execute_button(task_id):
                                            def on_click_handler():
                                                logger.info(
                                                    f"[UI] 按钮点击触发, task_id={task_id}"
                                                )
                                                execute_task_immediately(task_id)

                                            return create_loading_button(
                                                "立即执行",
                                                on_click=on_click_handler,
                                                icon="play_arrow",
                                            ).classes(
                                                "bg-green-50 hover:bg-green-100 text-green-600 font-medium py-2 px-4 rounded-lg shadow-sm text-sm"
                                            )

                                        # 为当前任务创建按钮
                                        create_execute_button(task.id)

            except Exception as e:
                logger.exception(f"[UI] 获取任务失败: {str(e)}")
                safe_notify_error(f"获取任务失败: {str(e)}")
                task_list_container.clear()
            finally:
                db.close()

        # 操作按钮区域 - 响应式布局
        with ui.column().classes(
            "w-full gap-4 md:gap-0 md:flex-row md:justify-between md:items-center mt-5 md:mt-6"
        ):
            with ui.row().classes("gap-3 flex-wrap"):
                create_loading_button(
                    "刷新任务", on_click=refresh_tasks, icon="refresh"
                ).classes(
                    "bg-blue-50 hover:bg-blue-100 text-blue-600 font-medium py-2 md:py-3 px-4 md:px-5 rounded-lg shadow-sm text-base"
                )

            # 快速操作按钮
            with ui.row().classes("gap-3"):
                # 查看全部按钮暂时保持原样，因为没有定义点击事件
                ui.button("查看全部", icon="visibility").classes(
                    "bg-gray-50 hover:bg-gray-100 text-gray-700 font-medium py-2 md:py-3 px-4 md:px-5 rounded-lg shadow-sm text-base"
                )

        # 初始加载任务
        refresh_tasks()
