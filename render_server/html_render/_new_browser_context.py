from pydantic import BaseModel
from pathlib import Path
from typing import Sequence, Pattern
from ._proxy_settings import ProxySettings
from enum import StrEnum

class ColorScheme(StrEnum):
    DARK = "dark"
    LIGHT = "light"
    NO_PREFERENCE = "no-preference"
    NULL = "null"

class ReducedMotion(StrEnum):
    NO_PREFERENCE = "no-preference"
    NULL = "null"
    REDUCE = "reduce"

class ForcedColors(StrEnum):
    ACTIVE = "active"
    NONE = "none"
    NULL = "null"

class Contrast(StrEnum):
    MORE = "more"
    NO_PREFERENCE = "no-preference"
    NULL = "null"

class ServiceWorkers(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"

class RecordHarMode(StrEnum):
    FULL = "full"
    MINIMAL = "minimal"

class ReclodeHarContent(StrEnum):
    ATTACH = "attach"
    EMBED = "embed"
    OMIT = "omit"

class HttpCredentialsSend(StrEnum):
    ALWAYS = "always"
    UNAUTHORIZED = "unauthorized"

class StorageStateCookieSameSite(StrEnum):
    LAX = "lax"
    NONE = "None"
    STRICT = "Strict"

class ViewportSize(BaseModel):
    width: int
    height: int

class Geolocation(BaseModel):
    latitude: float
    longitude: float
    accuracy: float | None = None

class HttpCredentials(BaseModel):
    username: str
    password: str
    origin: str
    send: HttpCredentialsSend

class StorageStateCookie(BaseModel):
    name: str
    value: str
    domain: str
    path: str
    expires: float
    httpOnly: bool
    secure: bool
    sameSite: StorageStateCookieSameSite

class LocalStorageEntry(BaseModel):
    name: str
    value: str

class OriginState(BaseModel):
    origin: str
    localStorage: list[LocalStorageEntry]

class StorageState(BaseModel):
    cookies: list[StorageStateCookie]
    origins: list[OriginState]

class ClientCertificate(BaseModel):
    origin: str
    certPath: str | Path | None = None
    cert: bytes | None = None
    keyPath: str | Path | None = None
    key: bytes | None = None
    pfxPath: str | Path | None = None
    pfx: bytes | None = None
    passphrase: str | None = None

class NewBrowserContext(BaseModel):
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
    default_browser_type: str | None = None
    proxy: ProxySettings | None = None
    record_har_path: Path | str | None = None
    record_har_omit_content: bool | None = None
    record_video_dir: Path | str | None = None
    record_video_size: ViewportSize | None = None
    storage_state: StorageState | str | Path | None = None
    base_url: str | None = None
    strict_selectors: bool | None = None
    service_workers: ServiceWorkers | None = None
    record_har_url_filter: Pattern[str] | str | None = None
    record_har_mode: RecordHarMode | None = None
    record_har_content: ReclodeHarContent | None = None
    client_certificates: list[ClientCertificate] | None = None