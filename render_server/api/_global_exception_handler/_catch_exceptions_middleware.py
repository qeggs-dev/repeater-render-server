from fastapi.responses import Response
from fastapi import Request
from typing import Callable, Awaitable

from .._resource import Resource
from ...global_config_manager import ConfigManager
from ._except_handler import (
    exception_handler,
    WarningHandler
)

# 初始化警告处理器
warning_handler = WarningHandler()
warning_handler.inject()

@Resource.app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]):
    try:
        return await call_next(request)
    except Exception as e:
        return await exception_handler(e)
    except BaseException as e:
        if ConfigManager().get_configs().global_exception_handler.record_all_exceptions:
            await exception_handler(e)
        raise