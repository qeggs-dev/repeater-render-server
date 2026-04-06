from __future__ import annotations
import asyncio
from typing import Coroutine

class StartHandler:
    _functions: asyncio.Queue[Coroutine[None, None, None]] = asyncio.Queue()
    _instance: StartHandler | None = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def execute(cls):
        while not cls._functions.empty():
            func = await cls._functions.get()
            await func
    
    @classmethod
    def add_function(cls, func: Coroutine[None, None, None], *args, **kwargs):
        if not asyncio.iscoroutine(func):
            raise TypeError("Function must be a coroutine")
        cls._functions.put_nowait(
            func
        )