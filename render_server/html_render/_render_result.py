from pydantic import BaseModel, Field, ConfigDict
from ._enums import RenderStatus, ImageFormat
from ._render_config import RenderConfig

class RenderResult(BaseModel):
    """渲染结果"""
    model_config = ConfigDict(
        validate_assignment=True
    )
    
    status: RenderStatus
    output_path: str
    browser_used: str | None = None
    image_format: ImageFormat | None = None
    dimensions: dict[str, int | None] = Field(default_factory=dict)
    error: str | None = None
    render_time_ms: int | None = None
    config_used: RenderConfig | None = None
    
    @property
    def success(self) -> bool:
        return self.status == RenderStatus.SUCCESS
    
    @property
    def width(self) -> int | None:
        return self.dimensions.get("width") if self.dimensions else None
    
    @property
    def height(self) -> int | None:
        return self.dimensions.get("height") if self.dimensions else None
    
    def __str__(self) -> str:
        if self.success:
            return f"RenderResult(status={self.status}, output={self.output_path}, browser={self.browser_used})"
        return f"RenderResult(status={self.status}, error={self.error})"