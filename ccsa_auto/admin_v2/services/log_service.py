from typing import Dict, Any, List, Optional
from datetime import datetime

from ccsa_auto.core.logger import get_logger
from ccsa_auto.modules.logging.service import LoggingService, LogType
from ccsa_auto.utils.timezone import format_datetime_for_display

logger = get_logger(__name__)


class LogManagementService:
    """Log management service for admin_v2"""

    @staticmethod
    def _parse_date(value: Any) -> Optional[datetime]:
        """把 ``YYYY-MM-DD`` 字符串安全地转换为 datetime（失败返回 None）。"""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.strptime(str(value), "%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_logs(
        keyword: str = None,
        log_type: str = None,
        start_date: str = None,
        end_date: str = None,
        page: int = 1,
        page_size: int = 20,
        user_id: int = None,
    ) -> Dict[str, Any]:
        """Get operation logs with filters"""
        try:
            start_dt = LogManagementService._parse_date(start_date)
            end_dt = LogManagementService._parse_date(end_date)

            result = LoggingService.get_logs(
                log_type=log_type,
                user_id=user_id,
                start_date=start_dt,
                end_date=end_dt,
                keyword=keyword,
                page=page,
                page_size=page_size,
            )

            if result.get("success"):
                # Format logs for display
                logs = result.get("logs", [])
                formatted_logs = []
                for log in logs:
                    formatted_logs.append(
                        {
                            "id": log.get("id"),
                            "log_type": log.get("log_type"),
                            "operation": log.get("operation"),
                            "content": log.get("content"),
                            "user_id": log.get("user_id"),
                            "target_type": log.get("target_type"),
                            "target_id": log.get("target_id"),
                            "ip_address": log.get("ip_address"),
                            "status": log.get("status"),
                            "created_at": log.get("created_at"),
                        }
                    )

                return {
                    "success": True,
                    "data": formatted_logs,
                    "total": result.get("total", 0),
                    "page": page,
                    "page_size": page_size,
                }

            return result
        except Exception as e:
            logger.exception("Failed to get logs")
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_task_runs(
        keyword: str = None,
        task_id=None,
        user_id=None,
        status=None,
        task_type=None,
        start_date=None,
        end_date=None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get precise task run records.

        ``keyword`` 仅用于兼容调用方签名——``LoggingService.get_task_runs``
        本身不支持关键词过滤，这里不做转发。
        """
        try:
            start_dt = LogManagementService._parse_date(start_date)
            end_dt = LogManagementService._parse_date(end_date)

            result = LoggingService.get_task_runs(
                task_id=task_id,
                user_id=user_id,
                status=status,
                task_type=task_type,
                start_date=start_dt,
                end_date=end_dt,
                page=page,
                page_size=page_size,
            )

            if result.get("success"):
                return {
                    "success": True,
                    "data": result.get("runs", []),
                    "total": result.get("total", 0),
                    "page": page,
                    "page_size": page_size,
                }

            return result
        except Exception as e:
            logger.exception("Failed to get task runs")
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_task_run_statistics(days: int = 7) -> Dict[str, Any]:
        """最近 N 天任务运行概览（透传 LoggingService）。"""
        try:
            return LoggingService.get_task_run_statistics(days=days)
        except Exception as e:
            logger.exception("Failed to get task run statistics")
            return {"success": False, "message": str(e)}

    @staticmethod
    def export_logs(
        log_type: str = None,
        start_date: str = None,
        end_date: str = None,
        keyword: str = None,
    ) -> Dict[str, Any]:
        """Export logs to file"""
        try:
            start_dt = LogManagementService._parse_date(start_date)
            end_dt = LogManagementService._parse_date(end_date)

            filepath = LoggingService.export_to_xlsx(
                log_type=log_type,
                start_date=start_dt,
                end_date=end_dt,
                keyword=keyword,
            )

            if filepath:
                return {"success": True, "filepath": filepath}
            else:
                return {"success": False, "message": "导出失败"}
        except Exception as e:
            logger.exception("Failed to export logs")
            return {"success": False, "message": str(e)}
