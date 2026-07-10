import sys
from loguru import logger
from ccsa_auto.core.config import Config


def setup_logger(name: str | None = None):
    """配置 Loguru 日志器"""

    logger.remove()

    logger.add(
        "logs/app.log",
        rotation="00:00",
        retention="60 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} - {message}",
        level=Config.LOG_LEVEL,
        encoding="utf-8",
        enqueue=True,
    )

    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=Config.LOG_LEVEL,
        colorize=True,
    )

    return logger


logger = setup_logger()
