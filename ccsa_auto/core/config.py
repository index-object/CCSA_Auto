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
        'HEADERS': {
            "Content-Type": "application/json"
        },
        'API_ENDPOINTS': {
            'DAILY_URL': "https://edu.axdxa.cn/prod-api/daily/question",
            'WEEKLY_URL': "https://edu.axdxa.cn/prod-api/weekly/lesson",
            'MONTHLY_URL': "https://edu.axdxa.cn/prod-api/monthly/exam"
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
