import json

import requests
from refactored_code.logger import Logger
from refactored_code.config import Config

try:  # 避免包未安装时导入失败，登录时才真正需要
    from ccsa_auto.utils.crypto import encrypt_payload
except Exception:  # pragma: no cover
    encrypt_payload = None

class AuthModule:
    def __init__(self):
        self.session = requests.Session()
        self.logger = Logger("登录模块")
        self.access_token = None

    def _build_login_request(self):
        """构造登录请求的 body/headers（新版需要加密）。

        Returns:
            tuple: (body, headers)
        """
        headers = dict(Config.HEADERS)
        payload = dict(Config.LOGIN_DATA)

        if not getattr(Config, "LOGIN_ENCRYPT", False):
            return json.dumps(payload, ensure_ascii=False), headers

        if encrypt_payload is None:
            raise RuntimeError("缺少加密依赖 cryptography，无法加密登录请求")

        cipher_text, encrypt_key = encrypt_payload(payload)
        headers["encrypt-key"] = encrypt_key
        headers["isencrypt"] = "true"
        # 与前端 axios 行为一致：base64 密文作为 JSON 字符串发送（带引号）
        return json.dumps(cipher_text), headers

    def login(self, return_error_info=False):
        """
        登录并获取 access_token。
        
        Args:
            return_error_info: 如果为True，返回元组 (success, error_info)，其中error_info是包含详细错误信息的字典
                              如果为False，只返回success（布尔值），保持向后兼容
        
        Returns:
            如果return_error_info为False: bool (成功/失败)
            如果return_error_info为True: tuple (bool, dict) 其中dict包含错误信息
        """
        try:
            self.logger.info("正在尝试登录...")
            body, headers = self._build_login_request()
            response = self.session.post(
                Config.LOGIN_URL, data=body, headers=headers
            )
            response_json = response.json()
            if response_json.get("code") == 200 and "data" in response_json:
                self.access_token = response_json["data"].get("access_token")
                if self.access_token:
                    self.logger.info("登录成功！")
                    if return_error_info:
                        return True, None
                    else:
                        return True
                else:
                    self.logger.error("未能提取 access_token")
                    error_info = {
                        'code': response_json.get('code', 500),
                        'msg': '未能提取 access_token',
                        'data': response_json.get('data')
                    }
                    if return_error_info:
                        return False, error_info
                    else:
                        return False
            else:
                self.logger.error(f"登录失败: {response_json}")
                error_info = {
                    'code': response_json.get('code', 500),
                    'msg': response_json.get('msg', '登录失败'),
                    'data': response_json.get('data')
                }
                if return_error_info:
                    return False, error_info
                else:
                    return False
        except Exception as e:
            self.logger.error(f"登录时发生异常：{e}")
            error_info = {
                'code': 500,
                'msg': f'登录时发生异常：{str(e)}',
                'data': None
            }
            if return_error_info:
                return False, error_info
            else:
                return False

    def ensure_login(self):
        """
        确保登录状态有效。
        """
        if not self.access_token:
            self.logger.warning("会话失效，正在重新登录...")
            if not self.login():
                raise ValueError("重新登录失败")