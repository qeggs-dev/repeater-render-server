from pydantic import BaseModel, ConfigDict, Field
from ._code_reader import CodeReaderConfig
from ._repeater_traceback import RepeaterTracebackConfig

class GlobalExceptionHandlerConfig(BaseModel):
    model_config = ConfigDict(case_sensitive=False)

    error_message: str = "Internal Server Error"
    critical_error_message: str = "Critical Server Error!"
    crash_exit: bool = True
    traceback_save_to: str | None = None
    record_all_exceptions: bool = False
    error_output_include_traceback: bool = False
    repeater_traceback: RepeaterTracebackConfig = Field(default_factory=RepeaterTracebackConfig)
    code_reader: CodeReaderConfig = Field(default_factory=CodeReaderConfig)
