import asyncio
from loguru import logger
from pathlib import Path

async def delete_image(render_output_image_dir: Path, filename: str):
    """
    删除图片
    """
    await asyncio.to_thread((render_output_image_dir / filename).unlink)
    logger.info("Deleted image {filename}", filename = filename)