"""分数追踪模型"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship

from ccsa_auto.core.database import Base, SessionLocal
from ccsa_auto.utils.timezone import get_current_time, utc_to_shanghai

logger = logging.getLogger(__name__)


class ScoreRecord(Base):
    """任务得分记录表"""

    __tablename__ = "score_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    task_id = Column(Integer, index=True)
    task_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    record_date = Column(DateTime, nullable=False, index=True)  # 记录日期（上海时间）
    total_questions = Column(Integer, default=0)  # 总题数
    correct_questions = Column(Integer, default=0)  # 正确题数
    score = Column(Float, default=0.0)  # 实际得分
    max_score = Column(Float, default=0.0)  # 满分
    score_ratio = Column(Float, default=1.0)  # 得分比例
    metadata_json = Column(Text)  # 额外元数据（JSON字符串）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "task_type": self.task_type,
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "total_questions": self.total_questions,
            "correct_questions": self.correct_questions,
            "score": self.score,
            "max_score": self.max_score,
            "score_ratio": self.score_ratio,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ScoreTracker:
    """分数追踪服务"""

    @staticmethod
    def record_score(
        user_id: int,
        task_id: Optional[int],
        task_type: str,
        total_questions: int,
        correct_questions: int,
        score: float,
        max_score: float,
        record_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        记录任务得分

        Args:
            user_id: 用户ID
            task_id: 任务ID
            task_type: 任务类型 (daily, weekly, monthly)
            total_questions: 总题数
            correct_questions: 正确题数
            score: 实际得分
            max_score: 满分
            record_date: 记录日期（上海时间），默认为当前日期
            metadata: 额外元数据

        Returns:
            int: 记录ID，失败返回None
        """
        db = SessionLocal()
        try:
            if record_date is None:
                record_date = get_current_time()
            else:
                record_date = utc_to_shanghai(record_date)

            score_ratio = score / max_score if max_score > 0 else 0.0

            import json

            record = ScoreRecord(
                user_id=user_id,
                task_id=task_id,
                task_type=task_type,
                record_date=record_date,
                total_questions=total_questions,
                correct_questions=correct_questions,
                score=score,
                max_score=max_score,
                score_ratio=score_ratio,
                metadata_json=json.dumps(metadata, ensure_ascii=False)
                if metadata
                else None,
            )

            db.add(record)
            db.commit()
            db.refresh(record)

            logger.info(
                f"记录得分成功: user_id={user_id}, task_type={task_type}, score={score}/{max_score}"
            )
            return record.id

        except Exception as e:
            db.rollback()
            logger.error(f"记录得分失败: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def get_monthly_scores(user_id: int, year: int, month: int) -> List[ScoreRecord]:
        """
        获取指定月份的所有得分记录

        Args:
            user_id: 用户ID
            year: 年份
            month: 月份

        Returns:
            List[ScoreRecord]: 得分记录列表
        """
        db = SessionLocal()
        try:
            from datetime import timedelta

            from ccsa_auto.utils.timezone import SHANGHAI_TZ

            start_date = datetime(year, month, 1, 0, 0, 0).replace(tzinfo=SHANGHAI_TZ)
            if month == 12:
                next_year = year + 1
                next_month = 1
            else:
                next_year = year
                next_month = month + 1

            end_date = datetime(next_year, next_month, 1, 0, 0, 0).replace(
                tzinfo=SHANGHAI_TZ
            ) - timedelta(seconds=1)

            records = (
                db.query(ScoreRecord)
                .filter(
                    ScoreRecord.user_id == user_id,
                    ScoreRecord.record_date >= start_date,
                    ScoreRecord.record_date <= end_date,
                )
                .order_by(ScoreRecord.record_date)
                .all()
            )

            return records

        except Exception as e:
            logger.error(f"获取月度得分失败: {e}")
            return []
        finally:
            db.close()

    @staticmethod
    def calculate_monthly_total(
        user_id: int, year: int, month: int
    ) -> Dict[str, float]:
        """
        计算指定月份的总得分（按任务类型分组）

        Args:
            user_id: 用户ID
            year: 年份
            month: 月份

        Returns:
            Dict: {"total": 总分, "daily": 每日一题总分, "weekly": 每周一课总分, "monthly": 每月一考总分}
        """
        records = ScoreTracker.get_monthly_scores(user_id, year, month)

        total = 0.0
        daily_total = 0.0
        weekly_total = 0.0
        monthly_total = 0.0

        for record in records:
            total += record.score
            if record.task_type == "daily":
                daily_total += record.score
            elif record.task_type == "weekly":
                weekly_total += record.score
            elif record.task_type == "monthly":
                monthly_total += record.score

        return {
            "total": total,
            "daily": daily_total,
            "weekly": weekly_total,
            "monthly": monthly_total,
        }

    @staticmethod
    def get_current_month_scores(user_id: int) -> Dict[str, float]:
        """
        获取当前月份的总得分

        Args:
            user_id: 用户ID

        Returns:
            Dict: {"total": 总分, "daily": 每日一题总分, "weekly": 每周一课总分, "monthly": 每月一考总分, "year": 年, "month": 月}
        """
        now = get_current_time()
        scores = ScoreTracker.calculate_monthly_total(user_id, now.year, now.month)
        scores["year"] = now.year
        scores["month"] = now.month
        return scores

    @staticmethod
    def get_score_control_status(user_id: int) -> Dict[str, Any]:
        """
        获取控分策略状态信息

        Args:
            user_id: 用户ID

        Returns:
            Dict: {
                "current_monthly_score": 当前月度得分,
                "target_monthly_score": 目标月度得分,
                "remaining_potential": 剩余可能得分,
                "progress_percentage": 进度百分比,
                "status": 状态（ahead, on_track, behind）
            }
        """
        now = get_current_time()
        try:
            from ccsa_auto.modules.task.score_strategy import ScoreStrategy

            current_scores = ScoreTracker.get_current_month_scores(user_id)
            current_total = current_scores["total"]
            target = ScoreStrategy.TARGET_MONTHLY_SCORE

            year, month = now.year, now.month
            remaining_potential = ScoreStrategy.calculate_remaining_potential(
                user_id, year, month, now
            )

            total_potential = current_total + remaining_potential["total"]
            progress_percentage = (current_total / target) * 100 if target > 0 else 0

            if current_total >= target:
                status = "ahead"
                status_text = "已达标"
            elif total_potential >= target:
                status = "on_track"
                status_text = "正常进行中"
            else:
                status = "behind"
                status_text = "需要追赶"

            return {
                "current_monthly_score": round(current_total, 2),
                "target_monthly_score": target,
                "remaining_potential": remaining_potential["total"],
                "total_potential": total_potential,
                "progress_percentage": round(progress_percentage, 1),
                "status": status,
                "status_text": status_text,
                "year": year,
                "month": month,
                "breakdown": {
                    "daily": round(current_scores["daily"], 2),
                    "weekly": round(current_scores["weekly"], 2),
                    "monthly": round(current_scores["monthly"], 2),
                },
            }
        except Exception as e:
            logger.error(f"获取控分策略状态失败: {e}")
            year, month = now.year, now.month
            return {
                "current_monthly_score": 0,
                "target_monthly_score": 530,
                "remaining_potential": 0,
                "total_potential": 0,
                "progress_percentage": 0,
                "status": "unknown",
                "status_text": "未知状态",
                "year": year,
                "month": month,
                "breakdown": {
                    "daily": 0,
                    "weekly": 0,
                    "monthly": 0,
                },
            }

    @staticmethod
    def delete_old_records(months_to_keep: int = 6) -> int:
        """
        删除旧的得分记录

        Args:
            months_to_keep: 保留最近几个月的记录

        Returns:
            int: 删除的记录数
        """
        db = SessionLocal()
        try:
            from datetime import timedelta

            from ccsa_auto.utils.timezone import get_current_utc_time

            cutoff_date = get_current_utc_time() - timedelta(days=months_to_keep * 30)

            deleted = (
                db.query(ScoreRecord)
                .filter(ScoreRecord.created_at < cutoff_date)
                .delete()
            )
            db.commit()

            logger.info(f"已删除 {deleted} 条超过 {months_to_keep} 个月的得分记录")
            return deleted

        except Exception as e:
            db.rollback()
            logger.error(f"删除旧记录失败: {e}")
            return 0
        finally:
            db.close()
