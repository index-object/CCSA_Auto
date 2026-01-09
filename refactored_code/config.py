class Config:
    # 基础配置
    BASE_URL = "https://edu.axdxa.cn/prod-api"
    CLIENT_ID = "e5cd7e4891bf95d1d19206ce24a7b32e"
    
    # 登录配置
    LOGIN_URL = f"{BASE_URL}/auth/pwdLogin"
    LOGIN_DATA = {
        "username": "18700240518",  # 替换为实际用户名
        "password": "hwwa240518",  # 替换为实际密码
        "clientId": "428a8310cd442757ae699df5d894f051",
        "grantType": "password"
    }
    HEADERS = {
        "Content-Type": "application/json"
    }

    # 功能接口配置
    DAILY_URL = f"{BASE_URL}/daily/question"
    WEEKLY_URL = f"{BASE_URL}/weekly/lesson"
    MONTHLY_URL = f"{BASE_URL}/monthly/exam"