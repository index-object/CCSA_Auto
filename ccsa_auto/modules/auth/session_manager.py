"""会话管理模块 - 管理多用户会话状态"""
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from nicegui import ui
from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import User
from ccsa_auto.modules.auth.models import get_auth_state


class SessionManager:
    """会话管理器
    
    管理用户会话状态，支持多用户并发访问
    每个浏览器会话有独立的认证状态
    """
    
    # 会话存储目录
    SESSION_DIR = 'sessions'
    
    def __init__(self):
        """初始化会话管理器"""
        # 确保会话目录存在
        if not os.path.exists(self.SESSION_DIR):
            os.makedirs(self.SESSION_DIR)
    
    def create_session(self, user_id: int, user_info: Dict[str, Any], 
                      access_token: str, external_token: Optional[str] = None) -> str:
        """创建新会话
        
        Args:
            user_id: 用户ID
            user_info: 用户信息
            access_token: 本地JWT令牌
            external_token: 外部平台令牌（可选）
            
        Returns:
            session_id: 会话ID
        """
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 创建会话数据
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'user_info': user_info,
            'access_token': access_token,
            'external_token': external_token,
            'created_at': datetime.utcnow().isoformat(),
            'last_accessed': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        # 保存会话到文件（可选持久化）
        session_file = os.path.join(self.SESSION_DIR, f"{session_id}.json")
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        # 设置当前会话的认证状态
        auth_state = get_auth_state()
        auth_state.set_auth(access_token, user_info, external_token)
        
        # 在会话上下文中存储会话ID
        try:
            ui.context.session_id = session_id
        except (AttributeError, TypeError):
            # 如果ui.context不支持属性设置，忽略错误
            pass
        
        return session_id
    
    def load_session(self, session_id: str) -> bool:
        """加载会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功加载
        """
        session_file = os.path.join(self.SESSION_DIR, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            return False
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # 检查会话是否过期
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.utcnow() > expires_at:
                # 会话已过期，删除文件
                os.remove(session_file)
                return False
            
            # 更新最后访问时间
            session_data['last_accessed'] = datetime.utcnow().isoformat()
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            # 设置当前会话的认证状态
            auth_state = get_auth_state()
            auth_state.set_auth(
                session_data['access_token'],
                session_data['user_info'],
                session_data.get('external_token')
            )
            
            # 在会话上下文中存储会话ID
            try:
                ui.context.session_id = session_id
            except (AttributeError, TypeError):
                # 如果ui.context不支持属性设置，忽略错误
                pass
            
            return True
            
        except Exception as e:
            print(f"加载会话失败: {e}")
            return False
    
    def get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID
        
        Returns:
            str: 会话ID，如果没有则返回None
        """
        try:
            return getattr(ui.context, 'session_id', None)
        except (AttributeError, TypeError):
            return None
    
    def get_current_user_id(self) -> Optional[int]:
        """获取当前用户ID
        
        Returns:
            int: 用户ID，如果没有则返回None
        """
        auth_state = get_auth_state()
        if auth_state.user_info:
            return auth_state.user_info.get('id')
        return None
    
    def destroy_session(self, session_id: Optional[str] = None):
        """销毁会话
        
        Args:
            session_id: 会话ID，如果为None则销毁当前会话
        """
        if session_id is None:
            session_id = self.get_current_session_id()
        
        if session_id:
            # 删除会话文件
            session_file = os.path.join(self.SESSION_DIR, f"{session_id}.json")
            if os.path.exists(session_file):
                try:
                    os.remove(session_file)
                except Exception as e:
                    print(f"删除会话文件失败: {e}")
        
        # 清除当前会话的认证状态
        auth_state = get_auth_state()
        auth_state.clear_auth()
        
        # 清除会话上下文中的会话ID
        try:
            # 尝试删除session_id属性
            if hasattr(ui.context, 'session_id'):
                delattr(ui.context, 'session_id')
        except (AttributeError, TypeError):
            # 如果ui.context不支持删除操作，忽略错误
            pass
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        if not os.path.exists(self.SESSION_DIR):
            return
        
        current_time = datetime.utcnow()
        for filename in os.listdir(self.SESSION_DIR):
            if filename.endswith('.json'):
                session_file = os.path.join(self.SESSION_DIR, filename)
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    expires_at = datetime.fromisoformat(session_data['expires_at'])
                    if current_time > expires_at:
                        os.remove(session_file)
                        print(f"已清理过期会话: {filename}")
                        
                except Exception as e:
                    print(f"清理会话文件失败 {filename}: {e}")


# 全局会话管理器实例
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    return session_manager


def require_auth():
    """认证装饰器：要求用户已登录
    
    使用示例：
        @require_auth()
        def some_function():
            # 只有已登录用户才能执行
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            auth_state = get_auth_state()
            if not auth_state.is_authenticated:
                # 重定向到登录页面或返回错误
                raise PermissionError("需要登录才能访问此功能")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user() -> Optional[User]:
    """获取当前用户对象
    
    Returns:
        User: 当前用户对象，如果未登录则返回None
    """
    user_id = session_manager.get_current_user_id()
    if not user_id:
        return None
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        return user
    finally:
        db.close()