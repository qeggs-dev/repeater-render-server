from pydantic import BaseModel, ConfigDict, Field
from ._models import *

class Global_Config(BaseModel):
    model_config = ConfigDict(case_sensitive=False)

    global_exception_handler: GlobalExceptionHandlerConfig = Field(default_factory=GlobalExceptionHandlerConfig)
    logger: LoggerConfig = Field(default_factory=LoggerConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)