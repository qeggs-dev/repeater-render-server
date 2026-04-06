from pydantic import BaseModel, ConfigDict
from ._enums import ImageFormat
from typing import Any

class RenderConfig(BaseModel):
    """渲染配置"""
    model_config = ConfigDict(
        validate_assignment=True
    )

    width: int = 1200
    height: int = 800
    full_page: bool = True
    quality: int = 90
    timeout: int = 30000
    omit_background: bool = False
    
    def to_screenshot_options(self, format: ImageFormat, path: str) -> dict[str, Any]:
        """转换为Playwright截图选项"""
        options = {
            "path": path,
            "full_page": self.full_page,
            "timeout": self.timeout,
            "omit_background": self.omit_background,
        }
        
        # 设置图片格式和质量
        if format != ImageFormat.PNG:
            options["type"] = format.value
        
        if format in [ImageFormat.JPEG, ImageFormat.WEBP]:
            options["quality"] = min(max(self.quality, 1), 100)
        
        return options