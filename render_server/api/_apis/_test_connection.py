from .._resource import Resource
from fastapi.responses import PlainTextResponse

@Resource.app.get("/connected")
def test_connection():
    return PlainTextResponse("OK")