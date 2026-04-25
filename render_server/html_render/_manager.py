from __future__ import annotations
import asyncio
import time
import re
import tempfile
import shutil
from pathlib import Path
from render_server.regex_checker import RegexChecker
from typing import Any
from ._enums import (
    BrowserType,
    ImageFormat,
    RenderStatus
)
from ._browser_context_args import BrowserContextArgs
from ._browser_stats import BrowserStats
from ._render_config import RenderConfig
from ._render_result import RenderResult
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    ProxySettings,
    Route,
    Request
)
from ._image_format_detector import ImageFormatDetector
from loguru import logger
from ..lifespan import (
    StartHandler,
    ExitHandler
)
from ._new_browser_context import NewBrowserContext


class BrowserPoolManager:
    """
    浏览器管理器 - 使用持久化上下文
    """
    
    _instances: list[BrowserPoolManager] = []
    _is_initialized = False
    
    def __init__(
        self,
        max_pages_per_browser: int = 10,
        max_browsers: int = 3,
        default_browser: BrowserType = BrowserType.AUTO,
        headless: bool = True,
        route_blacklist: RegexChecker | None = None,
        context_args: BrowserContextArgs | None = None,
        default_config: RenderConfig | None = None,
        user_data_dir: str | Path | None = None
    ):
        self.max_pages_per_browser: int = max_pages_per_browser
        self.max_browsers: int = max_browsers
        self.default_browser: BrowserType = default_browser
        self.headless: bool = headless
        self.context_args: BrowserContextArgs = context_args or BrowserContextArgs()
        self.default_config: RenderConfig = default_config or RenderConfig()
        
        # 用户数据目录（用于持久化上下文）
        self.user_data_dir: Path | None = Path(user_data_dir) if user_data_dir else None
        
        # 浏览器池状态 - 存储 BrowserContext 而不是 Browser
        self._playwright: Playwright | None = None
        self._context_pool: dict[BrowserType, list[BrowserContext]] = {}
        self._available_contexts: dict[BrowserType, list[BrowserContext]] = {}
        self._page_pool: dict[BrowserContext, list[Page]] = {}
        self._available_pages: dict[BrowserContext, list[Page]] = {}
        self._context_to_browser_type: dict[BrowserContext, BrowserType] = {}
        self._temp_dirs: list[Path] = []  # 跟踪临时目录以便清理
        self._lock = asyncio.Lock()
        
        # 性能统计
        self._render_count = 0
        self._total_render_time_ms = 0

        # 路由黑名单
        self._route_blacklist: RegexChecker = RegexChecker()
        if route_blacklist is not None:
            self._route_blacklist = route_blacklist
        
        # 注册实例
        BrowserPoolManager._instances.append(self)
        self._register_lifespan_handlers()
        
        logger.info(f"BrowserPoolManager initialized with default browser: {default_browser}")
    
    @classmethod
    def _register_lifespan_handlers(cls):
        """注册生命周期处理器"""
        if not cls._is_initialized:
            StartHandler.add_function(cls._global_startup())
            ExitHandler.add_function(cls._global_shutdown())
            cls._is_initialized = True
            logger.debug("Registered global lifespan handlers")
    
    @classmethod
    async def _global_startup(cls):
        """全局启动"""
        logger.info("Starting browser manager system...")
        for instance in cls._instances:
            if not instance._playwright:
                await instance._initialize()
        logger.info("Browser manager system started")
    
    @classmethod
    async def _global_shutdown(cls):
        """全局关闭"""
        logger.info("Shutting down browser manager system...")
        close_tasks = [
            instance.close() 
            for instance in cls._instances[:]
        ]
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        cls._instances.clear()
        cls._is_initialized = False
        logger.info("Browser manager system shut down")
    
    async def _initialize(self):
        """初始化管理器"""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            logger.debug("Playwright instance created")
            
            for browser_type in BrowserType:
                self._context_pool[browser_type] = []
                self._available_contexts[browser_type] = []
            
            logger.info("Browser context pool initialized")
    
    async def _block_intranet_resources(self, route: Route, request: Request):
        url = request.url
        resource_type = request.resource_type
        
        # 检查是否是允许的地址
        if self._route_blacklist.check(url, re.match):
            logger.warning(f"Blocked intranet {resource_type}: {url}")
            await route.abort()  # 中止请求
            return
        
        # 允许其他请求
        await route.continue_()
    
    async def render_html(
        self,
        html_content: str,
        output_path: str,
        browser_type: BrowserType | None = None,
        image_format: ImageFormat = ImageFormat.AUTO,
        new_context: NewBrowserContext | None = None,
        config: RenderConfig | None = None,
        **kwargs
    ) -> RenderResult:
        """
        渲染HTML为图片
        
        Args:
            html_content: HTML内容
            output_path: 输出路径
            browser_type: 浏览器类型（None使用默认）
            image_format: 图片格式（AUTO自动检测）
            new_context: 新的浏览器上下文配置（None使用默认）
            config: 渲染配置（None使用默认）
            **kwargs: 覆盖config的参数
        
        Returns:
            RenderResult dataclass
        """
        start_time = time.time()
        
        # 解析参数
        browser_type = browser_type or self.default_browser
        config = config or self.default_config
        
        # 应用kwargs覆盖
        if kwargs:
            config_dict = config.model_dump()
            config_dict.update(kwargs)
            config = RenderConfig(**config_dict)
        
        # 检测图片格式
        detected_format = ImageFormatDetector.detect_format(output_path, image_format)
        final_output_path = ImageFormatDetector.ensure_correct_extension(output_path, detected_format)
        
        logger.info(f"Starting render: format={detected_format.value}, output={final_output_path}")
        
        # 执行渲染
        try:
            context, page, browser_name = await self._acquire_page_for_render(browser_type, new_context)

            # 创建路由拦截
            await page.route("**/*", self._block_intranet_resources)
            
            # 配置页面
            await page.set_viewport_size({"width": config.width, "height": config.height})
            await page.set_content(html_content)
            await page.wait_for_load_state("networkidle")
            
            # 获取实际渲染尺寸
            dimensions = await self._get_page_dimensions(page)
            
            # 截图
            screenshot_options = config.to_screenshot_options(detected_format, final_output_path)
            await page.screenshot(**screenshot_options)
            
            render_time_ms = int((time.time() - start_time) * 1000)
            
            # 更新统计
            self._render_count += 1
            self._total_render_time_ms += render_time_ms
            
            logger.success(f"Render completed in {render_time_ms}ms")
            
            return RenderResult(
                status=RenderStatus.SUCCESS,
                output_path=final_output_path,
                browser_used=browser_name,
                image_format=detected_format,
                dimensions=dimensions,
                render_time_ms=render_time_ms,
                config_used=config
            )
            
        except Exception as e:
            render_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Render failed after {render_time_ms}ms: {e}")
            
            return RenderResult(
                status=RenderStatus.FAILED,
                output_path=final_output_path,
                error=str(e),
                render_time_ms=render_time_ms,
                config_used=config
            )
        
        finally:
            # 确保页面和上下文被释放
            if "context" in locals() and "page" in locals():
                await self._release_page(context, page)
    
    async def _acquire_page_for_render(
        self, 
        browser_type: BrowserType, 
        new_context: NewBrowserContext | None = None
    ) -> tuple[BrowserContext, Page, str]:
        """为渲染获取页面和上下文"""
        if browser_type == BrowserType.AUTO:
            # 尝试所有浏览器
            browser_types = [
                BrowserType.CHROME,
                BrowserType.MSEDGE,
                BrowserType.CHROMIUM,
                BrowserType.FIREFOX,
                BrowserType.WEBKIT,
            ]
            
            for bt in browser_types:
                try:
                    context, page = await self._try_acquire_page(bt, new_context)
                    return context, page, bt.value
                except Exception as e:
                    logger.debug(f"Browser {bt} failed: {e}")
                    continue
            
            raise RuntimeError("No browser available")
        else:
            # 使用指定浏览器
            context, page = await self._try_acquire_page(browser_type, new_context)
            return context, page, browser_type.value
    
    async def _try_acquire_page(
        self, 
        browser_type: BrowserType, 
        new_context: NewBrowserContext | None = None
    ) -> tuple[BrowserContext, Page]:
        """尝试获取页面和上下文"""
        context = await self._acquire_context(browser_type, new_context)
        
        async with self._lock:
            # 检查可用页面
            if self._available_pages.get(context):
                page = self._available_pages[context].pop()
                return context, page
            
            # 创建新页面
            if len(self._page_pool.get(context, [])) < self.max_pages_per_browser:
                page = await context.new_page()
                self._page_pool.setdefault(context, []).append(page)
                return context, page
            
            raise RuntimeError("Context page limit reached")
    
    async def _acquire_context(
        self, 
        browser_type: BrowserType, 
        new_context: NewBrowserContext | None = None
    ) -> BrowserContext:
        """获取浏览器上下文（使用 launch_persistent_context）"""
        if self._playwright is None:
            await self._initialize()
        
        async with self._lock:
            # 如果有可用的上下文且不需要新建特殊上下文，直接返回
            if new_context is None and self._available_contexts.get(browser_type):
                return self._available_contexts[browser_type].pop()
            
            # 检查是否可创建新上下文
            if len(self._context_pool.get(browser_type, [])) < self.max_browsers:
                context = await self._create_context(browser_type, new_context)
                self._context_pool.setdefault(browser_type, []).append(context)
                self._context_to_browser_type[context] = browser_type
                return context
            
            raise RuntimeError(f"No available {browser_type} contexts")
    
    def _get_user_data_dir(self, browser_type: BrowserType) -> Path:
        """获取用户数据目录"""
        if self.user_data_dir:
            # 为不同浏览器类型创建子目录
            return self.user_data_dir / browser_type.value
        else:
            # 创建临时目录
            temp_dir = Path(tempfile.mkdtemp(prefix=f"playwright_{browser_type.value}_"))
            self._temp_dirs.append(temp_dir)
            return temp_dir
    
    async def _create_context(
        self, 
        browser_type: BrowserType, 
        new_context: NewBrowserContext | None = None
    ) -> BrowserContext:
        """创建浏览器上下文（使用 launch_persistent_context）"""
        # 获取浏览器启动器
        match browser_type:
            case BrowserType.CHROME:
                browser_creator = self._playwright.chromium
                channel = "chrome"
            case BrowserType.MSEDGE:
                browser_creator = self._playwright.chromium
                channel = "msedge"
            case BrowserType.CHROMIUM:
                browser_creator = self._playwright.chromium
                channel = None
            case BrowserType.FIREFOX:
                browser_creator = self._playwright.firefox
                channel = None
            case BrowserType.WEBKIT:
                browser_creator = self._playwright.webkit
                channel = None
            case _:
                raise ValueError(f"Unsupported browser type: {browser_type}")
        
        # 获取用户数据目录
        user_data_dir = self._get_user_data_dir(browser_type)
        
        # 构建 launch_persistent_context 参数
        launch_args = self.context_args.model_dump(exclude_none=True)
        
        # 设置 channel（如果指定了）
        if channel:
            launch_args["channel"] = channel
        
        # 覆盖 new_context 参数（如果提供了）
        if new_context:
            new_context_dict = new_context.model_dump(exclude_none=True)
            launch_args.update(new_context_dict)
        
        # 设置 headless
        launch_args["headless"] = self.headless
        
        # 启动持久化上下文
        context = await browser_creator.launch_persistent_context(
            user_data_dir,
            **launch_args
        )
        
        # 初始化池
        self._page_pool[context] = []
        self._available_pages[context] = []
        
        logger.debug(f"Created new persistent context for {browser_type} at {user_data_dir}")
        return context
    
    async def _release_page(self, context: BrowserContext, page: Page):
        """释放页面"""
        async with self._lock:
            try:
                await page.close()
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
            
            # 清理池
            if context in self._page_pool and page in self._page_pool[context]:
                self._page_pool[context].remove(page)
            
            if context in self._available_pages and page in self._available_pages[context]:
                self._available_pages[context].remove(page)
            
            # 如果上下文没有页面了，释放上下文回池中
            if context in self._page_pool and not self._page_pool[context]:
                browser_type = self._context_to_browser_type.get(context)
                if browser_type and context not in self._available_contexts.get(browser_type, []):
                    self._available_contexts.setdefault(browser_type, []).append(context)
    
    async def _get_page_dimensions(self, page: Page) -> dict[str, int]:
        """获取页面实际渲染尺寸"""
        return await page.evaluate("""
            () => {
                const body = document.body;
                const html = document.documentElement;
                
                return {
                    width: Math.max(
                        body.scrollWidth, body.offsetWidth,
                        html.clientWidth, html.scrollWidth, html.offsetWidth
                    ),
                    height: Math.max(
                        body.scrollHeight, body.offsetHeight,
                        html.clientHeight, html.scrollHeight, html.offsetHeight
                    ),
                    viewportWidth: window.innerWidth,
                    viewportHeight: window.innerHeight
                };
            }
        """)
    
    async def get_stats(self) -> BrowserStats:
        """获取统计信息"""
        async with self._lock:
            total_contexts = sum(len(contexts) for contexts in self._context_pool.values())
            available_contexts = sum(len(contexts) for contexts in self._available_contexts.values())
            total_pages = sum(len(pages) for pages in self._page_pool.values())
            available_pages = sum(len(pages) for pages in self._available_pages.values())
            
            browser_type_counts = {
                btype.value: len(contexts) 
                for btype, contexts in self._context_pool.items()
                if contexts
            }
            
            return BrowserStats(
                total_browsers=total_contexts,
                available_browsers=available_contexts,
                total_pages=total_pages,
                available_pages=available_pages,
                browser_type_counts=browser_type_counts
            )
    
    def get_render_stats(self) -> dict[str, Any]:
        """获取渲染统计"""
        avg_time = (self._total_render_time_ms / self._render_count 
                   if self._render_count > 0 else 0)
        
        return {
            "total_renders": self._render_count,
            "total_render_time_ms": self._total_render_time_ms,
            "average_render_time_ms": avg_time,
        }
    
    async def close(self):
        """关闭管理器"""
        async with self._lock:
            logger.info("Closing BrowserPoolManager...")
            
            # 关闭所有页面
            for context, pages in list(self._page_pool.items()):
                for page in pages[:]:
                    try:
                        await page.close()
                    except Exception as e:
                        logger.warning(f"Error closing page: {e}")
            
            # 关闭所有上下文
            for browser_type, contexts in list(self._context_pool.items()):
                for context in contexts[:]:
                    try:
                        await context.close()
                    except Exception as e:
                        logger.warning(f"Error closing context: {e}")
            
            # 清理池
            self._context_pool.clear()
            self._available_contexts.clear()
            self._page_pool.clear()
            self._available_pages.clear()
            self._context_to_browser_type.clear()
            
            # 清理临时目录
            for temp_dir in self._temp_dirs:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.debug(f"Removed temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to remove temp directory {temp_dir}: {e}")
            self._temp_dirs.clear()
            
            # 停止Playwright
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            
            # 移除实例
            if self in BrowserPoolManager._instances:
                BrowserPoolManager._instances.remove(self)
            
            logger.info("BrowserPoolManager closed")
    
    async def __aenter__(self) -> BrowserPoolManager:
        await self._initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()