class AuthState:
    """认证状态"""
    def __init__(self):
        self.token = None  # 本地JWT令牌
        self.external_token = None  # 外部平台访问令牌
        self.user_info = None
        self.is_authenticated = False
    
    def set_auth(self, token, user_info, external_token=None):
        """设置认证状态"""
        self.token = token
        self.user_info = user_info
        self.external_token = external_token
        self.is_authenticated = True
    
    def clear_auth(self):
        """清除认证状态"""
        self.token = None
        self.external_token = None
        self.user_info = None
        self.is_authenticated = False
    
    def is_admin(self):
        """检查是否为管理员"""
        return self.user_info and self.user_info.get('username') == 'admin'

# 全局认证状态
auth_state = AuthState()
