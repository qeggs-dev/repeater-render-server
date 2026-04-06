import time

from pydantic import BaseModel, ConfigDict, Field
from typing import Any

class ErrorResponse(BaseModel):
    """
    Error Output Model
    """
    model_config = ConfigDict(
        validate_assignment=True
    )

    error_message: str = "Internal Server Error"
    timestamp_ns: int = Field(default_factory=lambda: time.time_ns())
    unix_timestamp: int = Field(default_factory=lambda: time.time_ns() // 10**9)
    error_code: int = 500
    source_exception: str = ""
    exception_message: str = ""
    extra_body: Any | None = None
    exception_traceback: str | None = None