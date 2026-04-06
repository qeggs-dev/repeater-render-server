import aiofiles
from pathlib import Path
from datetime import datetime

from ...global_config_manager import ConfigManager

async def save_error_traceback(time: datetime, traceback_str: str):
    """
    Saves the traceback to a file in the traceback_save_to directory

    :param time: The time the error occurred
    :param traceback: The traceback of the error
    :return: None
    """
    base_traceback_save_path = Path(ConfigManager.get_configs().global_exception_handler.traceback_save_to)
    time_str = time.strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"{time_str}.txt"
    file_path = base_traceback_save_path / file_name
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(traceback_str)