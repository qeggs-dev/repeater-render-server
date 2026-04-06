from typing import Any
from pydantic import BaseModel

class HTTPErrorDetail(BaseModel):
    status_code: int = 500
    message: str = "Internal Server Error"
    extra_data: Any = None

class HTTPException(Exception):
    def __init__(self, status_code: int = 500, message: str = "Internal Server Error", extra_data: Any = None):
        self.detail = HTTPErrorDetail(
            status_code=status_code,
            message=message,
            extra_data=extra_data
        )
        super().__init__(message)
    
    @property
    def status_code(self):
        return self.detail.status_code
    
    @property
    def message(self):
        return self.detail.message
    
    @property
    def extra_data(self):
        return self.detail.extra_data
    
    def __str__(self):
        return f"{self.__class__.__name__} ({self.status_code}): {self.message}"