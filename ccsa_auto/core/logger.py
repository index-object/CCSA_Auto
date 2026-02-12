import logging
import os
import shutil
import threading
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from ccsa_auto.core.config import Config

_global_logger_lock = threading.Lock()


class SafeTimedRotatingFileHandler(TimedRotatingFileHandler):
    """安全的日志轮转处理器 - 解决 Windows 文件锁定和多线程并发问题"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("delay", True)
        super().__init__(*args, **kwargs)
        self.rollover_lock = threading.Lock()

    def doRollover(self):
        """重写轮转逻辑，解决 Windows 文件锁定和多线程问题"""
        with self.rollover_lock:
            if self.stream:
                self.stream.close()
                self.stream = None  # type: ignore

            current_date_str = datetime.now().strftime("%Y-%m-%d")
            log_dir = os.path.dirname(self.baseFilename)
            base_name = os.path.basename(self.baseFilename)

            old_date_pattern = datetime.strptime(
                base_name.split("_")[1].split(".")[0], "%Y-%m-%d"
            ).strftime("%Y-%m-%d")

            new_log_name = base_name.replace(old_date_pattern, current_date_str)
            dfn = os.path.join(log_dir, new_log_name)

            if dfn == self.baseFilename:
                dfn = os.path.join(
                    log_dir, base_name.split("_")[0] + "_" + current_date_str + ".log"
                )

            safe_dfn = dfn
            counter = 1
            while os.path.exists(safe_dfn):
                base, ext = os.path.splitext(dfn)
                safe_dfn = f"{base}_{counter}{ext}"
                counter += 1

            try:
                if os.path.exists(self.baseFilename):
                    os.rename(self.baseFilename, safe_dfn)
            except (OSError, PermissionError):
                try:
                    if os.path.exists(self.baseFilename):
                        shutil.copy2(self.baseFilename, safe_dfn)
                        os.remove(self.baseFilename)
                except (OSError, PermissionError) as e:
                    import sys

                    print(f"[WARNING] 日志轮转失败: {e}", file=sys.stderr)
                    if os.path.exists(self.baseFilename):
                        self.stream = open(self.baseFilename, "a", encoding="utf-8")
                    return

            if self.backupCount > 0:
                for s in self.getFilesToDelete():
                    try:
                        os.remove(s)
                    except OSError:
                        pass

            if not self.delay:
                self.stream = self._open()


def setup_logger(name: str | None = None) -> logging.Logger:
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
    # 使用安全的处理器替代标准 TimedRotatingFileHandler
    file_handler = SafeTimedRotatingFileHandler(
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
