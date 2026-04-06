from pydantic import BaseModel
from playwright.async_api import ProxySettings as PlaywrightProxySettings

class ProxySettings(BaseModel):
    server: str
    bypass: str | None = None
    username: str | None = None
    password: str | None = None

    def to_playwright_proxy_settings(self) -> PlaywrightProxySettings:
        return PlaywrightProxySettings(
            server = self.server,
            bypass = self.bypass,
            username = self.username,
            password = self.password,
        )