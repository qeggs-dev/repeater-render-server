import logging
from loguru import logger

class InterceptHandler(logging.Handler):
    def __init__(self, level: int | str = logging.NOTSET, extra_fields:dict | None = None):
        super().__init__(level)
        self.extra_fields = extra_fields or {}

    def emit(self, record: logging.LogRecord):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # 找到调用者
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        # 创建带有额外字段的绑定logger
        bound_logger = logger.bind(**self.extra_fields)
        bound_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )