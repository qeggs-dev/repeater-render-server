from __future__ import annotations
import asyncio
import time
import re
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
    浏览器管理器
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
        browser_context_args: BrowserContextArgs | None = None,
        default_config: RenderConfig | None = None
    ):
        self.max_pages_per_browser: int = max_pages_per_browser
        self.max_browsers: int = max_browsers
        self.default_browser: BrowserType = default_browser
        self.headless: bool = headless
        self.browser_args: BrowserContextArgs = browser_context_args or {}
        self.default_config: RenderConfig = default_config or RenderConfig()
        
        # 浏览器池状态
        self._playwright: Playwright | None = None
        self._browser_pool: dict[BrowserType, list[BrowserContext]] = {}
        self._available_browsers: dict[BrowserType, list[BrowserContext]] = {}
        self._page_pool: dict[BrowserContext, list[Page]] = {}
        self._available_pages: dict[BrowserContext, list[Page]] = {}
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
                self._browser_pool[browser_type] = []
                self._available_browsers[browser_type] = []
            
            logger.info("Browser pool initialized")
    
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
            browser, page, browser_name = await self._acquire_page_for_render(browser_type)

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
            # 确保页面和浏览器被释放
            if "browser" in locals() and "page" in locals():
                await self._release_page(browser, page)
  
    async def _acquire_page_for_render(self, browser_type: BrowserType) -> tuple[BrowserContext, Page, str]:
        """为渲染获取页面"""
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
                    browser, page = await self._try_acquire_page(bt)
                    return browser, page, bt.value
                except Exception as e:
                    logger.debug(f"Browser {bt} failed: {e}")
                    continue
            
            raise RuntimeError("No browser available")
        else:
            # 使用指定浏览器
            browser, page = await self._try_acquire_page(browser_type)
            return browser, page, browser_type.value
    
    async def _try_acquire_page(self, browser_type: BrowserType) -> tuple[BrowserContext, Page]:
        """尝试获取页面"""
        browser_context = await self._acquire_browser(browser_type)
        
        async with self._lock:
            # 检查可用页面
            if self._available_pages.get(browser_context):
                page = self._available_pages[browser_context].pop()
                return browser_context, page
            
            # 创建新页面
            if len(self._page_pool.get(browser_context, [])) < self.max_pages_per_browser:
                page = await browser_context.new_page()
                self._page_pool.setdefault(browser_context, []).append(page)
                return browser_context, page
            
            raise RuntimeError("Browser page limit reached")
    
    async def _acquire_browser(self, browser_type: BrowserType) -> BrowserContext:
        """获取浏览器"""
        if self._playwright is None:
            await self._initialize()
        
        async with self._lock:
            # 检查可用浏览器
            if self._available_browsers.get(browser_type):
                return self._available_browsers[browser_type].pop()
            
            # 检查是否可创建新浏览器
            if len(self._browser_pool.get(browser_type, [])) < self.max_browsers:
                browser_context = await self._get_browser_context(browser_type)
                self._browser_pool.setdefault(browser_type, []).append(browser_context)
                return browser_context
            
            raise RuntimeError(f"No available {browser_type} browsers")
    
    async def _get_browser_context(self, browser_type: BrowserType) -> BrowserContext:
        """创建浏览器"""
        match browser_type:
            case BrowserType.CHROME:
                browser_creator = self._playwright.chromium
                launch_args = {"channel": "chrome", **self.browser_args.model_dump(exclude_none=True)}
            case BrowserType.MSEDGE:
                browser_creator = self._playwright.chromium
                launch_args = {"channel": "msedge", **self.browser_args.model_dump(exclude_none=True)}
            case BrowserType.CHROMIUM:
                browser_creator = self._playwright.chromium
                launch_args = self.browser_args.model_dump(exclude_none=True)
            case BrowserType.FIREFOX:
                browser_creator = self._playwright.firefox
                launch_args = self.browser_args.model_dump(exclude_none=True)
            case BrowserType.WEBKIT:
                browser_creator = self._playwright.webkit
                launch_args = self.browser_args.model_dump(exclude_none=True)
            case _:
                raise ValueError(f"Unsupported browser type: {browser_type}")
        
        launch_args["headless"] = self.headless
        browser_context = await browser_creator.launch_persistent_context(**launch_args)
        
        # 初始化池
        self._page_pool[browser_context] = []
        self._available_pages[browser_context] = []
        
        logger.debug(f"Created new {browser_type} browser")
        return browser_context
    
    async def _release_page(self, browser: BrowserContext, page: Page):
        """释放页面"""
        async with self._lock:
            try:
                await page.close()
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
            
            # 清理池
            if browser in self._page_pool and page in self._page_pool[browser]:
                self._page_pool[browser].remove(page)
            
            if browser in self._available_pages and page in self._available_pages[browser]:
                self._available_pages[browser].remove(page)
            
            # 如果浏览器没有页面了，释放浏览器
            if browser in self._page_pool and not self._page_pool[browser]:
                # 找到浏览器类型
                for btype, browsers in self._browser_pool.items():
                    if browser in browsers and browser not in self._available_browsers[btype]:
                        self._available_browsers[btype].append(browser)
                        break
    
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
            total_browsers = sum(len(browsers) for browsers in self._browser_pool.values())
            available_browsers = sum(len(browsers) for browsers in self._available_browsers.values())
            total_pages = sum(len(pages) for pages in self._page_pool.values())
            available_pages = sum(len(pages) for pages in self._available_pages.values())
            
            browser_type_counts = {
                btype.value: len(browsers) 
                for btype, browsers in self._browser_pool.items()
                if browsers
            }
            
            return BrowserStats(
                total_browsers=total_browsers,
                available_browsers=available_browsers,
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
            for browser, pages in list(self._page_pool.items()):
                for page in pages[:]:
                    try:
                        await page.close()
                    except Exception as e:
                        logger.warning(f"Error closing page: {e}")
            
            # 关闭所有浏览器
            for browser_type, browsers in list(self._browser_pool.items()):
                for browser in browsers[:]:
                    try:
                        await browser.close()
                    except Exception as e:
                        logger.warning(f"Error closing browser: {e}")
            
            # 清理池
            self._browser_pool.clear()
            self._available_browsers.clear()
            self._page_pool.clear()
            self._available_pages.clear()
            
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