import os

class Config:
    # 基础配置
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ccsa_auto.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.urandom(24)
    JWT_ACCESS_TOKEN_EXPIRES = 7200  # 2小时
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30天
    
    # 外部平台配置
    EXTERNAL_PLATFORM = {
        'LOGIN_URL': "https://edu.axdxa.cn/prod-api/auth/pwdLogin",
        'LOGIN_CLIENT_ID': "428a8310cd442757ae699df5d894f051",
        'LOGIN_GRANT_TYPE': "password",
        'BASE_URL': "https://edu.axdxa.cn/prod-api",
        'HEADERS': {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Content-Language": "zh_CN",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            "ClientId": "428a8310cd442757ae699df5d894f051"
        },
        'API_ENDPOINTS': {
            # 基础接口
            'GET_STUDY_LIST': "https://edu.axdxa.cn/prod-api/progress/app/regularStudy/getNewRegularStudyList",
            'SUBMIT_EXAM': "https://edu.axdxa.cn/prod-api/progress/app/regularExamRecord",
            'SUBMIT_STUDY_SCHEDULE': "https://edu.axdxa.cn/prod-api/progress/app/studyScheduleEscalation/studyScheduleEscalation",
            
            # 每日一题相关
            'GET_DAILY_QUESTIONS': "https://edu.axdxa.cn/prod-api/progress/app/regularStudyQuestionBank/getRegularStudyQuestionInfo",
            
            # 每周一课相关
            'GET_WEEKLY_LESSON': "https://edu.axdxa.cn/prod-api/progress/app/regularCourseWeek/{lesson_id}",
            
            # 每月一考相关
            'GET_MONTHLY_QUESTIONS': "https://edu.axdxa.cn/prod-api/progress/app/regularStudyQuestionBank/getRegularStudyQuestionInfo",
            
            # 用户信息相关
            'GET_USER_INFO': "https://edu.axdxa.cn/prod-api/system/app/userExtend/v2/getUserInfo",
            'GET_SCORES': "https://edu.axdxa.cn/prod-api/progress/app/regularStudyRecord/getRegularFractionInfo"
        }
    }
    
    # 任务配置
    TASK_SCHEDULE = {
        'DAILY': '0 0 * * *',  # 每天0点
        'WEEKLY': '0 0 * * 0',  # 每周日0点
        'MONTHLY': '0 0 1 * *'  # 每月1日0点
    }
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
