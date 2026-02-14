import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import User, Task, Announcement
from ccsa_auto.utils.timezone import get_current_time, SHANGHAI_TZ

logger = logging.getLogger(__name__)


class DashboardService:
    """Dashboard statistics service for admin_v2"""

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """Get dashboard statistics"""
        db = SessionLocal()
        try:
            now = get_current_time()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_utc = today_start.astimezone(timedelta(hours=0))
            week_start = today_start - timedelta(days=7)
            week_start_utc = week_start.astimezone(timedelta(hours=0))
            month_start = today_start - timedelta(days=30)
            month_start_utc = month_start.astimezone(timedelta(hours=0))

            # User statistics
            total_users = db.query(User).count()
            active_users = db.query(User).filter_by(status=0).count()
            banned_users = db.query(User).filter_by(status=1).count()
            new_users_today = (
                db.query(User).filter(User.created_at >= today_start_utc).count()
            )
            new_users_week = (
                db.query(User).filter(User.created_at >= week_start_utc).count()
            )
            new_users_month = (
                db.query(User).filter(User.created_at >= month_start_utc).count()
            )

            # Task statistics
            total_tasks = db.query(Task).count()
            active_tasks = db.query(Task).filter_by(is_active=True).count()
            inactive_tasks = db.query(Task).filter_by(is_active=False).count()
            pending_tasks = db.query(Task).filter_by(execution_status="pending").count()
            running_tasks = db.query(Task).filter_by(execution_status="running").count()
            completed_tasks = (
                db.query(Task).filter_by(execution_status="completed").count()
            )
            failed_tasks = db.query(Task).filter_by(execution_status="failed").count()

            # Tasks completed today
            completed_today = (
                db.query(Task)
                .filter(
                    Task.executed_at >= today_start_utc,
                    Task.execution_status == "completed",
                )
                .count()
            )

            # Tasks failed today
            failed_today = (
                db.query(Task)
                .filter(
                    Task.executed_at >= today_start_utc,
                    Task.execution_status == "failed",
                )
                .count()
            )

            # Announcement statistics
            total_announcements = db.query(Announcement).count()

            # Calculate success rate
            total_completed_or_failed = completed_tasks + failed_tasks
            success_rate = (
                round(completed_tasks / total_completed_or_failed * 100, 1)
                if total_completed_or_failed > 0
                else 0.0
            )

            return {
                "success": True,
                "data": {
                    "users": {
                        "total": total_users,
                        "active": active_users,
                        "banned": banned_users,
                        "new_today": new_users_today,
                        "new_week": new_users_week,
                        "new_month": new_users_month,
                    },
                    "tasks": {
                        "total": total_tasks,
                        "active": active_tasks,
                        "inactive": inactive_tasks,
                        "pending": pending_tasks,
                        "running": running_tasks,
                        "completed": completed_tasks,
                        "failed": failed_tasks,
                        "completed_today": completed_today,
                        "failed_today": failed_today,
                        "success_rate": success_rate,
                    },
                    "announcements": {
                        "total": total_announcements,
                    },
                },
            }
        except Exception as e:
            logger.exception("Failed to get statistics")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def get_user_trend(days: int = 7) -> Dict[str, Any]:
        """Get user registration trend"""
        db = SessionLocal()
        try:
            now = get_current_time()
            start_date = now - timedelta(days=days)
            start_date_utc = start_date.astimezone(timedelta(hours=0))

            users = (
                db.query(User)
                .filter(User.created_at >= start_date_utc)
                .order_by(User.created_at.asc())
                .all()
            )

            # Group by date
            trend = {}
            for user in users:
                if user.created_at:
                    # Convert to Shanghai timezone
                    date_key = user.created_at.astimezone(SHANGHAI_TZ).strftime(
                        "%Y-%m-%d"
                    )
                    trend[date_key] = trend.get(date_key, 0) + 1

            # Fill in missing dates with 0
            result = []
            for i in range(days):
                date = (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
                result.append(
                    {
                        "date": date,
                        "count": trend.get(date, 0),
                    }
                )

            return {
                "success": True,
                "data": result,
            }
        except Exception as e:
            logger.exception("Failed to get user trend")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def get_task_trend(days: int = 7) -> Dict[str, Any]:
        """Get task completion trend"""
        db = SessionLocal()
        try:
            now = get_current_time()
            start_date = now - timedelta(days=days)
            start_date_utc = start_date.astimezone(timedelta(hours=0))

            # Get completed tasks
            completed = {}
            failed = {}

            tasks = (
                db.query(Task)
                .filter(Task.executed_at >= start_date_utc)
                .order_by(Task.executed_at.asc())
                .all()
            )

            for task in tasks:
                if task.executed_at and task.execution_status:
                    date_key = task.executed_at.astimezone(SHANGHAI_TZ).strftime(
                        "%Y-%m-%d"
                    )
                    if task.execution_status == "completed":
                        completed[date_key] = completed.get(date_key, 0) + 1
                    elif task.execution_status == "failed":
                        failed[date_key] = failed.get(date_key, 0) + 1

            # Fill in missing dates with 0
            result = []
            for i in range(days):
                date = (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
                result.append(
                    {
                        "date": date,
                        "completed": completed.get(date, 0),
                        "failed": failed.get(date, 0),
                    }
                )

            return {
                "success": True,
                "data": result,
            }
        except Exception as e:
            logger.exception("Failed to get task trend")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def get_task_status_distribution() -> Dict[str, Any]:
        """Get task status distribution"""
        db = SessionLocal()
        try:
            statuses = (
                db.query(Task.execution_status, db.func.count(Task.id))
                .group_by(Task.execution_status)
                .all()
            )

            total = sum(count for _, count in statuses)
            distribution = []

            for status, count in statuses:
                distribution.append(
                    {
                        "name": status,
                        "value": count,
                        "percentage": round(count / total * 100, 1) if total > 0 else 0,
                    }
                )

            return {
                "success": True,
                "data": distribution,
            }
        except Exception as e:
            logger.exception("Failed to get task status distribution")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def get_user_status_distribution() -> Dict[str, Any]:
        """Get user status distribution"""
        db = SessionLocal()
        try:
            statuses = (
                db.query(User.status, db.func.count(User.id))
                .group_by(User.status)
                .all()
            )

            total = sum(count for _, count in statuses)
            distribution = []

            status_map = {0: "正常", 1: "封号"}
            for status, count in statuses:
                distribution.append(
                    {
                        "name": status_map.get(status, str(status)),
                        "value": count,
                        "percentage": round(count / total * 100, 1) if total > 0 else 0,
                    }
                )

            return {
                "success": True,
                "data": distribution,
            }
        except Exception as e:
            logger.exception("Failed to get user status distribution")
            return {"success": False, "message": str(e)}
        finally:
            db.close()
