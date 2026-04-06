import aiofiles

from os import PathLike, get_terminal_size
from ...global_config_manager import ConfigManager

class GetCode:
    def __init__(
            self,
            file_path: str | PathLike,
            line: int,
            end_line: int | None = None,
            column: int | None = None,
            end_column: int | None = None,

            dilation: int | None = None,
            with_numbers: bool | None = None,
            reserve_space: int | None = None,
            fill_char: str | None = None,
            add_bottom_border: bool | None = None,
            bottom_border_limit: int | None = None,
        ):
        self._file_path: str | PathLike = file_path

        self._line: int = line
        if end_line is None:
            self._end_line: int = line
        else:
            self._end_line: int = end_line
        
        self._column: int | None = column
        self._end_column: int | None = end_column

        if fill_char is None:
            self._fill_char: str = ConfigManager.get_configs().global_exception_handler.code_reader.fill_char
        else:
            self._fill_char: str = fill_char
        
        if dilation is None:
            self._dilation = ConfigManager.get_configs().global_exception_handler.code_reader.code_line_dilation
        else:
            self._dilation = dilation
        
        if with_numbers is None:
            self._with_numbers: bool = ConfigManager.get_configs().global_exception_handler.code_reader.with_numbers
        else:
            self._with_numbers: bool = with_numbers
        
        if reserve_space is None:
            self._reserve_space: int = ConfigManager.get_configs().global_exception_handler.code_reader.reserve_space
        else:
            self._reserve_space: int = reserve_space
        
        if add_bottom_border is None:
            self._add_bottom_border: bool = ConfigManager.get_configs().global_exception_handler.code_reader.add_bottom_border
        else:
            self._add_bottom_border: bool = add_bottom_border

        if bottom_border_limit is None:
            self._bottom_border_limit: int = ConfigManager.get_configs().global_exception_handler.code_reader.bottom_border_limit
        else:
            self._bottom_border_limit: int = bottom_border_limit

    async def get_code_async(self) -> str:
        text_buffer: list[str] = []
        max_length: int = 0
        add_bottom_border = self._add_bottom_border
        async with aiofiles.open(
            self._file_path,
            mode="r",
            encoding=ConfigManager.get_configs().global_exception_handler.code_reader.code_encoding
        ) as f:
            index: int = 1
            async for line in f:
                max_length = max(max_length, len(line))
                processed_text = self._get_line_text(
                    text=line,
                    index=index,
                )
                if isinstance(processed_text, str):
                    text_buffer.append(processed_text)
                if index == self._line and not (self._column is None and self._end_column is None):
                    text_buffer.append(self._get_columns_pointer_line())
                if (index - self._end_line) > self._dilation:
                    add_bottom_border = False
                    break
                index += 1
        
        if not text_buffer:
            return ""
        if add_bottom_border:
            text_buffer.append(self._get_last_line(max_length = max_length))
        return "\n".join(text_buffer)
                    
    def get_code(self) -> str:
        text_buffer: list[str] = []
        max_length: int = 0
        add_bottom_border = self._add_bottom_border
        with open(
            self._file_path,
            mode="r",
            encoding=ConfigManager.get_configs().global_exception_handler.code_reader.code_encoding
        ) as f:
            for index, line in enumerate(f, start=1):
                max_length = max(max_length, len(line))
                processed_text = self._get_line_text(
                    text=line,
                    index=index,
                )
                if isinstance(processed_text, str):
                    text_buffer.append(processed_text)
                if index == self._line and not (self._column is None and self._end_column is None):
                    text_buffer.append(self._get_columns_pointer_line())
                if (index - self._end_line) > self._dilation:
                    add_bottom_border = False
                    break
        
        if not text_buffer:
            return ""
        if add_bottom_border:
            text_buffer.append(self._get_last_line(max_length = max_length))
        return "\n".join(text_buffer)
    
    def _get_columns_pointer_line(self):
        spaces = self._fill_char * self._reserve_space
        
        if self._column is None and self._end_column is None:
            raise ValueError("Column is None")
        elif self._column is None:
            pointer_offset_space = ""
            pointer_text = "^" * self._end_column
        elif self._end_column is None:
            pointer_offset_space = " " * self._column
            pointer_text = "^~"
        else:
            pointer_offset_space = " " * self._column
            pointer_text = "^" * self._end_column

        text = f"│{spaces}│ {pointer_offset_space}{pointer_text}"
        return text
    
    def _get_line_text(
            self,
            text: str,
            index: int,
        ) -> str | None:
        text = text.strip("\n")
        if abs(index - self._line) <= self._dilation:
            if self._with_numbers:
                index_char = str(index).rjust(self._reserve_space, self._fill_char)
                if self._end_line >= index >= self._line:
                    if index_char.startswith(self._fill_char):
                        index_char = f">{index_char[1:]}"
                    else:
                        index_char = f">{index_char}"
                return f"│{index_char}│ {text}"
            else:
                return text
        return None
    
    def _get_last_line(self, max_length: int) -> str:
        text_buffer: list[str] = []
        
        text_buffer.append("└")

        for i in range(self._reserve_space):
            text_buffer.append("─")

        if self._bottom_border_limit is not None:
            bottom_border_limit = self._bottom_border_limit
        else:
            bottom_border_limit = get_terminal_size().columns - self._reserve_space - 2
        
        if bottom_border_limit > 0:
            text_buffer.append("┴")
        else:
            text_buffer.append("┘")
        
        for i in range(min(bottom_border_limit, max_length)):
            text_buffer.append("─")

        return "".join(text_buffer)