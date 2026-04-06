from pydantic import BaseModel

class RenderRequest(BaseModel):
    content: str
    image_expiry_time: float | None = None
    width: int | None = None
    height: int | None = None
    quality: int | None = None
    base_url: str | None = None