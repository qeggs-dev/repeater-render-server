from loguru import logger
import asyncio
import inspect
import signal
import os

from ...special_exception import CriticalException

async def shutdown_server(exception: CriticalException | None = None) -> None:
    wait_time: float = 0.0
    if isinstance(exception, CriticalException):
        if callable(exception.wait):
            logger.info(
                "Exceptions include waiting callbacks, and programs may exit delayed..."
            )
            
            if inspect.iscoroutinefunction(exception.wait):
                wait_time = await exception.wait(exception)
            elif callable(exception.wait):
                wait_time: float = await asyncio.to_thread(exception.wait, exception)
            elif not isinstance(wait_time, float):
                wait_time = exception.wait
            else:
                logger.error(
                    "The wait handler is invalid.",
                )
        elif isinstance(exception.wait, float):
            wait_time: float = exception.wait
    
    if (isinstance(wait_time, float) or isinstance(wait_time, int)) and wait_time > 0:
        logger.info(
            "Waiting for {wait_time} seconds before closing the application...",
            wait_time = wait_time
        )
        await asyncio.sleep(wait_time)

    logger.critical("The server crashed! exiting...")
    # 发送 SIGTERM 信号终止进程
    os.kill(os.getpid(), signal.SIGTERM)