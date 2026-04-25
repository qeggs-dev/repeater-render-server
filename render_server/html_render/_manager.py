# html_render/_manager.py
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
    Route,
    Request
)
from ._image_format_detector import ImageFormatDetector
from loguru import logger
from ..lifespan import (
    StartHandler,
    ExitHandler
)


class BrowserPoolManager:
    """
    单浏览器多页面管理器
    每个浏览器类型只有一个实例，但可以有多个页面
    """
    
    _instances: list[BrowserPoolManager] = []
    _is_initialized = False
    
    def __init__(
        self,
        max_pages_per_browser: int = 10,
        default_browser: BrowserType = BrowserType.AUTO,
        headless: bool = True,
        route_blacklist: RegexChecker | None = None,
        browser_context_args: BrowserContextArgs | None = None,
        default_config: RenderConfig | None = None
    ):
        self.max_pages_per_browser: int = max_pages_per_browser
        self.default_browser: BrowserType = default_browser
        self.headless: bool = headless
        self.browser_context_args: BrowserContextArgs = browser_context_args or BrowserContextArgs()
        self.default_config: RenderConfig = default_config or RenderConfig()
        
        # 单浏览器实例存储（每个类型一个）
        self._playwright: Playwright | None = None
        self._browsers: dict[BrowserType, BrowserContext] = {}  # 浏览器实例
        self._browser_types_available: list[BrowserType] = []   # 可用的浏览器类型列表
        
        # 页面池管理（按浏览器区分）
        self._pages: dict[BrowserContext, list[Page]] = {}       # 所有页面
        self._available_pages: dict[BrowserContext, list[Page]] = {}  # 可用页面
        
        self._browser_lock: dict[BrowserType, asyncio.Lock] = {}  # 每个浏览器的锁
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
        
        logger.info(f"BrowserPoolManager (single browser mode) initialized with default browser: {default_browser}")
    
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
            
            # 初始化浏览器类型可用列表
            self._browser_types_available = [
                BrowserType.CHROME,
                BrowserType.MSEDGE,
                BrowserType.CHROMIUM,
                BrowserType.FIREFOX,
                BrowserType.WEBKIT,
            ]
            
            logger.info("Browser pool initialized (single browser mode)")
    
    async def _block_intranet_resources(self, route: Route, request: Request):
        """拦截内网资源"""
        url = request.url
        resource_type = request.resource_type
        
        if self._route_blacklist.check(url, re.match):
            logger.warning(f"Blocked intranet {resource_type}: {url}")
            await route.abort()
            return
        
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
        """渲染HTML为图片"""
        start_time = time.time()
        
        browser_type = browser_type or self.default_browser
        config = config or self.default_config
        
        if kwargs:
            config_dict = config.model_dump()
            config_dict.update(kwargs)
            config = RenderConfig(**config_dict)
        
        detected_format = ImageFormatDetector.detect_format(output_path, image_format)
        final_output_path = ImageFormatDetector.ensure_correct_extension(output_path, detected_format)
        
        logger.info(f"Starting render: format={detected_format.value}, output={final_output_path}")
        
        try:
            browser, page, browser_name = await self._acquire_page_for_render(browser_type)
            
            await page.route("**/*", self._block_intranet_resources)
            await page.set_viewport_size({"width": config.width, "height": config.height})
            await page.set_content(html_content)
            await page.wait_for_load_state("networkidle")
            
            dimensions = await self._get_page_dimensions(page)
            
            screenshot_options = config.to_screenshot_options(detected_format, final_output_path)
            await page.screenshot(**screenshot_options)
            
            render_time_ms = int((time.time() - start_time) * 1000)
            
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
            if "browser" in locals() and "page" in locals():
                await self._release_page(browser, page)
    
    async def _acquire_page_for_render(self, browser_type: BrowserType) -> tuple[BrowserContext, Page, str]:
        """为渲染获取页面"""
        if browser_type == BrowserType.AUTO:
            # 尝试按顺序获取可用浏览器的页面
            for bt in self._browser_types_available:
                try:
                    browser, page = await self._try_acquire_page(bt)
                    return browser, page, bt.value
                except Exception as e:
                    logger.debug(f"Browser {bt} failed: {e}")
                    continue
            
            raise RuntimeError("No browser available")
        else:
            browser, page = await self._try_acquire_page(browser_type)
            return browser, page, browser_type.value
    
    async def _try_acquire_page(self, browser_type: BrowserType) -> tuple[BrowserContext, Page]:
        """尝试获取页面"""
        browser = await self._get_or_create_browser(browser_type)
        
        # 使用浏览器的专用锁
        if browser_type not in self._browser_lock:
            self._browser_lock[browser_type] = asyncio.Lock()
        
        async with self._browser_lock[browser_type]:
            # 检查可用页面
            if browser in self._available_pages and self._available_pages[browser]:
                page = self._available_pages[browser].pop()
                logger.debug(f"Reusing existing page for {browser_type}, available pages left: {len(self._available_pages[browser])}")
                return browser, page
            
            # 创建新页面
            if browser in self._pages and len(self._pages[browser]) < self.max_pages_per_browser:
                page = await browser.new_page()
                self._pages.setdefault(browser, []).append(page)
                logger.debug(f"Created new page for {browser_type}, total pages: {len(self._pages[browser])}/{self.max_pages_per_browser}")
                return browser, page
            
            # 等待可用页面（最多5秒）
            logger.debug(f"Waiting for available page for {browser_type}")
            for _ in range(50):  # 5秒超时
                if browser in self._available_pages and self._available_pages[browser]:
                    page = self._available_pages[browser].pop()
                    return browser, page
                await asyncio.sleep(0.1)
            
            raise RuntimeError(f"No available pages for {browser_type} browser")
    
    async def _get_or_create_browser(self, browser_type: BrowserType) -> BrowserContext:
        """获取或创建浏览器实例"""
        async with self._lock:
            # 如果浏览器已存在，直接返回
            if browser_type in self._browsers:
                return self._browsers[browser_type]
            
            # 创建新浏览器
            browser = await self._create_browser(browser_type)
            self._browsers[browser_type] = browser
            self._pages[browser] = []
            self._available_pages[browser] = []
            
            logger.info(f"Created browser instance for {browser_type}")
            return browser
    
    async def _create_browser(self, browser_type: BrowserType) -> BrowserContext:
        """创建浏览器实例（持久化上下文）"""
        if self._playwright is None:
            await self._initialize()
        
        # 为每个浏览器类型创建独立的用户数据目录
        import tempfile
        import uuid
        user_data_dir = tempfile.mkdtemp(prefix=f"playwright_{browser_type.value}_{uuid.uuid4().hex[:8]}")
        
        # 构建启动参数
        launch_args = self.browser_context_args.model_dump(exclude_none=True)
        
        # 设置用户数据目录
        launch_args["user_data_dir"] = user_data_dir
        
        # 确保 headless 设置
        launch_args["headless"] = self.headless
        
        # 根据浏览器类型选择创建器
        match browser_type:
            case BrowserType.CHROME:
                browser_creator = self._playwright.chromium
                launch_args["channel"] = "chrome"
            case BrowserType.MSEDGE:
                browser_creator = self._playwright.chromium
                launch_args["channel"] = "msedge"
            case BrowserType.CHROMIUM:
                browser_creator = self._playwright.chromium
            case BrowserType.FIREFOX:
                browser_creator = self._playwright.firefox
            case BrowserType.WEBKIT:
                browser_creator = self._playwright.webkit
            case _:
                raise ValueError(f"Unsupported browser type: {browser_type}")
        
        # 移除 None 值
        launch_args = {k: v for k, v in launch_args.items() if v is not None}
        
        browser_context = await browser_creator.launch_persistent_context(**launch_args)
        logger.debug(f"Created new {browser_type} browser with user_data_dir: {user_data_dir}")
        
        return browser_context
    
    async def _release_page(self, browser: BrowserContext, page: Page):
        """释放页面回池中"""
        async with self._lock:
            try:
                # 重置页面状态（清除路由、导航历史等）
                try:
                    # 清除所有路由拦截
                    await page.unroute_all()
                    # 返回 about:blank 以便下次使用
                    await page.goto("about:blank")
                except Exception as e:
                    logger.warning(f"Error resetting page: {e}")
                
                # 将页面放回可用池
                if browser in self._available_pages:
                    self._available_pages[browser].append(page)
                    logger.debug(f"Released page back to pool, available pages: {len(self._available_pages[browser])}")
                else:
                    # 如果浏览器不再存在，关闭页面
                    await page.close()
                    
            except Exception as e:
                logger.warning(f"Error releasing page: {e}")
                # 如果出错，尝试关闭页面
                try:
                    await page.close()
                except:
                    pass
    
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
            total_browsers = len(self._browsers)
            total_pages = sum(len(pages) for pages in self._pages.values())
            available_pages = sum(len(pages) for pages in self._available_pages.values())
            
            browser_type_counts = {}
            for bt, browser in self._browsers.items():
                browser_type_counts[bt.value] = 1
            
            return BrowserStats(
                total_browsers=total_browsers,
                available_browsers=total_browsers,  # 都可用，因为是共享的
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
            for browser, pages in list(self._pages.items()):
                for page in pages[:]:
                    try:
                        await page.close()
                    except Exception as e:
                        logger.warning(f"Error closing page: {e}")
            
            # 关闭所有浏览器
            for browser_type, browser in list(self._browsers.items()):
                try:
                    await browser.close()
                    logger.debug(f"Closed browser: {browser_type}")
                except Exception as e:
                    logger.warning(f"Error closing browser {browser_type}: {e}")
            
            self._browsers.clear()
            self._pages.clear()
            self._available_pages.clear()
            self._browser_lock.clear()
            
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            
            if self in BrowserPoolManager._instances:
                BrowserPoolManager._instances.remove(self)
            
            logger.info("BrowserPoolManager closed")
    
    async def ensure_browser_ready(self, browser_type: BrowserType | None = None) -> bool:
        """确保指定的浏览器已就绪（预热）"""
        bt = browser_type or self.default_browser
        
        if bt == BrowserType.AUTO:
            # 预热所有浏览器
            tasks = [self._get_or_create_browser(btype) for btype in self._browser_types_available]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            logger.info(f"Warmed up {success_count}/{len(tasks)} browsers")
            return success_count > 0
        else:
            try:
                await self._get_or_create_browser(bt)
                return True
            except Exception as e:
                logger.error(f"Failed to warm up browser {bt}: {e}")
                return False
    
    async def __aenter__(self) -> BrowserPoolManager:
        await self._initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()