from __future__ import annotations

import os
import yaml
import shutil
import orjson

from box import Box
from pathlib import Path
from typing import ClassVar, Generator, Iterable

from ._base_model import Global_Config

class ConfigManager:
    _configs: ClassVar[Global_Config] = Global_Config()
    _instance: ClassVar[ConfigManager] | None = None
    _base_path: ClassVar[Path] = Path("./configs/project_configs")
    _force_load_list: ClassVar[list[Path]] = []

    @classmethod
    def get_configs(cls) -> Global_Config:
        return cls._configs

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def update_base_path(cls, path: str | os.PathLike, force_load_list: list[str | os.PathLike] | None = None) -> None:
        cls._base_path = Path(path)
        if isinstance(force_load_list, list):
            cls._force_load_list = [Path(f) for f in force_load_list]
        else:
            cls._force_load_list = []
    
    @classmethod
    def _scan_dir(cls, globs: Iterable[str], temp_loadpath: Path | None = None) -> Generator[Path, None, None]:
        if temp_loadpath is None:
            load_path = cls._base_path
        else:
            load_path = temp_loadpath
        for glob in globs:
            for path in load_path.rglob(glob):
                yield path
    
    @classmethod
    def _config_files(cls, temp_loadpath: Path | None = None) -> list[Path]:
        return sorted(
            cls._scan_dir(
                [
                    "*.yaml",
                    "*.yml",
                    "*.json",
                ],
                temp_loadpath
            ),
            key=lambda path: str(path)
        )
    
    @staticmethod
    def _load_yaml(path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def _load_json(path: Path) -> dict:
        with open(path, "rb") as f:
            return orjson.loads(f.read())
    
    @classmethod
    def load(cls, create_if_missing: bool = False, temp_loadpath: str | os.PathLike | None = None) -> Global_Config:
        """
        Load the configs from the config files.

        :param use_cache: If True, use the cached config, otherwise reload the config
        """
        try:
            if cls._force_load_list:
                load_list: list[Path] = cls._force_load_list
            elif temp_loadpath is not None:
                load_list: list[Path] = cls._config_files(Path(temp_loadpath))
            else:
                load_list: list[Path] = cls._config_files()
            
            configs: list[Box] = []
            for path in load_list:
                if path.suffix in [".yaml", ".yml"]:
                    configs.append(Box(cls._load_yaml(path)))
                elif path.suffix == ".json":
                    configs.append(Box(cls._load_json(path)))
            
            if not configs:
                cls._configs = Global_Config()
                if create_if_missing:
                    cls.save(cls._configs)
                    return cls._configs
            
            base_config = configs[0]
            for config in configs[1:]:
                base_config.merge_update(config)
            
            merge_config = base_config.to_dict()
            cls._configs = Global_Config(**merge_config)
            return cls._configs
        except Exception as e:
            if create_if_missing:
                cls.save(cls._configs)
                return cls._configs
            else:
                raise
    
    @staticmethod
    def _dump_yaml(path: Path, data: Global_Config) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(
                yaml.safe_dump(
                    data.model_dump(),
                    allow_unicode=True,
                    sort_keys=False
                )
            )
    
    @staticmethod
    def _dump_json(path: Path, data: Global_Config) -> None:
        with open(path, "wb") as f:
            f.write(
                orjson.dumps(
                    data.model_dump()
                )
            )
    
    @classmethod
    def save(cls, config: Global_Config | None = None, filename: str | os.PathLike = "config.json") -> None:
        """
        Save the config to the config files.
        
        :param config: The config to save
        """
        if config is None:
            config = cls._configs
        if cls._base_path.exists():
            shutil.rmtree(cls._base_path)
        cls._base_path.mkdir(parents=True, exist_ok=True)
        config_file_path = cls._base_path / filename
        if config_file_path.suffix in [".yaml", ".yml"]:
            cls._dump_yaml(config_file_path, config)
        elif config_file_path.suffix == ".json":
            cls._dump_json(config_file_path, config)
            