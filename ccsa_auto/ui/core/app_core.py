"""应用核心模块 - 包含应用的核心逻辑（导航、状态管理、会话管理）"""
import json
import os
from ccsa_auto.modules.auth.models import auth_state


# 全局变量
current_page = 'login'
page_container = None


def load_login_state():
    """加载登录状态"""
    if os.path.exists('session.json'):
        try:
            with open('session.json', 'r') as f:
                session_data = json.load(f)
                auth_state.set_auth(
                    session_data.get('token'),
                    session_data.get('user_info'),
                    session_data.get('external_token')
                )
                return session_data.get('current_page', 'login')
        except Exception as e:
            print(f"加载会话失败: {e}")
            return 'login'
    return 'login'


def save_login_state(page):
    """保存登录状态"""
    with open('session.json', 'w') as f:
        json.dump({
            'token': auth_state.token,
            'external_token': auth_state.external_token,
            'user_info': auth_state.user_info,
            'current_page': page
        }, f)


def logout():
    """退出登录"""
    auth_state.clear_auth()
    
    # 清除会话文件
    if os.path.exists('session.json'):
        try:
            os.remove('session.json')
        except Exception as e:
            print(f"清除会话失败: {e}")
    
    # 导航到登录页面
    return 'login'