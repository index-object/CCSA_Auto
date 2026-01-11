from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import logging

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Task, User
from ccsa_auto.modules.task.service import TaskService
from ccsa_auto.core.config import Config

# 创建后台调度器实例
scheduler = BackgroundScheduler()

# 配置日志
logger = logging.getLogger(__name__)

def calculate_next_run_time(task, now=None):
    """
    根据任务类型和配置计算下次运行时间
    
    Args:
        task: 任务对象
        now: 当前时间，默认为UTC当前时间
    
    Returns:
        datetime: 下次运行时间
    """
    import random
    from datetime import datetime as dt
    
    if now is None:
        now = datetime.utcnow()
    
    task_type = task.task_type
    
    if task_type == 'daily':
        hour_range = Config.TASK_DETAILS['DAILY']['hour_range']
        minute_range = Config.TASK_DETAILS['DAILY']['minute_range']
        # 生成随机小时和分钟
        hour = random.randint(hour_range[0], hour_range[1])
        minute = random.randint(minute_range[0], minute_range[1])
        # 计算今天的执行时间
        today_execution = dt(now.year, now.month, now.day, hour, minute, 0)
        # 如果当前时间已经过了今天的执行时间，则使用明天的时间
        if now >= today_execution:
            next_run = today_execution + timedelta(days=1)
        else:
            next_run = today_execution
        return next_run
        
    elif task_type == 'weekly':
        weekday = Config.TASK_DETAILS['WEEKLY']['weekday']
        hour_range = Config.TASK_DETAILS['WEEKLY']['hour_range']
        minute_range = Config.TASK_DETAILS['WEEKLY']['minute_range']
        hour = random.randint(hour_range[0], hour_range[1])
        minute = random.randint(minute_range[0], minute_range[1])
        # 计算距离下周二还有多少天
        days_until = (weekday - now.weekday()) % 7
        if days_until == 0:
            # 如果是今天，检查是否已经过了执行时间
            today_execution = dt(now.year, now.month, now.day, hour, minute, 0)
            if now >= today_execution:
                days_until = 7
        next_run = dt(now.year, now.month, now.day, hour, minute, 0) + timedelta(days=days_until)
        return next_run
        
    elif task_type == 'monthly':
        day = Config.TASK_DETAILS['MONTHLY']['day']
        hour_range = Config.TASK_DETAILS['MONTHLY']['hour_range']
        minute_range = Config.TASK_DETAILS['MONTHLY']['minute_range']
        hour = random.randint(hour_range[0], hour_range[1])
        minute = random.randint(minute_range[0], minute_range[1])
        # 计算下个月的同一天
        if now.month == 12:
            next_year = now.year + 1
            next_month = 1
        else:
            next_year = now.year
            next_month = now.month + 1
        # 创建下个月的时间
        next_run = dt(next_year, next_month, day, hour, minute, 0)
        # 如果当前日期是当天且还未到执行时间，则使用本月的当天
        if now.day == day:
            today_execution = dt(now.year, now.month, day, hour, minute, 0)
            if now < today_execution:
                next_run = today_execution
        return next_run
    else:
        # 未知任务类型，使用默认的24小时后
        return datetime.utcnow() + timedelta(days=1)

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
        task.execution_status = 'running'
        task.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"开始执行任务 {task_id} (用户: {user.id}, 类型: {task.task_type})")
        
        # 执行任务
        result = TaskService.execute_task(task, user)
        
        # 更新任务状态
        task.execution_status = 'completed' if result.get('success') else 'failed'
        task.external_status = 'success' if result.get('success') else 'failed'
        task.result = str(result)
        task.executed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        # 计算下次运行时间
        if task.is_active:
            try:
                task.next_run_time = calculate_next_run_time(task)
            except Exception as e:
                logger.error(f"计算下次运行时间失败: {e}")
                # 设置默认的下次运行时间（24小时后）
                task.next_run_time = datetime.utcnow() + timedelta(days=1)
        
        db.commit()
        
        # 重新调度下一次执行
        try:
            add_task_to_scheduler(task.id)
            logger.info(f"任务 {task_id} 已重新调度，下次运行时间: {task.next_run_time}")
        except Exception as e:
            logger.error(f"重新调度任务 {task_id} 失败: {e}")
        
        if result.get('success'):
            logger.info(f"任务 {task_id} 执行成功: {result.get('message')}")
        else:
            logger.error(f"任务 {task_id} 执行失败: {result.get('message')}")
            
    except Exception as e:
        logger.exception(f"执行任务 {task_id} 时发生异常: {e}")
        
        # 更新任务状态为失败
        try:
            # 重新获取任务对象，因为之前的task变量可能未定义或已失效
            db.rollback()  # 回滚之前的操作
            task = db.query(Task).filter_by(id=task_id).first()
            if task:
                task.execution_status = 'failed'
                task.external_status = 'failed'
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
        # 检查调度器是否已经运行
        if scheduler.running:
            logger.info("任务调度器已经在运行")
            return
        
        logger.info("开始初始化任务调度器")
        
        # 从数据库加载所有激活的任务
        db = SessionLocal()
        try:
            active_tasks = db.query(Task).filter_by(is_active=True).all()
            logger.info(f"从数据库加载了 {len(active_tasks)} 个激活的任务")
            
            for task in active_tasks:
                try:
                    # 为每个任务创建调度任务
                    if not task.cron_expression:
                        logger.warning(f"任务 {task.id} 没有cron表达式，跳过调度")
                        continue
                    
                    job_id = f"user_task_{task.id}"
                    
                    # 检查是否已存在相同ID的任务
                    existing_job = scheduler.get_job(job_id)
                    if existing_job:
                        scheduler.remove_job(job_id)
                    
                    # 确定下次运行时间
                    run_time = task.next_run_time
                    if not run_time:
                        # 如果没有设置下次运行时间，则根据任务类型计算
                        try:
                            run_time = calculate_next_run_time(task)
                            # 更新数据库中的next_run_time
                            task.next_run_time = run_time
                            db.commit()
                        except Exception as e:
                            logger.error(f"计算下次运行时间失败: {e}")
                            run_time = datetime.utcnow() + timedelta(days=1)
                    
                    # 确保运行时间在未来
                    if run_time <= datetime.utcnow():
                        # 如果已经过期，重新计算下一次
                        try:
                            run_time = calculate_next_run_time(task)
                        except Exception:
                            run_time = datetime.utcnow() + timedelta(days=1)
                    
                    # 使用DateTrigger在具体时间点调度
                    scheduler.add_job(
                        func=execute_user_task,
                        args=[task.id],
                        trigger=DateTrigger(run_time),
                        id=job_id,
                        name=f"{task.task_name} (用户{task.user_id})",
                        replace_existing=True
                    )
                    
                    logger.info(f"添加任务调度: {job_id} - {task.task_name} (运行时间: {run_time})")
                        
                except Exception as e:
                    logger.error(f"添加任务 {task.id} 到调度器失败: {e}")
                    
        finally:
            db.close()
        
        # 启动调度器
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
        
        # 检查是否已存在相同ID的任务
        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)
        
        # 确定下次运行时间
        run_time = task.next_run_time
        if not run_time:
            # 如果没有设置下次运行时间，则根据任务类型计算
            try:
                run_time = calculate_next_run_time(task)
                # 更新数据库中的next_run_time
                task.next_run_time = run_time
                db.commit()
            except Exception as e:
                logger.error(f"计算下次运行时间失败: {e}")
                run_time = datetime.utcnow() + timedelta(days=1)
        
        # 确保运行时间在未来
        if run_time <= datetime.utcnow():
            # 如果已经过期，重新计算下一次
            try:
                run_time = calculate_next_run_time(task)
            except Exception:
                run_time = datetime.utcnow() + timedelta(days=1)
        
        # 使用DateTrigger在具体时间点调度
        scheduler.add_job(
            func=execute_user_task,
            args=[task.id],
            trigger=DateTrigger(run_time),
            id=job_id,
            name=f"{task.task_name} (用户{task.user_id})",
            replace_existing=True
        )
        
        logger.info(f"添加任务到调度器: {job_id} - {task.task_name} (运行时间: {run_time})")
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
