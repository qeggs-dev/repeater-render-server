import os
from ._loader import ConfigManager
from ._base_model import Global_Config

def get_config(config_dir: str | os.PathLike) -> Global_Config:
    loader = ConfigManager()
    return loader.load(temp_loadpath = config_dir)