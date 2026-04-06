from enum import StrEnum

class BrowserType(StrEnum):
    """支持的浏览器类型"""
    AUTO = "auto"
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"
    CHROME = "chrome"
    MSEDGE = "msedge"