"""每用户控分策略配置读取/保存"""

import logging

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import User

logger = logging.getLogger(__name__)

# 与 models.User 对应列的默认值保持一致
DEFAULT_SCORE_CONFIG = {
    "score_strategy_enabled": True,
    "score_target": 650,
    "score_threshold": 20,
    "score_random_min": 0.30,
    "score_random_max": 1.00,
    "daily_deduction_enabled": True,
    "daily_deduction_min": 1,
    "daily_deduction_max": 2,
}
SCORE_CONFIG_FIELDS = list(DEFAULT_SCORE_CONFIG)


def get_user_score_config(user_id: int) -> dict:
    """读取用户控分配置；用户不存在时返回默认配置（不崩）"""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if user is None:
            return dict(DEFAULT_SCORE_CONFIG)
        return {k: getattr(user, k) for k in SCORE_CONFIG_FIELDS}
    finally:
        db.close()


def set_user_score_config(user_id: int, config: dict) -> bool:
    """写回用户控分配置（仅更新传入的键）"""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if user is None:
            return False
        for k in SCORE_CONFIG_FIELDS:
            if k in config:
                setattr(user, k, config[k])
        db.commit()
        return True
    except Exception:
        logger.exception("设置用户控分配置失败: user_id=%s", user_id)
        db.rollback()
        return False
    finally:
        db.close()
