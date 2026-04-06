import sys
import logging
from pathlib import Path
from loguru import logger
from ._intercept_handler import InterceptHandler
from ..global_config_manager import LoggerConfig

def logger_init(config: LoggerConfig):
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)

    # 移除其他日志处理器
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # 移除默认处理器
    logger.remove()
    # 添加自定义处理器
    logger.add(
        sys.stderr,
        format = config.console_format,
        filter = lambda record: "donot_send_console" not in record["extra"],
        level = config.level.value
    )

    
    log_file = Path(config.file_path)

    if not log_file.parent.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        format = config.file_format,
        level = config.level.value,
        enqueue = True,
        delay = True,
        rotation = config.rotation,
        retention = config.retention,
        compression = config.compression,
    )