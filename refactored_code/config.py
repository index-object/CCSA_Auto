class Config:
    # 基础配置
    BASE_URL = "https://edu.axdxa.cn/prod-api"
    CLIENT_ID = "e5cd7e4891bf95d1d19206ce24a7b32e"
    
    # 登录配置（v2 接口：auth-v2/pwdLogin，请求体加密，isencrypt/encrypt-key）
    LOGIN_URL = f"{BASE_URL}/auth-v2/pwdLogin"
    # 新版登录要求加密请求体（isencrypt / encrypt-key）
    LOGIN_ENCRYPT = True
    LOGIN_DATA = {
        "username": "18700240518",  # 替换为实际用户名
        "password": "hwwa240518",  # 替换为实际密码
        "clientId": CLIENT_ID,
        "grantType": "password"
    }
    # 业务公共请求头（登录后的接口复用）
    HEADERS = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Content-Language": "zh_CN",
        "ClientId": CLIENT_ID,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0"
        ),
    }

    # 功能接口配置
    DAILY_URL = f"{BASE_URL}/daily/question"
    WEEKLY_URL = f"{BASE_URL}/weekly/lesson"
    MONTHLY_URL = f"{BASE_URL}/monthly/exam"