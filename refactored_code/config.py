class Config:
    # 登录配置
    LOGIN_URL = "https://edu.axdxa.cn/prod-api/auth/pwdLogin"
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
    DAILY_URL = "https://edu.axdxa.cn/prod-api/daily/question"
    WEEKLY_URL = "https://edu.axdxa.cn/prod-api/weekly/lesson"
    MONTHLY_URL = "https://edu.axdxa.cn/prod-api/monthly/exam"