from pydantic import BaseModel, ConfigDict, Field
from .....html_render import RenderStatus

class RenderTime(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True
    )

    preprocess: int | None = None
    render: int | None = None


class Render_Response(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True
    )

    image_url: str | None = None
    file_uuid: str | None = None
    status: RenderStatus | None = None
    browser_used: str | None = None
    url_expiry_time: float | None = None
    error: str | None = None
    content: str | None = None
    image_render_time_ms: float | None = None
    created: int | None = None
    created_ms: int | None = None
    details_time: RenderTime | None = None