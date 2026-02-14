import logging
from typing import Dict, Any, List, Optional
from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import User, Task
from ccsa_auto.utils.timezone import format_datetime_for_display

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def get_users(
        keyword: str = None, status: int = None, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            query = db.query(User)

            if keyword:
                query = query.filter(
                    (User.username.contains(keyword))
                    | (User.name.contains(keyword))
                    | (User.company_name.contains(keyword))
                )

            if status is not None:
                query = query.filter_by(status=status)

            total = query.count()
            users = (
                query.order_by(User.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            user_list = []
            for user in users:
                user_dict = {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "external_username": user.external_username,
                    "company_name": user.company_name,
                    "status": user.status,
                    "is_admin": user.is_admin,
                    "created_at": format_datetime_for_display(user.created_at),
                }
                user_list.append(user_dict)

            return {
                "success": True,
                "data": user_list,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.exception("Failed to get users")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def get_user_detail(user_id: int) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return {"success": False, "message": "User not found"}

            total_tasks = db.query(Task).filter_by(user_id=user_id).count()
            completed_tasks = (
                db.query(Task)
                .filter_by(user_id=user_id, execution_status="completed")
                .count()
            )
            failed_tasks = (
                db.query(Task)
                .filter_by(user_id=user_id, execution_status="failed")
                .count()
            )

            user_detail = {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "external_username": user.external_username,
                "company_name": user.company_name,
                "status": user.status,
                "is_admin": user.is_admin,
                "external_token": user.external_token[:20] + "..."
                if user.external_token
                else None,
                "token_expires_at": format_datetime_for_display(user.token_expires_at)
                if user.token_expires_at
                else None,
                "created_at": format_datetime_for_display(user.created_at),
                "task_stats": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "failed": failed_tasks,
                },
            }

            return {"success": True, "data": user_detail}
        except Exception as e:
            logger.exception("Failed to get user detail")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def update_user(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return {"success": False, "message": "User not found"}

            if "name" in data:
                user.name = data["name"]
            if "company_name" in data:
                user.company_name = data["company_name"]
            if "external_username" in data:
                user.external_username = data["external_username"]
            if "external_password" in data:
                user.external_password = data["external_password"]

            db.commit()
            return {"success": True, "message": "User updated successfully"}
        except Exception as e:
            db.rollback()
            logger.exception("Failed to update user")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def delete_user(user_id: int) -> Dict[str, Any]:
        from ccsa_auto.modules.admin.service import AdminService

        return AdminService.delete_user(user_id)

    @staticmethod
    def batch_update_status(user_ids: List[int], status: int) -> Dict[str, Any]:
        from ccsa_auto.modules.admin.service import AdminService

        return AdminService.batch_update_user_status(user_ids, status)
