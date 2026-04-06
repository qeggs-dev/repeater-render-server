import time

from ...._resource import Resource
from .....html_render import (
    RenderConfig,
    NewBrowserContext,
)
from fastapi import (
    HTTPException,
    Request
)
from loguru import logger
from uuid import uuid4
from pathlib import Path
from yarl import URL
from .....global_config_manager import ConfigManager
from .....lifespan import (
    ExitHandler
)
from .....delayed_tasks_pool import DelayedTasksPool
from .._assists import (
    delete_image
)
from .._requests import (
    RenderRequest
)
from .._responses import (
    Render_Response,
    RenderTime
)

delayed_tasks_pool = DelayedTasksPool()
ExitHandler.add_function(delayed_tasks_pool.cancel_all())

@Resource.app.post("/render")
async def render(
    request: Request,
    render_request:RenderRequest
):
    """
    Endpoint for rendering markdown text to image
    """
    start_time = time.monotonic_ns()

    global_configs = ConfigManager.get_configs()

    # 检查请求是否合法
    if not render_request.content:
        raise HTTPException(status_code=400, detail="text is required")
    
    # 生成图片ID
    fuuid = uuid4()
    filename = f"{fuuid}{global_configs.render.output_suffix}"
    render_output_image_dir = Path(global_configs.render.output_dir)

    # 保证输出目录存在
    render_output_image_dir.mkdir(parents=True, exist_ok=True)
    
    if not render_request.image_expiry_time:
        render_url_expiry_time = global_configs.render.default_image_timeout
    else:
        render_url_expiry_time = render_request.image_expiry_time
    
    base_url = render_request.base_url or global_configs.render.base_url
    
    # 日志打印文件名和渲染风格
    logger.info(
        "Rendering image {file_name}",
        file_name = filename
    )

    browser_type = global_configs.render.browser_type

    width = render_request.width if render_request.width is not None else global_configs.render.width
    height = render_request.height if render_request.height is not None else global_configs.render.height
    quality = render_request.quality if render_request.quality is not None else global_configs.render.quality

    end_of_preprocessing = time.monotonic_ns()

    # 生成图片
    result = await Resource.browser_pool_manager.render_html(
        html_content = render_request.content,
        output_path = str(render_output_image_dir / filename),
        browser_type = browser_type,
        config = RenderConfig(
            width = width,
            height = height,
            quality = quality
        ),
        new_context = NewBrowserContext(
            base_url = base_url
        )
    )

    end_of_render = time.monotonic_ns()

    create_ms = time.time_ns() // 10**6
    create = create_ms // 1000
    logger.info(f"Created image {filename}")

    # 添加一个后台任务，时间到后删除图片
    await delayed_tasks_pool.add_task(
        render_url_expiry_time,
        delete_image(
            render_output_image_dir = render_output_image_dir,
            filename = filename
        ),
        id = f"[time: {start_time}] Render Image Timing Deleter"
    )

    # 生成图片的URL
    fileurl = request.url_for("render_file", file_uuid=fuuid)

    return Render_Response(
        image_url = str(fileurl),
        file_uuid = str(fuuid),
        status = result.status,
        browser_used = result.browser_used,
        url_expiry_time = render_url_expiry_time,
        error = result.error,
        content = render_request.content,
        image_render_time_ms = result.render_time_ms,
        created = create,
        created_ms = create_ms,
        details_time = RenderTime(
            preprocess = end_of_preprocessing - start_time,
            render = end_of_render - end_of_render
        )
    )

