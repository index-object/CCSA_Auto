"""应用核心模块 - 包含应用的核心逻辑（导航、状态管理、会话管理）"""
import json
import os
from ccsa_auto.modules.auth.models import auth_state
from ccsa_auto.modules.auth.session_manager import get_session_manager


# 全局变量
current_page = 'login'
page_container = None


def load_login_state():
    """加载登录状态
    
    在新的会话管理系统中，每个会话独立存储状态
    检查当前会话是否已认证，返回相应的页面
    """
    # 尝试从会话管理器恢复会话
    session_manager = get_session_manager()
    session_id = session_manager.get_current_session_id()
    
    if session_id:
        # 尝试加载会话
        if session_manager.load_session(session_id):
            print(f"已从会话ID恢复会话: {session_id}")
    
    # 检查当前用户是否已认证
    if auth_state.is_authenticated:
        return 'main'
    else:
        return 'login'


def save_login_state(page):
    """保存登录状态
    
    在新的会话管理系统中，每个会话独立存储状态
    页面状态由应用内部管理，不需要持久化到全局文件
    """
    # 不再保存到全局文件，页面状态由应用内部管理
    pass


def logout():
    """退出登录"""
    # 获取会话管理器
    session_manager = get_session_manager()
    
    # 销毁当前会话
    session_manager.destroy_session()
    
    # 导航到登录页面
    return 'login'


def get_current_user_id():
    """获取当前用户ID"""
    session_manager = get_session_manager()
    return session_manager.get_current_user_id()


def is_authenticated():
    """检查当前用户是否已认证"""
    return auth_state.is_authenticated


def require_auth_redirect(navigate_to):
    """要求认证的重定向装饰器
    
    如果用户未登录，重定向到登录页面
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                navigate_to('login')
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator