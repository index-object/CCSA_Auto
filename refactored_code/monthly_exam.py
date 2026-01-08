from refactored_code.auth_module import AuthModule
from refactored_code.logger import Logger
from refactored_code.config import Config

class MonthlyExam:
    def __init__(self, auth: AuthModule):
        self.auth = auth
        self.logger = Logger("每月一考模块")

    def submit_exam(self, exam_data):
        """
        提交每月一考答案。

        Args:
            exam_data (dict): 动态考试参数。

        Returns:
            bool: 成功返回 True，失败返回 False。
        """
        self.auth.ensure_login()
        try:
            self.logger.info("正在提交每月一考答案...")
            response = self.auth.session.post(Config.MONTHLY_URL, json=exam_data, headers={
                "Authorization": f"Bearer {self.auth.access_token}"
            })
            response_json = response.json()
            if response_json.get("code") == 200:
                self.logger.info("每月一考提交成功！")
                return True
            elif response_json.get("code") == 401:
                self.logger.warning("认证失败，正在重新登录...")
                self.auth.login()
                return self.submit_exam(exam_data)  # 重新调用接口
            else:
                self.logger.error(f"每月一考提交失败，返回信息：{response_json}")
                return False
        except Exception as e:
            self.logger.error(f"提交每月一考时发生异常：{e}")
            return False