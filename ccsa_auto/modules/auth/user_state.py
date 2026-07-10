import json
from typing import Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import AuthSession
from ccsa_auto.core.config import Config


class UserStateService:
    """用户状态服务 - 替代 app.storage.user

    将用户状态存储到数据库的 AuthSession 表中，
    避免使用 NiceGUI 的文件系统存储，解决文件锁定问题。
    """

    @staticmethod
    def save_state(session_id: str, state: Dict[str, Any]) -> bool:
        """保存用户状态到数据库

        Args:
            session_id: 会话ID
            state: 用户状态字典

        Returns:
            bool: 是否保存成功
        """
        if not session_id:
            return False

        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter_by(session_id=session_id).first()
            if not session:
                return False

            session.is_authenticated = state.get("authenticated", False)
            session.is_admin = state.get("is_admin", False)
            session.access_token = state.get("access_token")
            session.external_token = state.get("external_token")
            session.user_id = state.get("user_id")

            user_info = state.get("user_info")
            if user_info:
                session.user_info_json = json.dumps(user_info, ensure_ascii=False)

            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"保存用户状态失败: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def get_state(session_id: str) -> Optional[Dict[str, Any]]:
        """从数据库获取用户状态

        Args:
            session_id: 会话ID

        Returns:
            dict: 用户状态字典，如果没有找到返回 None
        """
        if not session_id:
            return None

        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter_by(session_id=session_id).first()
            if not session:
                return None

            state = {
                "authenticated": session.is_authenticated,
                "is_admin": session.is_admin,
                "access_token": session.access_token,
                "external_token": session.external_token,
                "user_id": session.user_id,
                "session_id": session.session_id,
            }

            if session.user_info_json:
                try:
                    state["user_info"] = json.loads(session.user_info_json)
                except json.JSONDecodeError:
                    state["user_info"] = {}
            else:
                state["user_info"] = {}

            return state
        except SQLAlchemyError as e:
            print(f"获取用户状态失败: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def clear_state(session_id: str) -> bool:
        """清除用户状态（保留数据库会话记录）

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否清除成功
        """
        if not session_id:
            return False

        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter_by(session_id=session_id).first()
            if not session:
                return False

            session.is_authenticated = False
            session.is_admin = False
            session.user_info_json = None
            session.access_token = None
            session.external_token = None

            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"清除用户状态失败: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def update_external_token(session_id: str, token: str) -> bool:
        """更新外部令牌

        Args:
            session_id: 会话ID
            token: 新的外部令牌

        Returns:
            bool: 是否更新成功
        """
        if not session_id:
            return False

        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter_by(session_id=session_id).first()
            if not session:
                return False

            session.external_token = token
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"更新外部令牌失败: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def get_referrer_path(session_id: str) -> Optional[str]:
        """获取referrer路径

        Args:
            session_id: 会话ID

        Returns:
            str: referrer路径，如果没有返回 None
        """
        if not session_id:
            return None

        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter_by(session_id=session_id).first()
            return session.referrer_path if session else None
        except SQLAlchemyError as e:
            print(f"获取referrer路径失败: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def set_referrer_path(session_id: str, path: str) -> bool:
        """设置referrer路径

        Args:
            session_id: 会话ID
            path: referrer路径

        Returns:
            bool: 是否设置成功
        """
        if not session_id:
            return False

        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter_by(session_id=session_id).first()
            if not session:
                return False

            session.referrer_path = path
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"设置referrer路径失败: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def set_authenticated(session_id: str, authenticated: bool = True) -> bool:
        """设置认证状态

        Args:
            session_id: 会话ID
            authenticated: 是否认证

        Returns:
            bool: 是否设置成功
        """
        if not session_id:
            return False

        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter_by(session_id=session_id).first()
            if not session:
                return False

            session.is_authenticated = authenticated
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"设置认证状态失败: {e}")
            return False
        finally:
            db.close()
