from sqlalchemy import Column, Integer, String, Text, DateTime, Float

from datetime import datetime

from ccsa_auto.core.database import Base
from ccsa_auto.utils.timezone import format_datetime_for_display


class AppLog(Base):
    """统一应用日志模型（面向管理后台的“操作/认证/错误/访问”台账）"""

    __tablename__ = "app_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_type = Column(String(20), nullable=False, index=True)
    operation = Column(String(100), nullable=False)
    content = Column(Text)
    user_id = Column(Integer)
    target_type = Column(String(50))
    target_id = Column(Integer)
    ip_address = Column(String(50))
    status = Column(String(20), default="success")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "log_type": self.log_type,
            "operation": self.operation,
            "content": self.content,
            "user_id": self.user_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "ip_address": self.ip_address,
            "status": self.status,
            "created_at": format_datetime_for_display(self.created_at),
        }


class TaskRunLog(Base):
    """精确的任务运行记录：一次任务执行 = 一行。

    与 ``AppLog`` 的区别：``AppLog`` 是面向后台的通用台账（一次成功/失败一条），
    本表记录一次运行的完整生命周期（开始时间、耗时、重试次数、得分、错误类型），
    便于统计任务成功率/耗时分布，也便于排查“某个任务为什么失败”。
    """

    __tablename__ = "task_run_logs"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(32), index=True)
    task_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    task_type = Column(String(20), index=True)
    task_name = Column(String(100))
    # success / failed / skipped / running
    status = Column(String(20), default="running", index=True)
    # schedule（定时触发）/ manual（后台手动触发）/ batch（批量执行）/ fixer（修复器补跑）
    trigger = Column(String(20), default="schedule")
    attempt = Column(Integer, default=1)
    max_attempts = Column(Integer, default=1)
    started_at = Column(DateTime, index=True)
    finished_at = Column(DateTime)
    duration_ms = Column(Integer)
    total_questions = Column(Integer, default=0)
    correct_questions = Column(Integer, default=0)
    score = Column(Float)
    max_score = Column(Float)
    message = Column(Text)
    error_type = Column(String(50))
    next_run_time = Column(DateTime)
    detail = Column(Text)  # JSON 字符串，保留原始结果
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "task_type": self.task_type,
            "task_name": self.task_name,
            "status": self.status,
            "trigger": self.trigger,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "started_at": format_datetime_for_display(self.started_at),
            "finished_at": format_datetime_for_display(self.finished_at),
            "duration_ms": self.duration_ms,
            "total_questions": self.total_questions,
            "correct_questions": self.correct_questions,
            "score": self.score,
            "max_score": self.max_score,
            "message": self.message,
            "error_type": self.error_type,
            "next_run_time": format_datetime_for_display(self.next_run_time),
            "created_at": format_datetime_for_display(self.created_at),
        }
