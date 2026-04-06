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
    extensions: list[str] = [
        "extra",
        "sane_lists",
        "admonition",
        "codehilite",
        "nl2br"
    ]
    allowed_tags: list[str] = [
        "p", "br", "strong", "em", "u", "del", "ins",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "ul", "ol", "li",
        "a", "img",
        "code", "pre", "blockquote",
        "table", "thead", "tbody", "tr", "th", "td",
    ]
    allowed_attrs: dict[str, list[str]] = {
        "a": ["href", "title", "rel"],
        "img": ["src", "alt", "title"],
        "code": ["class"],
        "pre": ["class"],
    }
    allowed_protocols: list[str] = ["http", "https", "mailto"]