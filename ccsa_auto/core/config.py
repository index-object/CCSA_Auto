import os
from datetime import timezone, timedelta

# 项目根目录（本文件位于 <root>/ccsa_auto/core/config.py）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Config:
    # 基础配置
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = "sqlite:///ccsa_auto.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # NiceGUI 热重载：默认关闭。开启后会派生子进程，父子进程都会导入应用代码
    # （重复初始化调度器、重复打开日志文件），生产环境请保持关闭。
    APP_RELOAD = os.getenv("CCSA_RELOAD", "0") == "1"

    # 时区配置
    TIMEZONE = timezone(timedelta(hours=8))
    TIMEZONE_NAME = "Asia/Shanghai"

    # JWT配置
    JWT_SECRET_KEY = os.urandom(24)
    JWT_ACCESS_TOKEN_EXPIRES = 7200  # 2小时
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30天

    # 外部平台配置（2026-09 平台升级为 v2 接口）
    EXTERNAL_PLATFORM = {
        "LOGIN_URL": "https://edu.axdxa.cn/prod-api/auth-v2/pwdLogin",
        "LOGIN_CLIENT_ID": "e5cd7e4891bf95d1d19206ce24a7b32e",
        "LOGIN_GRANT_TYPE": "password",
        "BASE_URL": "https://edu.axdxa.cn/prod-api",
        "HEADERS": {
            "content-type": "application/json;charset=UTF-8",
            "accept": "application/json, text/plain, */*",
            "content-language": "zh_CN",
            "clientid": "e5cd7e4891bf95d1d19206ce24a7b32e",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0",
        },
        "API_ENDPOINTS": {
            # 三个一状态（每日/每周/每月，v2 起拆分为独立接口）
            "GET_REGULAR_STUDY_DAY": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularStudy/getRegularStudyDay",
            "GET_REGULAR_STUDY_WEEK": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularStudy/getRegularStudyWeek",
            "GET_REGULAR_STUDY_MONTH": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularStudy/getRegularStudyMonth",
            # 交卷（每日/每月通用）
            "SUBMIT_EXAM": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularExamRecord",
            # 每日/每月试题（返回 questionAnswera 标准答案）
            "GET_DAILY_QUESTIONS": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularStudyQuestionBank/getRegularStudyQuestionInfo",
            "GET_MONTHLY_QUESTIONS": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularStudyQuestionBank/getRegularStudyQuestionInfo",
            # 每周一课
            "GET_WEEKLY_LESSON": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularCourseWeek/{lesson_id}",
            "GET_VIDEO_URL": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularCourseWeek/courseWeekPlayAuth/{lesson_id}",
            "SUBMIT_STUDY_SCHEDULE": "https://edu.axdxa.cn/prod-api/platform-resource-v2/app/weeklyCourse/progressReporter",
            # 用户信息相关
            "GET_USER_INFO": "https://edu.axdxa.cn/prod-api/system-v2/app/userExtend/v2/getUserInfo",
            "GET_SCORES": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularStudyRecord/getRegularFractionInfo",
            # 答题记录查询（只读，用于采集答案库）
            "GET_EXAM_RECORDS": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularExamRecord/list",
            "GET_EXAM_DETAIL": "https://edu.axdxa.cn/prod-api/progress-v2/app/regularExamRecord/getRegularStudyExamInfo",
        },
    }

    # 任务配置
    TASK_SCHEDULE = {
        "DAILY": "0 7-11 * * *",  # 每天7点~11点之间随机时间
        "WEEKLY": "0 8-11 * * 2",  # 每周二8点~11点之间随机时间
        "MONTHLY": "0 9-15 15 * *",  # 每月15日9点~15点之间随机时间
    }

    # 任务详细配置（用于计算next_run_time）
    TASK_DETAILS = {
        "DAILY": {
            "name": "每日一题",
            "description": "每天自动完成每日一题",
            "hour_range": (7, 11),  # 执行小时范围：7~11点
            "minute_range": (0, 59),  # 执行分钟范围：0~59分
        },
        "WEEKLY": {
            "name": "每周一课",
            "description": "每周自动完成每周一课",
            "weekday": 2,  # 周二 (0=周一, 1=周二, ..., 6=周日)
            "hour_range": (8, 11),  # 执行小时范围：8~11点
            "minute_range": (0, 59),  # 执行分钟范围：0~59分
        },
        "MONTHLY": {
            "name": "每月一考",
            "description": "每月自动完成每月一考",
            "day": 15,  # 每月15日
            "hour_range": (9, 15),  # 执行小时范围：9~15点
            "minute_range": (0, 59),  # 执行分钟范围：0~59分
        },
    }

    # 日志配置
    LOG_LEVEL = os.getenv("CCSA_LOG_LEVEL", "INFO")
    LOG_DIR = os.getenv("CCSA_LOG_DIR") or os.path.join(BASE_DIR, "logs")
    LOG_RETENTION_DAYS = 60
    # 每天 00:00 轮转；轮转后的文件压缩为 zip
    LOG_ROTATION = "00:00"
    LOG_COMPRESSION = "zip"
    # 单个记录超过该长度时在控制台/上下文里截断（文件仍写完整消息）
    LOG_CONTEXT_VALUE_MAX_LEN = 120
    # 是否把日志同时输出到控制台（部署时 stdout/stderr 会被重定向到 logs/console）
    LOG_CONSOLE = os.getenv("CCSA_LOG_CONSOLE", "1") == "1"
    # enqueue=True 会使用进程内队列 + 后台线程；fork 出的子进程会共享该队列，
    # 因此默认关闭。需要异步写入时可自行打开。
    LOG_ENQUEUE = os.getenv("CCSA_LOG_ENQUEUE", "0") == "1"
    # 客户访问日志（文件 + 数据库）
    LOG_ACCESS_ENABLED = os.getenv("CCSA_LOG_ACCESS", "1") == "1"
    LOG_ACCESS_DB_ENABLED = os.getenv("CCSA_LOG_ACCESS_DB", "1") == "1"
    # 精确任务运行记录（task_run_logs 表）保留天数
    LOG_TASK_RUN_RETENTION_DAYS = 90
    # 每天归档时间（把前一天各进程日志合并到 logs/archive/YYYY-MM-DD/）
    LOG_ARCHIVE_HOUR = 0
    LOG_ARCHIVE_MINUTE = 5

    # 会话配置
    SESSION_TIMEOUT = 3600  # 1小时无活动过期（秒）
    SESSION_ABSOLUTE_TIMEOUT = 86400  # 24小时强制过期（秒）

    # 任务修复器配置
    TASK_FIXER_ENABLED = True  # 是否启用任务修复器
    TASK_FIXER_CRON = "0 2 * * *"  # 每天凌晨2点执行

# 控分策略配置
    SCORE_STRATEGY_ENABLED = False  # 是否启用控分策略，False则全部满分
    SCORE_TARGET = 650  # 目标分数
    SCORE_THRESHOLD = 20  # 接近阈值
    SCORE_RANDOM_MIN = 0.30  # 随机分数下限
    SCORE_RANDOM_MAX = 1.00  # 随机分数上限
