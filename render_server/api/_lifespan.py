from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import AsyncIterator
from ..lifespan import StartHandler, ExitHandler

# 定义生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await StartHandler.execute()
    yield
    await ExitHandler.execute()