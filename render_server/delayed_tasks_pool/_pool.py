import asyncio
from typing import TypeVar
from collections.abc import Coroutine
from loguru import logger

T = TypeVar("T")

class DelayedTasksPool:
    def __init__(self):
        self.tasks: set[asyncio.Task] = set()
    
    async def _task_warper(self, sleep_time: int | float, task: Coroutine[None, None, T], id: str | None = None) -> T:
        if id is None:
            id = task.__qualname__
        logger.trace(
            "Adding task to pool: \"{id}\"",
            id = id
        )
        try:
            logger.trace(
                "Task \"{id}\" will be executed after {sleep_time} seconds",
                id = id,
                sleep_time = sleep_time
            )
            await asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            logger.trace(
                "Task \"{id}\" cancelled",
                id = id
            )
            pass
        finally:
            logger.trace(
                "Task \"{id}\" is being executed",
                id = id
            )
            result = await task
        
        return result

    async def add_task(self, sleep_time: float, task: Coroutine[None, None, T], id: str | None = None):
        """Add task to the pool"""
        self.tasks.add(
            asyncio.create_task(
                self._task_warper(
                    sleep_time = sleep_time,
                    task = task,
                    id = id
                )
            )
        )

    async def wait_all(self):
        """Wait for all tasks in the pool to complete"""
        await asyncio.gather(*self.tasks)
        self.tasks.clear()

    async def cancel_all(self, wait: bool = True):
        """Cancel all tasks in the pool"""
        for task in self.tasks:
            task.cancel()
            if wait:
                await task
        self.tasks.clear()
    
    async def close(self):
        """Close the pool"""
        await self.cancel_all()