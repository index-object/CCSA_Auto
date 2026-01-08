import requests
from refactored_code.logger import Logger
from refactored_code.config import Config

class AuthModule:
    def __init__(self):
        self.session = requests.Session()
        self.logger = Logger("登录模块")
        self.access_token = None

    def login(self):
        """
        登录并获取 access_token。
        """
        try:
            self.logger.info("正在尝试登录...")
            response = self.session.post(Config.LOGIN_URL, json=Config.LOGIN_DATA, headers=Config.HEADERS)
            response_json = response.json()
            if response_json.get("code") == 200 and "data" in response_json:
                self.access_token = response_json["data"].get("access_token")
                if self.access_token:
                    self.logger.info("登录成功！")
                    return True
                else:
                    self.logger.error("未能提取 access_token")
                    return False
            else:
                self.logger.error(f"登录失败: {response_json}")
                return False
        except Exception as e:
            self.logger.error(f"登录时发生异常：{e}")
            return False

    def ensure_login(self):
        """
        确保登录状态有效。
        """
        if not self.access_token:
            self.logger.warning("会话失效，正在重新登录...")
            if not self.login():
                raise ValueError("重新登录失败")