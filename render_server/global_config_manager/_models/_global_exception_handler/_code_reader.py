from pydantic import BaseModel, ConfigDict, Field

class CodeReaderConfig(BaseModel):
    model_config = ConfigDict(case_sensitive=False)

    enable: bool = True
    code_encoding: str = "utf-8"
    code_line_dilation: int = Field(3, ge=0)
    with_numbers: bool = True
    reserve_space: int = Field(5, ge=0)
    fill_char: str = " "
    add_bottom_border: bool = True
    bottom_border_limit: int | None = Field(None, ge=0)