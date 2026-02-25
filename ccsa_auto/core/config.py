import os
from datetime import timezone, timedelta


class Config:
    # 基础配置
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = "sqlite:///ccsa_auto.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 时区配置
    TIMEZONE = timezone(timedelta(hours=8))
    TIMEZONE_NAME = "Asia/Shanghai"

    # JWT配置
    JWT_SECRET_KEY = os.urandom(24)
    JWT_ACCESS_TOKEN_EXPIRES = 7200  # 2小时
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30天

    # 外部平台配置
    EXTERNAL_PLATFORM = {
        "LOGIN_URL": "https://edu.axdxa.cn/prod-api/auth/pwdLogin",
        "LOGIN_CLIENT_ID": "428a8310cd442757ae699df5d894f051",
        "LOGIN_GRANT_TYPE": "password",
        "BASE_URL": "https://edu.axdxa.cn/prod-api",
        "HEADERS": {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Content-Language": "zh_CN",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            "ClientId": "428a8310cd442757ae699df5d894f051",
        },
        "API_ENDPOINTS": {
            # 基础接口
            "GET_STUDY_LIST": "https://edu.axdxa.cn/prod-api/progress/app/regularStudy/getNewRegularStudyList",
            "SUBMIT_EXAM": "https://edu.axdxa.cn/prod-api/progress/app/regularExamRecord",
            "SUBMIT_STUDY_SCHEDULE": "https://edu.axdxa.cn/prod-api/progress/app/studyScheduleEscalation/studyScheduleEscalation",
            # 每日一题相关
            "GET_DAILY_QUESTIONS": "https://edu.axdxa.cn/prod-api/progress/app/regularStudyQuestionBank/getRegularStudyQuestionInfo",
            # 每周一课相关
            "GET_WEEKLY_LESSON": "https://edu.axdxa.cn/prod-api/progress/app/regularCourseWeek/{lesson_id}",
            "GET_VIDEO_URL": "https://edu.axdxa.cn/prod-api/platform-resource/app/resourceVideo/selectUrlByVodId",
            # 每月一考相关
            "GET_MONTHLY_QUESTIONS": "https://edu.axdxa.cn/prod-api/progress/app/regularStudyQuestionBank/getRegularStudyQuestionInfo",
            # 用户信息相关
            "GET_USER_INFO": "https://edu.axdxa.cn/prod-api/system/app/userExtend/v2/getUserInfo",
            "GET_SCORES": "https://edu.axdxa.cn/prod-api/progress/app/regularStudyRecord/getRegularFractionInfo",
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
    LOG_LEVEL = "INFO"
    LOG_DIR = "logs"
    LOG_RETENTION_DAYS = 60

    # 会话配置
    SESSION_TIMEOUT = 3600  # 1小时无活动过期（秒）
    SESSION_ABSOLUTE_TIMEOUT = 86400  # 24小时强制过期（秒）

    # 任务修复器配置
    TASK_FIXER_ENABLED = True  # 是否启用任务修复器
    TASK_FIXER_CRON = "0 2 * * *"  # 每天凌晨2点执行

    # 控分策略配置
    SCORE_STRATEGY_ENABLED = False  # 是否启用控分策略，False则全部满分
