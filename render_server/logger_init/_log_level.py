from ..global_config_manager import LogLevel as ConfigLogLevel
from enum import IntEnum

class LogLevel(IntEnum):
    """Logger log levels."""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

def config_to_log_level(config_level: ConfigLogLevel) -> LogLevel:
    """Converts a config log level to a log level."""
    match config_level:
        case ConfigLogLevel.TRACE:
            return LogLevel.TRACE
        case ConfigLogLevel.DEBUG:
            return LogLevel.DEBUG
        case ConfigLogLevel.INFO:
            return LogLevel.INFO
        case ConfigLogLevel.SUCCESS:
            return LogLevel.SUCCESS
        case ConfigLogLevel.WARNING:
            return LogLevel.WARNING
        case ConfigLogLevel.ERROR:
            return LogLevel.ERROR
        case ConfigLogLevel.CRITICAL:
            return LogLevel.CRITICAL

def log_level_to_config(log_level: LogLevel) -> ConfigLogLevel:
    """Converts a log level to a config log level."""
    match log_level:
        case LogLevel.TRACE:
            return ConfigLogLevel.TRACE
        case LogLevel.DEBUG:
            return ConfigLogLevel.DEBUG
        case LogLevel.INFO:
            return ConfigLogLevel.INFO
        case LogLevel.SUCCESS:
            return ConfigLogLevel.SUCCESS
        case LogLevel.WARNING:
            return ConfigLogLevel.WARNING
        case LogLevel.ERROR:
            return ConfigLogLevel.ERROR
        case LogLevel.CRITICAL:
            return ConfigLogLevel.CRITICAL