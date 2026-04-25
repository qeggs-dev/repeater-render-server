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