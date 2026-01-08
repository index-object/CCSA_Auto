from refactored_code.auth_module import AuthModule
from refactored_code.logger import Logger
from refactored_code.config import Config

class WeeklyLesson:
    def __init__(self, auth: AuthModule):
        self.auth = auth
        self.logger = Logger("每周一课模块")

    def fetch_lesson(self):
        """
        获取每周一课内容。

        Returns:
            bool: 成功返回 True，失败返回 False。
        """
        self.auth.ensure_login()
        try:
            self.logger.info("正在获取每周一课内容...")
            response = self.auth.session.get(Config.WEEKLY_URL, headers={
                "Authorization": f"Bearer {self.auth.access_token}"
            })
            response_json = response.json()
            if response_json.get("code") == 200:
                self.logger.info("每周一课内容获取成功！")
                return True
            elif response_json.get("code") == 401:
                self.logger.warning("认证失败，正在重新登录...")
                self.auth.login()
                return self.fetch_lesson()  # 重新调用接口
            else:
                self.logger.error(f"每周一课内容获取失败，返回信息：{response_json}")
                return False
        except Exception as e:
            self.logger.error(f"获取每周一课内容时发生异常：{e}")
            return False