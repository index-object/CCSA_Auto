"""会话管理模块 - 管理多用户会话状态"""

import json
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from nicegui import ui
from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import User, AuthSession
from ccsa_auto.core.config import Config
from ccsa_auto.modules.auth.models import get_auth_state
from ccsa_auto.modules.auth.user_state import UserStateService


def migrate_auth_session_schema():
    """迁移 AuthSession 表结构，添加用户状态字段

    此函数检查并添加新字段，如果列不存在则添加
    """
    db = SessionLocal()
    try:
        from sqlalchemy import inspect, text

        inspector = inspect(db.bind)
        columns = [c["name"] for c in inspector.get_columns("auth_sessions")]

        new_columns = {
            "is_authenticated": "BOOLEAN DEFAULT 0",
            "is_admin": "BOOLEAN DEFAULT 0",
            "user_info_json": "TEXT",
            "access_token": "VARCHAR(500)",
            "external_token": "TEXT",
            "referrer_path": "VARCHAR(500)",
        }

        for col_name, col_def in new_columns.items():
            if col_name not in columns:
                try:
                    db.execute(
                        text(
                            f"ALTER TABLE auth_sessions ADD COLUMN {col_name} {col_def}"
                        )
                    )
                    print(f"已添加字段: auth_sessions.{col_name}")
                except Exception as e:
                    print(f"添加字段 {col_name} 失败（可能已存在）: {e}")

        db.commit()
        print("AuthSession 表结构迁移完成")
    except Exception as e:
        db.rollback()
        print(f"迁移 AuthSession 表结构失败: {e}")
    finally:
        db.close()


class SessionManager:
    """会话管理器

    管理用户会话状态，支持多用户并发访问
    每个浏览器会话有独立的认证状态
    """

    SESSION_DIR = "sessions"

    def __init__(self):
        if not os.path.exists(self.SESSION_DIR):
            os.makedirs(self.SESSION_DIR)

    def create_session(
        self,
        user_id: int,
        user_info: Dict[str, Any],
        access_token: str,
        external_token: Optional[str] = None,
    ) -> str:
        """创建新会话

        Args:
            user_id: 用户ID
            user_info: 用户信息
            access_token: 本地JWT令牌
            external_token: 外部平台令牌（可选）

        Returns:
            session_id: 会话ID
        """
        session_id = str(uuid.uuid4())

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "user_info": user_info,
            "access_token": access_token,
            "external_token": external_token,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }

        UserStateService.save_state(
            session_id,
            {
                "authenticated": True,
                "is_admin": False,
                "user_info": user_info,
                "access_token": access_token,
                "external_token": external_token,
                "user_id": user_id,
            },
        )

        auth_state = get_auth_state()
        auth_state.set_auth(access_token, user_info, external_token)

        try:
            ui.context.session_id = session_id
        except (AttributeError, TypeError):
            pass

        return session_id

    def create_db_session(
        self,
        user_id: int,
        access_token: str,
        user_info: Dict[str, Any] = None,
        is_admin: bool = False,
        external_token: str = None,
    ) -> Optional[str]:
        """创建数据库会话（新的服务器端会话管理）

        Args:
            user_id: 用户ID
            access_token: JWT令牌
            user_info: 用户信息字典
            is_admin: 是否管理员
            external_token: 外部平台令牌

        Returns:
            session_id: 会话ID，失败返回None
        """
        session_id = str(uuid.uuid4())
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()

        db = SessionLocal()
        try:
            auth_session = AuthSession(
                session_id=session_id,
                user_id=user_id,
                token_hash=token_hash,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                expires_at=datetime.utcnow()
                + timedelta(seconds=Config.SESSION_ABSOLUTE_TIMEOUT),
                is_active=True,
                is_authenticated=True,
                is_admin=is_admin,
                access_token=access_token,
                external_token=external_token,
            )

            if user_info:
                auth_session.set_user_info(user_info)

            db.add(auth_session)
            db.commit()

            # 设置当前请求的 session_id
            try:
                ui.context.session_id = session_id
            except (AttributeError, TypeError):
                pass

            return session_id
        except Exception as e:
            db.rollback()
            print(f"创建数据库会话失败: {e}")
            return None
        finally:
            db.close()

    def validate_session(
        self, session_id: str, access_token: str
    ) -> Optional[Dict[str, Any]]:
        """验证数据库会话是否有效

        Args:
            session_id: 会话ID
            access_token: JWT令牌

        Returns:
            dict: 会话信息，如果无效返回None
        """
        if not session_id:
            return None

        db = SessionLocal()
        try:
            session = (
                db.query(AuthSession)
                .filter_by(session_id=session_id, is_active=True)
                .first()
            )

            if not session:
                return None

            if session.is_expired():
                self.delete_session(session_id)
                return None

            token_hash = hashlib.sha256(access_token.encode()).hexdigest()
            if token_hash != session.token_hash:
                return None

            if session.is_inactive_expired(Config.SESSION_TIMEOUT):
                self.delete_session(session_id)
                return None

            return {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "expires_at": session.expires_at,
            }
        except Exception as e:
            print(f"验证会话失败: {e}")
            return None
        finally:
            db.close()

    def refresh_session(self, session_id: str) -> bool:
        """刷新会话的最后活动时间（滑动过期）

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功
        """
        if not session_id:
            return False

        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter_by(session_id=session_id).first()
            if session and session.is_active and not session.is_expired():
                session.last_activity = datetime.utcnow()
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"刷新会话失败: {e}")
            return False
        finally:
            db.close()

    def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功
        """
        if not session_id:
            return False

        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter_by(session_id=session_id).first()
            if session:
                db.delete(session)
                db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"删除会话失败: {e}")
            return False
        finally:
            db.close()

    def delete_user_sessions(self, user_id: int) -> int:
        """删除用户的所有会话

        Args:
            user_id: 用户ID

        Returns:
            int: 删除的会话数量
        """
        db = SessionLocal()
        try:
            sessions = db.query(AuthSession).filter_by(user_id=user_id).all()
            count = len(sessions)
            for session in sessions:
                db.delete(session)
            db.commit()
            return count
        except Exception as e:
            db.rollback()
            print(f"删除用户会话失败: {e}")
            return 0
        finally:
            db.close()

    def delete_all_sessions(self) -> int:
        """删除所有会话（用于重启应用时强制所有用户登出）

        Returns:
            int: 删除的会话数量
        """
        db = SessionLocal()
        try:
            sessions = db.query(AuthSession).all()
            count = len(sessions)
            for session in sessions:
                db.delete(session)
            db.commit()
            return count
        except Exception as e:
            db.rollback()
            print(f"删除所有会话失败: {e}")
            return 0
        finally:
            db.close()

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话

        Returns:
            int: 清理的会话数量
        """
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            expired_sessions = (
                db.query(AuthSession).filter(AuthSession.expires_at < now).all()
            )
            count = len(expired_sessions)
            for session in expired_sessions:
                db.delete(session)
            db.commit()
            print(f"已清理 {count} 个过期会话")
            return count
        except Exception as e:
            db.rollback()
            print(f"清理过期会话失败: {e}")
            return 0
        finally:
            db.close()

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
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                os.remove(session_file)
                return False

            session_data["last_accessed"] = datetime.utcnow().isoformat()
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            auth_state = get_auth_state()
            auth_state.set_auth(
                session_data["access_token"],
                session_data["user_info"],
                session_data.get("external_token"),
            )

            try:
                ui.context.session_id = session_id
            except (AttributeError, TypeError):
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
            return getattr(ui.context, "session_id", None)
        except (AttributeError, TypeError):
            return None

    def get_current_user_id(self) -> Optional[int]:
        """获取当前用户ID

        Returns:
            int: 用户ID，如果没有则返回None
        """
        auth_state = get_auth_state()
        if auth_state.user_info:
            return auth_state.user_info.get("id")
        return None

    def destroy_session(self, session_id: Optional[str] = None):
        """销毁会话

        Args:
            session_id: 会话ID，如果为None则销毁当前会话
        """
        if session_id is None:
            session_id = self.get_current_session_id()

        if session_id:
            UserStateService.clear_state(session_id)
            self.delete_session(session_id)

        auth_state = get_auth_state()
        auth_state.clear_auth()

        try:
            if hasattr(ui.context, "session_id"):
                delattr(ui.context, "session_id")
        except (AttributeError, TypeError):
            pass


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
