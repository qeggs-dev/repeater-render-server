import os
import mimetypes
from pathlib import Path
from loguru import logger
from ._enums import ImageFormat

class ImageFormatDetector:
    """图片格式检测器"""
    
    # 文件扩展名到格式的映射
    EXTENSION_MAP = {
        ".png": ImageFormat.PNG,
        ".jpg": ImageFormat.JPEG,
        ".jpeg": ImageFormat.JPEG,
        ".jfif": ImageFormat.JPEG,
        ".webp": ImageFormat.WEBP,
        ".bmp": ImageFormat.PNG,  # BMP转换为PNG
        ".gif": ImageFormat.PNG,  # GIF转换为PNG
        ".tiff": ImageFormat.PNG,  # TIFF转换为PNG
    }
    
    # MIME类型到格式的映射
    MIME_MAP = {
        "image/png": ImageFormat.PNG,
        "image/jpeg": ImageFormat.JPEG,
        "image/jpg": ImageFormat.JPEG,
        "image/webp": ImageFormat.WEBP,
        "image/bmp": ImageFormat.PNG,
        "image/gif": ImageFormat.PNG,
        "image/tiff": ImageFormat.PNG,
    }
    
    @classmethod
    def detect_format(
            cls,
            output_path:str | os.PathLike, 
            requested_format: ImageFormat = ImageFormat.AUTO
        ) -> ImageFormat:
        """
        检测图片格式，优先级：
        1. 如果指定了具体格式，使用它
        2. 根据文件扩展名检测
        3. 根据MIME类型检测
        4. 默认使用PNG
        """
        # 如果指定了具体格式（非AUTO）
        if requested_format != ImageFormat.AUTO:
            return requested_format
        
        path = Path(output_path)
        
        # 根据扩展名检测
        ext = path.suffix.lower()
        if ext in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[ext]
        
        # 根据MIME类型检测
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type and mime_type in cls.MIME_MAP:
            return cls.MIME_MAP[mime_type]
        
        # 默认使用PNG
        logger.warning(f"Could not detect image format for \"{output_path}\", defaulting to PNG")
        return ImageFormat.PNG
    
    @classmethod
    def ensure_correct_extension(
            cls,
            output_path: str, 
            image_format: ImageFormat
        ) -> str:
        """确保文件扩展名与格式匹配"""
        path = Path(output_path)
        
        # 获取正确的扩展名
        format_extensions = {
            ImageFormat.PNG: ".png",
            ImageFormat.JPEG: ".jpg",
            ImageFormat.WEBP: ".webp",
        }
        
        correct_ext = format_extensions.get(image_format, ".png")
        
        # 如果扩展名不正确，修正它
        if path.suffix.lower() != correct_ext:
            new_path = path.with_suffix(correct_ext)
            logger.info(f"Corrected file extension: {path.name} -> {new_path.name}")
            return str(new_path)
        
        return str(path)