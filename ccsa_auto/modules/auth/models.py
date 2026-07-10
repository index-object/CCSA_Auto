from nicegui import ui

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

def get_auth_state():
    """获取当前会话的认证状态
    
    使用NiceGUI的ui.context来存储每个客户端会话的认证状态
    如果当前会话没有认证状态，则创建一个新的AuthState实例
    """
    # 尝试从当前会话获取认证状态
    try:
        # 尝试使用getattr获取auth_state
        if hasattr(ui.context, 'auth_state'):
            auth_state = ui.context.auth_state
            if auth_state is None:
                # 如果当前会话没有认证状态，创建一个新的
                auth_state = AuthState()
                ui.context.auth_state = auth_state
            return auth_state
        else:
            # 如果auth_state属性不存在，创建一个新的
            auth_state = AuthState()
            ui.context.auth_state = auth_state
            return auth_state
    except Exception:
        # 如果出现任何错误，返回一个新的AuthState实例
        # 注意：在没有ui.context的环境中，这可能会失败
        # 在这种情况下，我们返回一个全局的AuthState作为后备
        return AuthState()

# 向后兼容：保持auth_state变量，但改为函数调用
# 注意：现有代码使用auth_state作为对象，需要修改为函数调用
# 为了最小化修改，我们创建一个代理对象
class AuthStateProxy:
    """认证状态代理，提供向后兼容的接口"""
    
    @property
    def token(self):
        return get_auth_state().token
    
    @property
    def external_token(self):
        return get_auth_state().external_token
    
    @property
    def user_info(self):
        return get_auth_state().user_info
    
    @property
    def is_authenticated(self):
        return get_auth_state().is_authenticated
    
    def set_auth(self, token, user_info, external_token=None):
        """设置认证状态"""
        get_auth_state().set_auth(token, user_info, external_token)
    
    def clear_auth(self):
        """清除认证状态"""
        get_auth_state().clear_auth()
    
    def is_admin(self):
        """检查是否为管理员"""
        return get_auth_state().is_admin()

# 创建代理实例，保持向后兼容
auth_state = AuthStateProxy()
