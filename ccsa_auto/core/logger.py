import logging
import os
import shutil
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from ccsa_auto.core.config import Config


class SafeTimedRotatingFileHandler(TimedRotatingFileHandler):
    """安全的日志轮转处理器 - 解决 Windows 文件锁定问题"""

    def __init__(self, *args, **kwargs):
        # Windows 上延迟打开文件，避免初始化时锁定
        kwargs.setdefault("delay", True)
        super().__init__(*args, **kwargs)

    def doRollover(self):
        """重写轮转逻辑，解决 Windows 文件锁定问题"""
        # 关闭当前流
        if self.stream:
            self.stream.close()
            self.stream = None

        # 获取目标文件名 (格式: app_YYYY-MM-DD.log)
        dfn = self.rotation_filename(
            os.path.join(
                os.path.dirname(self.baseFilename),
                os.path.basename(self.baseFilename).replace(
                    datetime.now().strftime("%Y-%m-%d"), self.suffix
                ),
            )
        )

        # 如果 suffix 与 baseFilename 相同，使用默认命名
        if dfn == self.baseFilename:
            dfn = self.rotation_filename(
                datetime.now()
                .strftime("%Y-%m-%d")
                .join(os.path.splitext(self.baseFilename)[:1])
                + "_%Y-%m-%d.log"
            )

        safe_dfn = dfn
        counter = 1
        # 如果目标文件已存在，添加序号避免冲突
        while os.path.exists(safe_dfn):
            base, ext = os.path.splitext(dfn)
            safe_dfn = f"{base}_{counter}{ext}"
            counter += 1

        # 尝试安全的轮转方式
        try:
            # 尝试直接重命名（最快的方式）
            if os.path.exists(self.baseFilename):
                os.rename(self.baseFilename, safe_dfn)
        except (OSError, PermissionError):
            # Windows 上重命名失败时，使用复制+删除
            try:
                if os.path.exists(self.baseFilename):
                    shutil.copy2(self.baseFilename, safe_dfn)
                    os.remove(self.baseFilename)
            except (OSError, PermissionError) as e:
                # 如果仍然失败，记录错误但不影响程序运行
                import sys

                print(f"[WARNING] 日志轮转失败: {e}", file=sys.stderr)
                # 重新打开原文件继续写入
                if os.path.exists(self.baseFilename):
                    self.stream = open(self.baseFilename, "a")
                return

        # 删除过期日志
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                try:
                    os.remove(s)
                except OSError:
                    pass

        # 重新打开新日志文件
        if not self.delay:
            self.stream = self._open()


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
