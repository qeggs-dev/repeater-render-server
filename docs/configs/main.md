# Main Configs

用于告诉服务器应该如何运行的配置文件

推荐配置
``` json
{
    "render": {

        // 浏览器类型
        "browser_type": "auto",

        // 除非你为 Playwright 配置了专属浏览器
        // 否则建议你定义这个为你已经安装的浏览器
        "browser_executable_path": ""
    },

    // 你需要配置这个，否则服务器将不知道自己如何启动
    "server": {

        // 监听的地址，建议不要公开在公网
        "host": "127.0.0.1",

        // 监听的端口
        "port": 8080
    }
}
```

全部配置
``` json
{
    // 全局异常处理器
    "global_exception_handler": {
        // 未指定时，默认的错误信息
        "error_message": "Internal Server Error",
        
        // 未指定时使用的严重错误信息
        "critical_error_message": "Critical Server Error!",

        // 崩溃时是否退出程序
        "crash_exit": true,

        // 自动保存错误信息到指定文件
        "traceback_save_to": null,

        // 记录所有异常（包括 Python 自己抛出的）
        "record_all_exceptions": false,

        // 在 Response 中输出 Traceback
        "error_output_include_traceback": false,

        // Repeater Traceback 配置
        "repeater_traceback": {
            // 启用 Repeater Traceback
            "enable": true,

            // 时间格式化字符串
            "timeformat": "%Y-%m-%d %H:%M:%S",

            // 是否排除库代码
            "exclude_library_code": true,

            // 是否格式化 Pydantic 验证错误
            "format_validation_error": true,

            // 是否记录 Warning
            "record_warnings": true,

            // 是否使用传统堆栈帧
            "traditional_stack_frame": true
        },

        // Code Reader 配置
        "code_reader": {
            // 启用 Code Reader
            "enable": true,

            // 源代码编码
            "code_encoding": "utf-8",

            // 向上下两个方向扩展读取的最大源代码行数
            "code_line_dilation": 3,

            // 源代码携带行数显示
            "with_numbers": true,

            // 携带行数时左侧保留的空格数
            "reserve_space": 5,

            // 携带行数时左侧填充字符
            "fill_char": " ",

            // 添加底部边框
            "add_bottom_border": true,

            // 底部边框上限
            "bottom_border_limit": null
        }
    },

    // 日志配置
    "logger": {
        // 日志文件路径
        "file_path": "./logs/repeater-render-server-log-{time:YYYY-MM-DD_HH-mm-ss.SSS}.log",

        // 日志等级
        "level": "DEBUG",

        // 日志轮转
        "rotation": "1 days",

        // 日志保留
        "retention": "7 days",

        // 控制台日志格式
        "console_format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",

        // 文件日志格式
        "file_format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",

        // 日志压缩格式
        "compression": "zip"
    },

    // 渲染配置
    "render": {
        // 默认图片超时时间
        "default_image_timeout": 60.0,

        // 图片宽度
        "width": 1200,

        // 图片高度
        "height": 600,

        // 图片质量
        "quality": 90,

        // 图片后缀
        "output_suffix": ".png",

        // 图片输出目录
        "output_dir": "./workspace/rendered_images",

        // 路由黑名单文件
        "route_blacklist_file": "./configs/blacklist.regex",

        // 基础URL
        "base_url": null,

        // 浏览器类型
        // 支持："auto", "chromium", "firefox", "webkit", "chrome", "msedge"
        "browser_type": "auto",

        // 浏览器路径
        "browser_executable_path": null,

        // Markdown 配置
        "max_pages_per_browser": 10,
        
        // 最大浏览器数量
        "max_browsers": 10,

        // 是否无头模式
        "headless": true,

        // 允许包含的通信协议
        "allowed_protocols": [
            "http",
            "https",
            "mailto"
        ]
    },

    // 服务器配置
    "server": {
        // 服务器主机
        "host": "127.0.0.1",

        // 服务器端口
        "port": 8080
    }
}
```