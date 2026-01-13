from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta, timezone
import logging

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Task, User
from ccsa_auto.modules.task.service import TaskService
from ccsa_auto.core.config import Config
from ccsa_auto.utils.timezone import (
    get_current_time,
    get_current_utc_time,
    utc_to_shanghai,
    shanghai_to_utc,
    format_datetime_for_display,
    format_datetime_short,
    SHANGHAI_TZ,
    calculate_next_run_time_utc,
    ensure_utc_timezone,
)


def cleanup_expired_sessions_job():
    """定时清理过期会话任务"""
    try:
        from ccsa_auto.modules.auth.session_manager import get_session_manager

        session_manager = get_session_manager()
        count = session_manager.cleanup_expired_sessions()
        if count > 0:
            logger.info(f"定时任务: 已清理 {count} 个过期会话")
    except Exception as e:
        logger.error(f"清理过期会话任务失败: {e}")


# 创建后台调度器实例
scheduler = BackgroundScheduler()

# 配置日志
logger = logging.getLogger(__name__)


def execute_user_task(task_id):
    """
    执行用户任务

    Args:
        task_id: 任务ID
    """
    db = SessionLocal()
    try:
        # 获取任务
        task = db.query(Task).filter_by(id=task_id).first()
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return

        # 获取用户
        user = db.query(User).filter_by(id=task.user_id).first()
        if not user:
            logger.error(f"用户 {task.user_id} 不存在")
            return

        # 检查任务是否激活
        if not task.is_active:
            logger.info(f"任务 {task_id} 未激活，跳过执行")
            return

        # 更新任务状态为运行中
        task.execution_status = "running"
        task.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"开始执行任务 {task_id} (用户: {user.id}, 类型: {task.task_type})")

        # 执行任务
        result = TaskService.execute_task(task, user)

        # 获取当前执行时间（上海时间）
        executed_at_shanghai = get_current_time()

        # 更新任务状态
        task.execution_status = "completed" if result.get("success") else "failed"
        task.external_status = "success" if result.get("success") else "failed"
        task.result = str(result)
        task.executed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()

        # 基于执行时间计算下次运行时间（确保是明天）
        if task.is_active:
            try:
                task.next_run_time = calculate_next_run_time_utc(
                    task, executed_at_shanghai
                )
            except Exception as e:
                logger.error(f"计算下次运行时间失败: {e}")
                task.next_run_time = get_current_utc_time() + timedelta(days=1)

        db.commit()

        # 重新调度下一次执行
        try:
            add_task_to_scheduler(task.id)
            logger.info(
                f"任务 {task_id} 已重新调度，下次运行时间: {format_datetime_for_display(task.next_run_time)}"
            )
        except Exception as e:
            logger.error(f"重新调度任务 {task_id} 失败: {e}")

        if result.get("success"):
            logger.info(f"任务 {task_id} 执行成功: {result.get('message')}")
        else:
            logger.error(f"任务 {task_id} 执行失败: {result.get('message')}")

    except Exception as e:
        logger.exception(f"执行任务 {task_id} 时发生异常: {e}")

        # 更新任务状态为失败
        try:
            db.rollback()
            task = db.query(Task).filter_by(id=task_id).first()
            if task:
                task.execution_status = "failed"
                task.external_status = "failed"
                task.result = f"异常: {str(e)}"
                task.executed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"任务 {task_id} 状态已更新为失败")
        except Exception as update_error:
            logger.error(f"更新任务 {task_id} 状态失败: {update_error}")
    finally:
        db.close()


def init_scheduler():
    """
    初始化任务调度器
    """
    try:
        if scheduler.running:
            logger.info("任务调度器已经在运行")
            return

        logger.info("开始初始化任务调度器")

        db = SessionLocal()
        try:
            active_tasks = db.query(Task).filter_by(is_active=True).all()
            logger.info(f"从数据库加载了 {len(active_tasks)} 个激活的任务")

            for task in active_tasks:
                try:
                    if not task.cron_expression:
                        logger.warning(f"任务 {task.id} 没有cron表达式，跳过调度")
                        continue

                    job_id = f"user_task_{task.id}"

                    existing_job = scheduler.get_job(job_id)
                    if existing_job:
                        scheduler.remove_job(job_id)

                    run_time = task.next_run_time
                    if not run_time:
                        try:
                            run_time = calculate_next_run_time_utc(task)
                            task.next_run_time = run_time
                            db.commit()
                        except Exception as e:
                            logger.error(f"计算下次运行时间失败: {e}")
                            run_time = get_current_utc_time() + timedelta(days=1)

                    # 确保run_time有时区信息
                    run_time = ensure_utc_timezone(run_time)
                    current_utc = get_current_utc_time()

                    if run_time <= current_utc:
                        try:
                            run_time = calculate_next_run_time_utc(
                                task, get_current_time()
                            )
                            run_time = ensure_utc_timezone(run_time)
                            # 关键修复：更新数据库中的 next_run_time
                            task.next_run_time = run_time
                            db.commit()
                            logger.info(
                                f"任务 {task.id} 的过期时间已修正为: {format_datetime_for_display(run_time)}"
                            )
                        except Exception:
                            run_time = get_current_utc_time() + timedelta(days=1)

                    if run_time <= current_utc:
                        run_time = current_utc + timedelta(seconds=1)

                    scheduler.add_job(
                        func=execute_user_task,
                        args=[task.id],
                        trigger=DateTrigger(run_time),
                        id=job_id,
                        name=f"{task.task_name} (用户{task.user_id})",
                        replace_existing=True,
                    )

                    logger.info(
                        f"添加任务调度: {job_id} - {task.task_name} (运行时间: {format_datetime_for_display(run_time)}"
                    )

                except Exception as e:
                    logger.error(f"添加任务 {task.id} 到调度器失败: {e}")

        finally:
            db.close()

        # 添加清理过期会话的定时任务（每小时执行一次）
        scheduler.add_job(
            func=cleanup_expired_sessions_job,
            trigger=CronTrigger(minute=0),
            id="cleanup_expired_sessions",
            name="清理过期会话",
            replace_existing=True,
        )
        logger.info("已添加清理过期会话定时任务（每小时执行一次）")

        scheduler.start()
        logger.info("任务调度器初始化完成并已启动")

    except Exception as e:
        logger.error(f"初始化任务调度器失败: {e}")


def start_scheduler():
    """
    启动任务调度器
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("任务调度器已启动")


def stop_scheduler():
    """
    停止任务调度器
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("任务调度器已停止")


def add_task_to_scheduler(task_id):
    """
    添加单个任务到调度器

    Args:
        task_id: 任务ID
    """
    db = SessionLocal()
    try:
        task = db.query(Task).filter_by(id=task_id).first()
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return False

        if not task.is_active:
            logger.info(f"任务 {task_id} 未激活，不添加到调度器")
            return False

        if not task.cron_expression:
            logger.warning(f"任务 {task_id} 没有cron表达式，无法调度")
            return False

        job_id = f"user_task_{task.id}"

        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)

        run_time = task.next_run_time
        if not run_time:
            try:
                run_time = calculate_next_run_time_utc(task)
                task.next_run_time = run_time
                db.commit()
            except Exception as e:
                logger.error(f"计算下次运行时间失败: {e}")
                run_time = get_current_utc_time() + timedelta(days=1)

        run_time = ensure_utc_timezone(run_time)
        current_utc = get_current_utc_time()

        if run_time <= current_utc:
            try:
                run_time = calculate_next_run_time_utc(task, get_current_time())
                run_time = ensure_utc_timezone(run_time)
                # 关键修复：更新数据库中的 next_run_time
                task.next_run_time = run_time
                db.commit()
                logger.info(
                    f"任务 {task.id} 的过期时间已修正为: {format_datetime_for_display(run_time)}"
                )
            except Exception:
                run_time = get_current_utc_time() + timedelta(days=1)

        if run_time <= current_utc:
            run_time = current_utc + timedelta(seconds=1)

        scheduler.add_job(
            func=execute_user_task,
            args=[task.id],
            trigger=DateTrigger(run_time),
            id=job_id,
            name=f"{task.task_name} (用户{task.user_id})",
            replace_existing=True,
        )

        logger.info(
            f"添加任务到调度器: {job_id} - {task.task_name} (运行时间: {format_datetime_for_display(run_time)}"
        )
        return True

    except Exception as e:
        logger.error(f"添加任务 {task_id} 到调度器失败: {e}")
        return False
    finally:
        db.close()


def remove_task_from_scheduler(task_id):
    """
    从调度器移除任务

    Args:
        task_id: 任务ID
    """
    job_id = f"user_task_{task_id}"
    try:
        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)
            logger.info(f"从调度器移除任务: {job_id}")
            return True
        else:
            logger.info(f"调度器中未找到任务: {job_id}")
            return False
    except Exception as e:
        logger.error(f"从调度器移除任务 {task_id} 失败: {e}")
        return False
