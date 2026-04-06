from pydantic import BaseModel, ConfigDict
from ._log_level import LogLevel
from ._log_compression import CompressionMode

class LoggerConfig(BaseModel):
    model_config = ConfigDict(case_sensitive=False)

    file_path: str = "./logs/repeater-render-server-log-{time:YYYY-MM-DD_HH-mm-ss.SSS}.log"
    level: LogLevel = LogLevel.DEBUG
    rotation: str = "1 days"
    retention: str = "7 days"
    console_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    file_format: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}"
    compression: CompressionMode | None = CompressionMode.ZIP