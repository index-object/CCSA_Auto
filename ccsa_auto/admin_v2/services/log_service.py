import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ccsa_auto.modules.logging.service import LoggingService
from ccsa_auto.utils.timezone import format_datetime_for_display

logger = logging.getLogger(__name__)


class LogManagementService:
    """Log management service for admin_v2"""

    @staticmethod
    def get_logs(
        keyword: str = None,
        log_type: str = None,
        start_date: str = None,
        end_date: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get operation logs with filters"""
        try:
            # Convert date strings to datetime
            start_dt = None
            end_dt = None

            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    pass

            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    pass

            result = LoggingService.get_logs(
                log_type=log_type,
                start_date=start_dt,
                end_date=end_dt,
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
    def export_logs(
        log_type: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> Dict[str, Any]:
        """Export logs to file"""
        try:
            start_dt = None
            end_dt = None

            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    pass

            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    pass

            filepath = LoggingService.export_to_xlsx(
                log_type=log_type,
                start_date=start_dt,
                end_date=end_dt,
            )

            if filepath:
                return {"success": True, "filepath": filepath}
            else:
                return {"success": False, "message": "导出失败"}
        except Exception as e:
            logger.exception("Failed to export logs")
            return {"success": False, "message": str(e)}
