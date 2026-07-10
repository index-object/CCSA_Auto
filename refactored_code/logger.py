import logging

class Logger:
    def __init__(self, module_name, debug=False):
        self.logger = logging.getLogger(module_name)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # 防止日志传递给根logger（避免重复输出）
        self.logger.propagate = False

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)