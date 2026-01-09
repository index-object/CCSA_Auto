from apscheduler.schedulers.background import BackgroundScheduler

# 创建后台调度器实例
scheduler = BackgroundScheduler()

def init_scheduler():
    """
    初始化任务调度器
    """
    try:
        # 检查调度器是否已经运行
        if scheduler.running:
            print("任务调度器已经在运行")
            return
        
        # 添加定时任务
        # 每天9:00执行每日一题
        if not any(job.id == 'daily_question_job' for job in scheduler.get_jobs()):
            scheduler.add_job(
                func=lambda: print("执行每日一题任务"),  # 这里需要替换为实际的任务执行函数
                trigger='cron',
                hour=9,
                minute=0,
                id='daily_question_job'
            )
        
        # 每周一10:00执行每周一课
        if not any(job.id == 'weekly_lesson_job' for job in scheduler.get_jobs()):
            scheduler.add_job(
                func=lambda: print("执行每周一课任务"),  # 这里需要替换为实际的任务执行函数
                trigger='cron',
                day_of_week=0,  # 0表示周一
                hour=10,
                minute=0,
                id='weekly_lesson_job'
            )
        
        # 每月1号14:00执行每月一考
        if not any(job.id == 'monthly_exam_job' for job in scheduler.get_jobs()):
            scheduler.add_job(
                func=lambda: print("执行每月一考任务"),  # 这里需要替换为实际的任务执行函数
                trigger='cron',
                day=1,
                hour=14,
                minute=0,
                id='monthly_exam_job'
            )
        
        # 启动调度器
        scheduler.start()
    except Exception as e:
        print(f"初始化任务调度器失败: {e}")

def start_scheduler():
    """
    启动任务调度器
    """
    if not scheduler.running:
        scheduler.start()
        print("任务调度器已启动")

def stop_scheduler():
    """
    停止任务调度器
    """
    if scheduler.running:
        scheduler.shutdown()
        print("任务调度器已停止")
