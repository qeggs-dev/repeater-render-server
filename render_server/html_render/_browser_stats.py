from pydantic import BaseModel, Field, ConfigDict

class BrowserStats(BaseModel):
    """浏览器池统计信息"""
    model_config = ConfigDict(
        validate_assignment=True
    )

    total_browsers: int = 0
    available_browsers: int = 0
    total_pages: int = 0
    available_pages: int = 0
    browser_type_counts: dict[str, int] = Field(default_factory=dict)
    
    def __str__(self) -> str:
        return (
            f"Browsers: {self.available_browsers}/{self.total_browsers} available | "
            f"Pages: {self.available_pages}/{self.total_pages} available"
        )