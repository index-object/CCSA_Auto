import logging
from typing import Dict, Any, List, Optional

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Task, User
from ccsa_auto.utils.timezone import format_datetime_for_display
from ccsa_auto.modules.task.service import TaskService as BaseTaskService
from ccsa_auto.modules.task.scheduler import (
    add_task_to_scheduler,
    remove_task_from_scheduler,
)

logger = logging.getLogger(__name__)


class TaskManagementService:
    """Task management service for admin_v2"""

    @staticmethod
    def get_tasks(
        keyword: str = None,
        user_id: int = None,
        task_type: str = None,
        is_active: bool = None,
        execution_status: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get task list with filters"""
        db = SessionLocal()
        try:
            query = db.query(Task)

            if keyword:
                query = query.filter(Task.task_name.contains(keyword))

            if user_id is not None:
                query = query.filter_by(user_id=user_id)

            if task_type:
                query = query.filter_by(task_type=task_type)

            if is_active is not None:
                query = query.filter_by(is_active=is_active)

            if execution_status:
                query = query.filter_by(execution_status=execution_status)

            total = query.count()
            tasks = (
                query.order_by(Task.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            task_list = []
            for task in tasks:
                user = db.query(User).filter_by(id=task.user_id).first()
                task_dict = {
                    "id": task.id,
                    "user_id": task.user_id,
                    "username": user.username if user else "Unknown",
                    "task_type": task.task_type,
                    "task_name": task.task_name,
                    "description": task.description,
                    "is_active": task.is_active,
                    "execution_status": task.execution_status,
                    "external_status": task.external_status,
                    "next_run_time": format_datetime_for_display(task.next_run_time)
                    if task.next_run_time
                    else None,
                    "created_at": format_datetime_for_display(task.created_at),
                }
                task_list.append(task_dict)

            return {
                "success": True,
                "data": task_list,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.exception("Failed to get tasks")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def get_task_detail(task_id: int) -> Dict[str, Any]:
        """Get task detail with execution history"""
        db = SessionLocal()
        try:
            task = db.query(Task).filter_by(id=task_id).first()
            if not task:
                return {"success": False, "message": "Task not found"}

            user = db.query(User).filter_by(id=task.user_id).first()

            # Get recent execution history
            recent_tasks = (
                db.query(Task)
                .filter_by(user_id=task.user_id, task_type=task.task_type)
                .order_by(Task.executed_at.desc())
                .limit(10)
                .all()
            )

            history = []
            for t in recent_tasks:
                history.append(
                    {
                        "id": t.id,
                        "executed_at": format_datetime_for_display(t.executed_at)
                        if t.executed_at
                        else None,
                        "execution_status": t.execution_status,
                        "external_status": t.external_status,
                        "result": t.result[:100] + "..."
                        if t.result and len(t.result) > 100
                        else t.result,
                    }
                )

            task_detail = {
                "id": task.id,
                "user_id": task.user_id,
                "username": user.username if user else "Unknown",
                "task_type": task.task_type,
                "task_name": task.task_name,
                "description": task.description,
                "cron_expression": task.cron_expression,
                "is_active": task.is_active,
                "execution_status": task.execution_status,
                "external_status": task.external_status,
                "result": task.result,
                "scheduled_time": format_datetime_for_display(task.scheduled_time)
                if task.scheduled_time
                else None,
                "next_run_time": format_datetime_for_display(task.next_run_time)
                if task.next_run_time
                else None,
                "executed_at": format_datetime_for_display(task.executed_at)
                if task.executed_at
                else None,
                "created_at": format_datetime_for_display(task.created_at),
                "history": history,
            }

            return {"success": True, "data": task_detail}
        except Exception as e:
            logger.exception("Failed to get task detail")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def toggle_task(task_id: int) -> Dict[str, Any]:
        """Toggle task active status"""
        db = SessionLocal()
        try:
            task = db.query(Task).filter_by(id=task_id).first()
            if not task:
                return {"success": False, "message": "Task not found"}

            task.is_active = not task.is_active
            db.commit()

            if task.is_active:
                add_task_to_scheduler(task_id)
                message = "任务已启用"
            else:
                remove_task_from_scheduler(task_id)
                message = "任务已禁用"

            return {"success": True, "message": message}
        except Exception as e:
            db.rollback()
            logger.exception("Failed to toggle task")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def trigger_task(task_id: int) -> Dict[str, Any]:
        """Manually trigger a task"""
        try:
            result = BaseTaskService.execute_task(task_id)
            if result.get("success"):
                return {"success": True, "message": "任务已触发执行"}
            return result
        except Exception as e:
            logger.exception("Failed to trigger task")
            return {"success": False, "message": str(e)}

    @staticmethod
    def delete_task(task_id: int) -> Dict[str, Any]:
        """Delete a task"""
        db = SessionLocal()
        try:
            task = db.query(Task).filter_by(id=task_id).first()
            if not task:
                return {"success": False, "message": "Task not found"}

            # Remove from scheduler if active
            if task.is_active:
                remove_task_from_scheduler(task_id)

            db.delete(task)
            db.commit()

            return {"success": True, "message": "任务删除成功"}
        except Exception as e:
            db.rollback()
            logger.exception("Failed to delete task")
            return {"success": False, "message": str(e)}
        finally:
            db.close()
