from enum import StrEnum

class ImageFormat(StrEnum):
    """支持的图片格式"""
    AUTO = "auto"
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"