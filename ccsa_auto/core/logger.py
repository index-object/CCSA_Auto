import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from ccsa_auto.core.config import Config


def setup_logger(name: str = None) -> logging.Logger:
    """配置并返回日志器

    日志格式: %(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s
    日志文件: logs/app_YYYY-MM-DD.log (按天切割，保留60天)
    """
    logger = logging.getLogger(name or "ccsa_auto")
    logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))

    if logger.handlers:
        return logger

    log_dir = Config.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=Config.LOG_RETENTION_DAYS
    )
    file_handler.suffix = "%Y-%m-%d"

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
