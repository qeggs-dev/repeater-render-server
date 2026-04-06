import warnings

from typing import TextIO
from loguru import logger
from datetime import datetime
from pathlib import Path

from ....global_config_manager import ConfigManager
from .._get_code import GetCode

class WarningHandler:
    """Warning Handler"""
    def __init__(self) -> None:
        self.raw_showwarning = warnings.showwarning
    
    def inject(self) -> None:
        warnings.showwarning = self.warning_handler
    
    def recovery(self) -> None:
        warnings.showwarning = self.raw_showwarning
    
    def warning_handler(
            self,
            message: Warning | str,
            category: type[Warning],
            filename: str,
            lineno: int,
            file: TextIO | None = None,
            line: str | None = None
        ) -> None:
        if ConfigManager().get_configs().global_exception_handler.repeater_traceback.record_warnings:
            warning_time = datetime.now()
            file_path = Path(filename)

            if ConfigManager().get_configs().global_exception_handler.code_reader.enable:
                if file_path.exists() and file_path.is_file() and lineno > 0:
                    get_code = GetCode(file_path, lineno)
                    try:
                        code = get_code.get_code()
                    except Exception as e:
                        code = f"[Get Code Error: {e}]"
                else:
                    code = "[Invalid Code Frame]"
            else:
                code = "[Code Reader Disabled]"

            # 记录异常日志
            logger.warning(
                (
                    "Warning: \n"
                    "{warning_name}\n"
                    "    - Raised from:\n"
                    "        {raiser}:{lineno}\n"
                    "    - Message: \n"
                    "        {message}\n"
                    "File: \n"
                    "{code}"
                ),
                warning_name = category.__name__,
                message = message,
                raiser = file_path.as_posix(),
                lineno = lineno,
                code = code
            )
        else:
            self.raw_showwarning(
                message = message,
                category = category,
                filename = filename,
                lineno = lineno,
                file = file,
                line = line
            )