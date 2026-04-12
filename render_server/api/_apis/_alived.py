from .._resource import Resource
from fastapi.responses import PlainTextResponse

@Resource.app.get("/alive")
def alive():
    return PlainTextResponse("OK")