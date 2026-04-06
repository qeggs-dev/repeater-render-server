from pydantic import BaseModel, ConfigDict, Field
from ....html_render import BrowserType

class RenderConfig(BaseModel):
    model_config = ConfigDict(case_sensitive=False)

    default_image_timeout: float = 60.0

    width: int = 1200
    height: int = 600
    quality: int = 90
    output_suffix: str = ".png"
    output_dir: str = "./workspace/rendered_images"
    route_blacklist_file: str = "./configs/blacklist.regex"
    base_url: str | None = None
    browser_type: BrowserType = BrowserType.AUTO
    browser_executable_path: str | None = None
    max_pages_per_browser: int = 10
    max_browsers: int = 10
    headless: bool = True
    allowed_protocols: list[str] = ["http", "https", "mailto"]