from pathlib import Path
from typing import Any, Sequence
from pydantic import BaseModel, ConfigDict
from ._proxy_settings import ProxySettings

class BrowserArgs(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True
    )

    executable_path: Path | str | None = None
    channel: str | None = None
    args: Sequence[str] | None = None
    ignore_default_args: bool | Sequence[str] | None = None
    handle_sigint: bool | None = None
    handle_sigterm: bool | None = None
    handle_sighup: bool | None = None
    timeout: float | None = None
    env: dict[str, str | float | bool] | None = None
    headless: bool | None = None
    devtools: bool | None = None
    proxy: ProxySettings | None = None
    downloads_path: Path | str | None = None
    slow_mo: float | None = None
    traces_dir: Path | str | None = None
    chromium_sandbox: bool | None = None
    firefox_user_prefs: dict[str, str | float | bool] | None = None