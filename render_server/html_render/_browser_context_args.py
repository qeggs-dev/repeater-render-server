from pathlib import Path
from typing import Any, Sequence, Pattern
from pydantic import BaseModel, ConfigDict
from ._proxy_settings import ProxySettings
from ._assist_models import (
    ViewportSize,
    Geolocation,
    HttpCredentials,
    ColorScheme,
    ReducedMotion,
    ForcedColors,
    Contrast,
    ServiceWorkers,
    RecordHarMode,
    ReclodeHarContent,
    ClientCertificate
)

class BrowserContextArgs(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True
    )

    user_data_dir: str | Path | None = None
    channel: str | None = None
    executable_path: Path | str | None = None
    args: Sequence[str] | None = None
    ignore_default_args: bool | Sequence[str] = None
    handle_sigint: bool | None = None
    handle_sigterm: bool | None = None
    handle_sighup: bool | None = None
    timeout: float | None = None
    env: dict[str, str | float | bool] | None = None
    headless: bool | None = None
    proxy: ProxySettings | None = None
    downloads_path: Path | str | None = None
    slow_mo: float | None = None
    viewport: ViewportSize | None = None
    screen: ViewportSize | None = None
    no_viewport: bool | None = None
    ignore_https_errors: bool | None = None
    java_script_enabled: bool | None = None
    bypass_csp: bool | None = None
    user_agent: str | None = None
    locale: str | None = None
    timezone_id: str | None = None
    geolocation: Geolocation | None = None
    permissions: Sequence[str] | None = None
    extra_http_headers: dict[str, str] | None = None
    offline: bool | None = None
    http_credentials: HttpCredentials | None = None
    device_scale_factor: float | None = None
    is_mobile: bool | None = None
    has_touch: bool | None = None
    color_scheme: ColorScheme | None = None
    reduced_motion: ReducedMotion | None = None
    forced_colors: ForcedColors | None = None
    contrast: Contrast | None = None
    accept_downloads: bool | None = None
    traces_dir: Path | str | None = None
    chromium_sandbox: bool | None = None
    firefox_user_prefs: dict[str, str | float | bool] | None = None
    record_har_path: Path | str | None = None
    record_har_omit_content: bool | None = None
    record_video_dir: Path | str | None = None
    record_video_size: ViewportSize | None = None
    base_url: str | None = None
    strict_selectors: bool | None = None
    service_workers: ServiceWorkers | None = None
    record_har_url_filter: Pattern[str] | str | None = None
    record_har_mode: RecordHarMode | None = None
    record_har_content: ReclodeHarContent | None = None
    client_certificates: list[ClientCertificate] | None = None