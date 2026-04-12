from .._resource import Resource
from fastapi.responses import PlainTextResponse

@Resource.app.get("/alived")
def alived():
    return PlainTextResponse("OK")