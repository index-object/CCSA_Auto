import logging
from typing import Any, Optional

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import SystemConfig

logger = logging.getLogger(__name__)

DEFAULT_CONFIGS = {
    "score_target": {"value": "650", "type": "int", "description": "目标分数"},
    "score_threshold": {"value": "20", "type": "int", "description": "接近阈值（分）"},
    "score_random_min": {"value": "0.30", "type": "float", "description": "随机分数下限"},
    "score_random_max": {"value": "1.00", "type": "float", "description": "随机分数上限"},
    "score_strategy_enabled": {"value": "true", "type": "bool", "description": "是否启用控分策略"},
    "daily_deduction_enabled": {"value": "true", "type": "bool", "description": "每日一题是否启用随机扣分"},
    "daily_deduction_min": {"value": "1", "type": "int", "description": "每日一题最少答错题数"},
    "daily_deduction_max": {"value": "2", "type": "int", "description": "每日一题最多答错题数"},
}


class SystemConfigService:
    """系统配置服务"""

    _cache: dict[str, Any] = {}
    _cache_valid: bool = False

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """获取配置值"""
        db = SessionLocal()
        try:
            config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
            if config:
                return SystemConfigService._parse_value(config.config_value, config.config_type)
            if key in DEFAULT_CONFIGS:
                return SystemConfigService._parse_value(
                    DEFAULT_CONFIGS[key]["value"], DEFAULT_CONFIGS[key]["type"]
                )
            return default
        except Exception as e:
            logger.error(f"获取配置失败: {key}, {e}")
            if key in DEFAULT_CONFIGS:
                return SystemConfigService._parse_value(
                    DEFAULT_CONFIGS[key]["value"], DEFAULT_CONFIGS[key]["type"]
                )
            return default
        finally:
            db.close()

    @staticmethod
    def set(key: str, value: Any, config_type: str = "string", description: str = None) -> bool:
        """设置配置值"""
        db = SessionLocal()
        try:
            config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
            str_value = str(value) if not isinstance(value, str) else value

            if config:
                config.config_value = str_value
                config.config_type = config_type
                if description:
                    config.description = description
            else:
                config = SystemConfig(
                    config_key=key,
                    config_value=str_value,
                    config_type=config_type,
                    description=description or DEFAULT_CONFIGS.get(key, {}).get("description", ""),
                )
                db.add(config)

            db.commit()
            SystemConfigService._cache_valid = False
            logger.info(f"配置已更新: {key}={value}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"设置配置失败: {key}={value}, {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def get_all() -> list[SystemConfig]:
        """获取所有配置"""
        db = SessionLocal()
        try:
            return db.query(SystemConfig).all()
        finally:
            db.close()

    @staticmethod
    def init_defaults():
        """初始化默认配置"""
        db = SessionLocal()
        try:
            for key, info in DEFAULT_CONFIGS.items():
                existing = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
                if not existing:
                    config = SystemConfig(
                        config_key=key,
                        config_value=info["value"],
                        config_type=info["type"],
                        description=info["description"],
                    )
                    db.add(config)
            db.commit()
            logger.info("默认配置初始化完成")
        except Exception as e:
            db.rollback()
            logger.error(f"初始化默认配置失败: {e}")
        finally:
            db.close()

    @staticmethod
    def get_score_target() -> int:
        """获取目标分数"""
        return SystemConfigService.get("score_target", 650)

    @staticmethod
    def get_score_threshold() -> int:
        """获取接近阈值"""
        return SystemConfigService.get("score_threshold", 20)

    @staticmethod
    def get_score_random_range() -> tuple[float, float]:
        """获取随机分数范围"""
        min_val = SystemConfigService.get("score_random_min", 0.30)
        max_val = SystemConfigService.get("score_random_max", 1.00)
        return (min_val, max_val)

    @staticmethod
    def is_score_strategy_enabled() -> bool:
        """是否启用控分策略"""
        return SystemConfigService.get("score_strategy_enabled", True)

    @staticmethod
    def is_daily_deduction_enabled() -> bool:
        """每日一题是否启用随机扣分"""
        return SystemConfigService.get("daily_deduction_enabled", True)

    @staticmethod
    def get_daily_deduction_range() -> tuple[int, int]:
        """获取每日一题随机扣分范围（答错题数）"""
        min_val = SystemConfigService.get("daily_deduction_min", 1)
        max_val = SystemConfigService.get("daily_deduction_max", 2)
        return (min_val, max_val)

    @staticmethod
    def _parse_value(value: str, value_type: str) -> Any:
        """解析配置值"""
        try:
            if value_type == "int":
                return int(value)
            elif value_type == "float":
                return float(value)
            elif value_type == "bool":
                return value.lower() in ("true", "1", "yes")
            else:
                return value
        except (ValueError, TypeError):
            return value