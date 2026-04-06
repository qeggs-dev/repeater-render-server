import sys
import time
import asyncio
import traceback

from loguru import logger
from datetime import datetime
from fastapi.responses import JSONResponse

from ....special_exception import CriticalException, HTTPException
from ....global_config_manager import ConfigManager
from .._shutdown_server import shutdown_server
from .._save_error_traceback import save_error_traceback
from .._error_output_model import ErrorResponse
from ._traceback import format_traceback

async def exception_handler(error: BaseException) -> JSONResponse:
    error_time = time.time_ns()

    error_code = 500
    exception_message = str(error)
    extra_data = None

    # 判断是否为特殊Exception
    if isinstance(error, CriticalException):
        is_critical_exception: bool = True
    else:
        is_critical_exception: bool = False
    
    if isinstance(error, HTTPException):
        error_code = error.status_code
        extra_data = error.detail
        is_http_exception: bool = True
    else:
        is_http_exception: bool = False

    if ConfigManager.get_configs().global_exception_handler.repeater_traceback.enable:
        traceback_str = await format_traceback(
            time.strftime(
                ConfigManager.get_configs().global_exception_handler.repeater_traceback.timeformat,
                time.localtime(error_time / 1e9)
            ),
            ConfigManager.get_configs().global_exception_handler.repeater_traceback.exclude_library_code,
            ConfigManager.get_configs().global_exception_handler.code_reader.enable,
            ConfigManager.get_configs().global_exception_handler.repeater_traceback.traditional_stack_frame,
            ConfigManager.get_configs().global_exception_handler.repeater_traceback.format_validation_error
        )
    else:
        traceback_str = traceback.format_exc()

    # 记录异常日志
    if is_critical_exception:
        logger.critical(
            (
                "Critical Exception:\n"
                "{traceback}"
            ),
            traceback = traceback_str,
        )
    else:
        logger.exception(
            (
                "Exception: \n"
                "{traceback}"
            ),
            traceback = traceback_str
        )

    
    # 记录Traceback
    if ConfigManager.get_configs().global_exception_handler.traceback_save_to:
        await save_error_traceback(
            datetime.fromtimestamp(error_time / 1e9),
            traceback_str
        )
    
    # 判断是否要关闭服务器
    if is_critical_exception:
        if ConfigManager.get_configs().global_exception_handler.crash_exit:
            asyncio.create_task(shutdown_server(error))
        else:
            logger.critical(
                "A critical error has occurred on the server, but the server has not been allowed to go down!",
            )
    
    error_response = ErrorResponse(
        error_code = error_code,
        timestamp_ns = error_time,
        unix_timestamp = error_time // 1_000_000_000,
        source_exception = type(error).__name__,
        exception_message = exception_message,
        extra_body = extra_data
    )
    if is_critical_exception:
        error_response.error_message = ConfigManager.get_configs().global_exception_handler.critical_error_message
    elif is_http_exception:
        error_response.error_message = error.message
    else:
        error_response.error_message = ConfigManager.get_configs().global_exception_handler.error_message
    
    if ConfigManager.get_configs().global_exception_handler.error_output_include_traceback:
        error_response.exception_traceback = traceback_str

    return JSONResponse(
        status_code=error_response.error_code,
        content=error_response.model_dump(exclude_none=True)
    )