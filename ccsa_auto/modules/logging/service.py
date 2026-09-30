"""日志服务：面向管理后台的结构化日志台账。

与 ``ccsa_auto.core.logger``（文件日志）的分工：

* ``core.logger``  —— 运行期排障用的**文件日志**，分渠道、每天归档、带上下文；
* 本模块            —— 可查询、可导出、可在后台展示的**数据库台账**，
  覆盖操作、认证、访问、错误以及精确的任务运行记录。

两者互补：文件日志回答“当时发生了什么”，数据库台账回答“谁在什么时候做了什么”。
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import or_

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.logger import get_logger
from ccsa_auto.modules.logging.models import AppLog, TaskRunLog

logger = get_logger(__name__)

_DETAIL_MAX_LEN = 8000


class LogType:
    """日志类型（同时用于管理后台筛选）。"""

    OPERATION = "operation"  # 管理员操作
    TASK = "task"  # 任务执行台账（失败日报依赖此类型）
    AUTH = "auth"  # 登录/登出
    ACCESS = "access"  # 客户访问
    SYSTEM = "system"  # 系统事件（启动、定时任务、维护）
    ERROR = "error"  # 错误


_STATUS_SUCCESS = "success"
_STATUS_FAILED = "failed"


def _dump_detail(detail: Any) -> Optional[str]:
    if detail is None:
        return None
    if isinstance(detail, str):
        text = detail
    else:
        try:
            text = json.dumps(detail, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            text = str(detail)
    return text[:_DETAIL_MAX_LEN]


def current_client_ip(default: Optional[str] = None) -> Optional[str]:
    """尽力获取当前 NiceGUI 客户端的 IP（后台线程/无上下文时返回 default）。"""
    try:
        from nicegui import ui

        client = getattr(ui.context, "client", None)
        ip = getattr(client, "ip", None) if client else None
        return ip or default
    except Exception:  # noqa: BLE001 - 拿不到就算了
        return default


class LoggingService:
    """统一日志服务（数据库台账）。所有方法都不会向上抛异常。"""

    # ------------------------------------------------------------------
    # 基础写入
    # ------------------------------------------------------------------
    @staticmethod
    def log(
        log_type: str,
        operation: str,
        content: str,
        user_id: Optional[int] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        status: str = _STATUS_SUCCESS,
        detail: Any = None,
    ) -> Optional[int]:
        """记录一条台账日志，返回自增 ID（失败返回 None）。"""
        message = content
        if detail is not None:
            dumped = _dump_detail(detail)
            if dumped:
                message = f"{content} | detail={dumped}" if content else dumped

        db = SessionLocal()
        try:
            entry = AppLog(
                log_type=log_type,
                operation=operation,
                content=message,
                user_id=user_id,
                target_type=target_type,
                target_id=target_id,
                ip_address=ip_address,
                status=status,
            )
            db.add(entry)
            db.commit()
            return entry.id
        except Exception as exc:  # noqa: BLE001 - 日志失败不能影响业务
            db.rollback()
            logger.error(f"记录日志失败: {exc}")
            return None
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 业务辅助方法
    # ------------------------------------------------------------------
    @staticmethod
    def log_admin_operation(
        admin_id: int,
        operation: str,
        target_type: str,
        target_id: Optional[int],
        content: str,
        ip_address: Optional[str] = None,
        detail: Any = None,
    ) -> Optional[int]:
        """记录管理员操作。"""
        if ip_address is None:
            ip_address = current_client_ip()
        return LoggingService.log(
            log_type=LogType.OPERATION,
            operation=operation,
            content=content,
            user_id=admin_id,
            target_type=target_type,
            target_id=target_id,
            ip_address=ip_address,
            detail=detail,
        )

    @staticmethod
    def log_task_execution(
        task_id: int,
        user_id: int,
        task_type: str,
        status: str,
        message: str,
        detail: Any = None,
    ) -> Optional[int]:
        """记录任务执行台账。

        注意：任务失败日报通过 ``log_type=TASK & status=failed`` + 主键水位统计，
        因此这里的类型/状态取值不要随意改动。
        """
        return LoggingService.log(
            log_type=LogType.TASK,
            operation=task_type,
            content=message,
            user_id=user_id,
            target_type="task",
            target_id=task_id,
            status=status,
            detail=detail,
        )

    @staticmethod
    def log_auth(
        user_id: Optional[int],
        action: str,
        success: bool,
        ip_address: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> Optional[int]:
        """记录认证事件。"""
        if ip_address is None:
            ip_address = current_client_ip()
        return LoggingService.log(
            log_type=LogType.AUTH,
            operation=action,
            content=detail or f"{action} {'成功' if success else '失败'}",
            user_id=user_id,
            ip_address=ip_address,
            status=_STATUS_SUCCESS if success else _STATUS_FAILED,
        )

    @staticmethod
    def log_access(
        event: str,
        user_id: Optional[int] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        content: Optional[str] = None,
    ) -> Optional[int]:
        """记录客户访问。"""
        ok = status_code is None or status_code < 400
        parts = [p for p in (method, path) if p]
        summary = content or (f"{' '.join(parts)} -> {status_code}" if parts else event)
        if duration_ms is not None:
            summary = f"{summary} ({duration_ms:.0f}ms)"
        return LoggingService.log(
            log_type=LogType.ACCESS,
            operation=event,
            content=summary,
            user_id=user_id,
            target_type="page" if path else None,
            ip_address=ip_address,
            status=_STATUS_SUCCESS if ok else _STATUS_FAILED,
            detail={"session_id": session_id} if session_id else None,
        )

    @staticmethod
    def log_system(
        operation: str,
        content: str,
        status: str = _STATUS_SUCCESS,
        detail: Any = None,
    ) -> Optional[int]:
        """记录系统事件。"""
        return LoggingService.log(
            log_type=LogType.SYSTEM,
            operation=operation,
            content=content,
            status=status,
            detail=detail,
        )

    @staticmethod
    def log_error(
        operation: str,
        content: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        detail: Any = None,
    ) -> Optional[int]:
        """记录错误日志。"""
        return LoggingService.log(
            log_type=LogType.ERROR,
            operation=operation,
            content=content,
            user_id=user_id,
            ip_address=ip_address,
            status=_STATUS_FAILED,
            detail=detail,
        )

    # ------------------------------------------------------------------
    # 精确任务运行记录
    # ------------------------------------------------------------------
    @staticmethod
    def log_task_run_start(
        task_id: Optional[int],
        user_id: Optional[int],
        task_type: str,
        task_name: Optional[str] = None,
        trigger: str = "schedule",
        trace_id: Optional[str] = None,
        started_at: Optional[datetime] = None,
        max_attempts: int = 1,
    ) -> Optional[int]:
        """写入一条“运行中”的任务记录，返回主键，供结束时更新。"""
        db = SessionLocal()
        try:
            entry = TaskRunLog(
                trace_id=trace_id,
                task_id=task_id,
                user_id=user_id,
                task_type=task_type,
                task_name=task_name,
                status="running",
                trigger=trigger,
                attempt=1,
                max_attempts=max_attempts,
                started_at=started_at or datetime.utcnow(),
            )
            db.add(entry)
            db.commit()
            return entry.id
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.error(f"写入任务运行开始记录失败: {exc}")
            return None
        finally:
            db.close()

    @staticmethod
    def log_task_run_finish(
        run_id: Optional[int],
        status: str,
        *,
        task_id: Optional[int] = None,
        user_id: Optional[int] = None,
        task_type: Optional[str] = None,
        task_name: Optional[str] = None,
        trigger: str = "schedule",
        trace_id: Optional[str] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        attempt: int = 1,
        max_attempts: int = 1,
        message: Optional[str] = None,
        error_type: Optional[str] = None,
        result: Any = None,
        next_run_time: Optional[datetime] = None,
    ) -> Optional[int]:
        """更新任务运行结果；``run_id`` 为空时退化为直接插入一条完整记录。"""
        finished_at = finished_at or datetime.utcnow()
        result = result or {}
        summary = result.get("score_strategy") or {}
        values = dict(
            status=status,
            finished_at=finished_at,
            duration_ms=duration_ms,
            attempt=attempt,
            max_attempts=max_attempts,
            message=message,
            error_type=error_type,
            next_run_time=next_run_time,
            detail=_dump_detail(result.get("result", result)),
            total_questions=summary.get("correct_questions", 0)
            + summary.get("wrong_questions", 0),
            correct_questions=summary.get("correct_questions"),
            score=summary.get("score"),
            max_score=summary.get("max_score"),
        )

        db = SessionLocal()
        try:
            entry = None
            if run_id is not None:
                entry = db.query(TaskRunLog).filter_by(id=run_id).first()
            if entry is None:
                entry = TaskRunLog(
                    trace_id=trace_id,
                    task_id=task_id,
                    user_id=user_id,
                    task_type=task_type or "unknown",
                    task_name=task_name,
                    trigger=trigger,
                    started_at=started_at or finished_at,
                )
                db.add(entry)
            for key, value in values.items():
                if value is not None:
                    setattr(entry, key, value)
            db.commit()
            return entry.id
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.error(f"写入任务运行结果失败: {exc}")
            return None
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    @staticmethod
    def get_logs(
        log_type: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """查询台账日志（支持关键词与类型过滤）。"""
        db = SessionLocal()
        try:
            query = db.query(AppLog)

            if log_type and log_type != "all":
                query = query.filter(AppLog.log_type == log_type)
            if user_id is not None:
                query = query.filter(AppLog.user_id == user_id)
            if start_date:
                query = query.filter(AppLog.created_at >= start_date)
            if end_date:
                # 结束日期按“当天 23:59:59”处理，避免只查到 00:00:00
                query = query.filter(AppLog.created_at < end_date + timedelta(days=1))
            if keyword:
                like = f"%{keyword}%"
                query = query.filter(
                    or_(
                        AppLog.operation.like(like),
                        AppLog.content.like(like),
                        AppLog.ip_address.like(like),
                    )
                )

            total = query.count()
            logs = (
                query.order_by(AppLog.created_at.desc(), AppLog.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            return {
                "success": True,
                "logs": [log.to_dict() for log in logs],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"查询日志失败: {e}")
            return {"success": False, "message": str(e), "logs": [], "total": 0}
        finally:
            db.close()

    @staticmethod
    def get_task_runs(
        task_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """查询精确任务运行记录。"""
        db = SessionLocal()
        try:
            query = db.query(TaskRunLog)
            if task_id is not None:
                query = query.filter(TaskRunLog.task_id == task_id)
            if user_id is not None:
                query = query.filter(TaskRunLog.user_id == user_id)
            if status and status != "all":
                query = query.filter(TaskRunLog.status == status)
            if task_type and task_type != "all":
                query = query.filter(TaskRunLog.task_type == task_type)
            if start_date:
                query = query.filter(TaskRunLog.started_at >= start_date)
            if end_date:
                query = query.filter(
                    TaskRunLog.started_at < end_date + timedelta(days=1)
                )

            total = query.count()
            runs = (
                query.order_by(TaskRunLog.started_at.desc(), TaskRunLog.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            return {
                "success": True,
                "runs": [run.to_dict() for run in runs],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"查询任务运行记录失败: {e}")
            return {"success": False, "message": str(e), "runs": [], "total": 0}
        finally:
            db.close()

    @staticmethod
    def get_task_run_statistics(days: int = 7) -> Dict[str, Any]:
        """最近 N 天任务运行概览（成功/失败/平均耗时）。"""
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)
            rows = (
                db.query(TaskRunLog)
                .filter(TaskRunLog.started_at >= since)
                .all()
            )
            total = len(rows)
            success = sum(1 for r in rows if r.status == "success")
            failed = sum(1 for r in rows if r.status == "failed")
            durations = [r.duration_ms for r in rows if r.duration_ms]
            return {
                "success": True,
                "days": days,
                "total": total,
                "success": success,
                "failed": failed,
                "success_rate": round(success / total * 100, 2) if total else None,
                "avg_duration_ms": int(sum(durations) / len(durations))
                if durations
                else None,
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"统计任务运行记录失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 维护 / 导出
    # ------------------------------------------------------------------
    @staticmethod
    def cleanup_old_logs(
        days: int = 60, task_run_days: Optional[int] = None
    ) -> int:
        """清理过期台账日志与任务运行记录，返回删除条数。"""
        db = SessionLocal()
        deleted = 0
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted += (
                db.query(AppLog).filter(AppLog.created_at < cutoff_date).delete()
            )

            run_days = (
                task_run_days
                if task_run_days is not None
                else max(days, 90)
            )
            run_cutoff = datetime.utcnow() - timedelta(days=run_days)
            deleted += (
                db.query(TaskRunLog)
                .filter(TaskRunLog.started_at < run_cutoff)
                .delete()
            )
            db.commit()
            logger.info(f"已清理 {deleted} 条过期日志（保留 {days} 天）")
            return deleted
        except Exception as e:  # noqa: BLE001
            db.rollback()
            logger.error(f"清理日志失败: {e}")
            return 0
        finally:
            db.close()

    @staticmethod
    def export_to_xlsx(
        log_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        keyword: Optional[str] = None,
    ) -> Optional[str]:
        """导出日志为 xlsx 文件，返回文件路径。"""
        try:
            from openpyxl import Workbook

            result = LoggingService.get_logs(
                log_type=log_type,
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                page=1,
                page_size=100000,
            )

            if not result.get("success"):
                return None

            wb = Workbook()
            ws = wb.active
            ws.title = "操作日志"

            headers = [
                "ID",
                "时间",
                "类型",
                "操作",
                "内容",
                "用户ID",
                "目标类型",
                "目标ID",
                "IP",
                "状态",
            ]
            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)

            for row, log in enumerate(result["logs"], 2):
                ws.cell(row=row, column=1, value=log["id"])
                ws.cell(row=row, column=2, value=log["created_at"])
                ws.cell(row=row, column=3, value=log["log_type"])
                ws.cell(row=row, column=4, value=log["operation"])
                ws.cell(row=row, column=5, value=log["content"])
                ws.cell(row=row, column=6, value=log["user_id"])
                ws.cell(row=row, column=7, value=log["target_type"])
                ws.cell(row=row, column=8, value=log["target_id"])
                ws.cell(row=row, column=9, value=log["ip_address"])
                ws.cell(row=row, column=10, value=log["status"])

            for column in ws.columns:
                max_length = max(len(str(cell.value or "")) for cell in column)
                ws.column_dimensions[column[0].column_letter].width = min(
                    max_length + 2, 50
                )

            export_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "exports",
            )
            os.makedirs(export_dir, exist_ok=True)

            filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(export_dir, filename)
            wb.save(filepath)

            logger.info(f"日志导出成功: {filepath}")
            return filepath

        except ImportError:
            logger.error("openpyxl 未安装，无法导出 xlsx")
            return None
        except Exception as e:  # noqa: BLE001
            logger.error(f"导出日志失败: {e}")
            return None
