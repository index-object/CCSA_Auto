from ccsa_auto.core.logger import get_task_logger


class Logger:
    """兼容旧接口的日志封装。

    旧实现会为每个模块单独创建标准库 logger 并添加 StreamHandler，
    导致输出分散且格式不一。现在统一委托给核心日志模块的 task 渠道。
    """

    def __init__(self, module_name, debug=False):
        self._logger = get_task_logger(module_name)
        self.debug_enabled = debug

    def debug(self, message):
        self._logger.debug(message)

    def info(self, message):
        self._logger.info(message)

    def warning(self, message):
        self._logger.warning(message)

    def error(self, message):
        self._logger.error(message)
