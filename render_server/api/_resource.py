# ==== 标准库 ==== #
from __future__ import annotations

from typing import ClassVar, Sequence, Callable, Any
from pathlib import Path

# ==== 第三方库 ==== #
import uvicorn

from fastapi import FastAPI

# ==== 自定义库 ==== #
from ..global_config_manager import ConfigManager
from ..html_render import (
    BrowserPoolManager,
    BrowserContextArgs,
)
from ..logger_init import logger_init
from ..regex_checker import RegexChecker
from ._lifespan import lifespan
from .._info import __version__

class Resource:
    startup: ClassVar[Sequence[Callable[[], Any]] | None] = None
    shutdown: ClassVar[Sequence[Callable[[], Any]]] | None = None
    
    app: ClassVar[FastAPI] = FastAPI(
        title = "Repeater Render Server",
        lifespan = lifespan,
        on_startup = startup,
        on_shutdown = shutdown,
        version = __version__
    )
    browser_pool_manager: ClassVar[BrowserPoolManager | None] = None
    _instance: ClassVar[Resource | None] = None

    @classmethod
    def inited(cls):
        if cls.browser_pool_manager is None:
            return False
        return True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def init_all(cls):
        cls.init_logger()
        cls.init_browser_pool_manager()
    
    @classmethod
    def init_logger(cls):
        # 初始化日志
        logger_init(
            ConfigManager.get_configs().logger,
        )

    @classmethod
    def init_browser_pool_manager(cls):
        # 渲染配置
        render_config = ConfigManager.get_configs().render
        route_blacklist_file = Path(render_config.route_blacklist_file)
        route_blacklist = RegexChecker()
        if route_blacklist_file.exists():
            with open(route_blacklist_file, "r", encoding="utf-8") as f:
                file_content = f.read()
                route_blacklist.load(file_content)
        cls.browser_pool_manager = BrowserPoolManager(
            max_pages_per_browser = render_config.max_pages_per_browser,
            max_browsers = render_config.max_browsers,
            default_browser = render_config.browser_type,
            headless = render_config.headless,
            route_blacklist = route_blacklist,
            browser_context_args = BrowserContextArgs(
                executable_path = render_config.browser_executable_path,
                base_url = render_config.base_url,
                user_data_dir = render_config.browser_user_data_dir
            )
        )

    @classmethod
    def run_server(
        cls,
        host: str,
        port: int,
        workers: int = 1,
        reload: bool = False
    ) -> None:
        if not cls.inited():
            raise RuntimeError("API not initialized")
        uvicorn.run(
            app = cls.app,
            host = host,
            port = port,
            workers = workers,
            reload = reload,
            log_config = None,
        )