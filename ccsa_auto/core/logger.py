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
        self._write_lock = threading.Lock()

    def emit(self, record):
        """重写 emit 方法，添加写锁解决并发写入问题"""
        try:
            with self._write_lock:
                if self.shouldRollover(record):
                    self.doRollover()
                super().emit(record)
        except Exception:
            self.handleError(record)

    def doRollover(self):
        """重写轮转逻辑，解决 Windows 文件锁定和多线程问题"""
        with self.rollover_lock:
            # 首先关闭当前流
            self._close_stream()

            current_date_str = datetime.now().strftime("%Y-%m-%d")
            log_dir = os.path.dirname(self.baseFilename)
            base_name = os.path.basename(self.baseFilename)
            base, ext = os.path.splitext(base_name)

            dfn = os.path.join(log_dir, f"{base}_{current_date_str}{ext}")

            safe_dfn = dfn
            counter = 1
            while os.path.exists(safe_dfn):
                base_part, ext_part = os.path.splitext(dfn)
                safe_dfn = f"{base_part}_{counter}{ext_part}"
                counter += 1

            # 尝试多次重命名
            for attempt in range(3):
                try:
                    if os.path.exists(self.baseFilename):
                        self._close_stream()
                        time.sleep(0.1)
                        os.rename(self.baseFilename, safe_dfn)
                    break
                except (OSError, PermissionError):
                    if attempt < 2:
                        time.sleep(0.2 * (attempt + 1))
                    else:
                        try:
                            if os.path.exists(self.baseFilename):
                                self._close_stream()
                                time.sleep(0.1)
                                shutil.copy2(self.baseFilename, safe_dfn)
                                os.remove(self.baseFilename)
                        except (OSError, PermissionError) as copy_error:
                            import sys

                            print(
                                f"[WARNING] 日志轮转失败: {copy_error}", file=sys.stderr
                            )
                            self._reopen_stream()
                            return

            # 清理过期文件
            if self.backupCount > 0:
                for s in self.getFilesToDelete():
                    try:
                        os.remove(s)
                    except OSError:
                        pass

            # 重新打开流
            self._reopen_stream()

    def _close_stream(self):
        """安全关闭流"""
        try:
            if self.stream:
                self.stream.flush()
                self.stream.close()
                self.stream = None
        except Exception:
            pass

    def _reopen_stream(self):
        """重新打开流"""
        try:
            if not self.delay:
                self.stream = self._open()
            else:
                # 对于 delay 模式，需要手动创建文件
                if not os.path.exists(self.baseFilename):
                    os.makedirs(os.path.dirname(self.baseFilename), exist_ok=True)
                self.stream = open(self.baseFilename, "a", encoding="utf-8")
        except Exception:
            pass

    def shouldRollover(self, record):
        """检查是否需要轮转（添加额外保护）"""
        with self._write_lock:
            try:
                return super().shouldRollover(record)
            except Exception:
                return False


def setup_logger(name: str | None = None) -> logging.Logger:
    """配置并返回日志器

    日志格式: %(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s
    日志文件: logs/app.log (按天自动轮转，保留60天)
    """
    logger = logging.getLogger(name or "ccsa_auto")
    logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))

    if logger.handlers:
        return logger

    log_dir = Config.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)

    # 使用固定的文件名，TimedRotatingFileHandler 会自动按日期轮转
    log_file = os.path.join(log_dir, "app.log")
    # 使用安全的处理器替代标准 TimedRotatingFileHandler
    file_handler = SafeTimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=Config.LOG_RETENTION_DAYS
    )
    # 设置后缀格式，用于轮转后的文件名
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
