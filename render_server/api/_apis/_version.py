from .._resource import Resource
from ..._info import __version__ as __core_version__
from fastapi.responses import (
    PlainTextResponse
)
from pydantic import BaseModel

class Versions(BaseModel):
    core: str = __core_version__

@Resource.app.get("/version")
async def version():
    """
    Return the version of the API and the core
    """
    return Versions()

@Resource.app.get("/version/{module}")
async def module_version(module: str):
    """
    Return the version of the specified module
    """
    dumped = Versions().model_dump()
    if module in dumped:
        return PlainTextResponse(dumped[module])
    else:
        return PlainTextResponse(
            "Module not found",
            status_code = 404
        )
