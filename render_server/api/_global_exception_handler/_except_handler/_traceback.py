import os
import sys
import json
import traceback

from .._get_code import GetCode
from pathlib import Path
from typing import Generator
from pydantic import ValidationError

def is_library_code(filename: str | os.PathLike):
    if not filename:
        return True
    
    file_path = Path(filename)
    file_name_str = str(filename)
    
    stdlib_dirs: list[str] = [
        sys.prefix,
        sys.base_prefix,
    ]
    stdlib_dirs: list[Path] = [Path(dir) for dir in stdlib_dirs]
    for dir in stdlib_dirs.copy():
        stdlib_dirs.append(dir / "lib")
    
    for lib_dir in stdlib_dirs:
        if file_path.is_relative_to(lib_dir):
            return True
    
    for path in sys.path:
        if "site-packages" in path and file_name_str.startswith(path):
            return True
        if "dist-packages" in path and file_name_str.startswith(path):
            return True
    
    if file_name_str.startswith("<") and file_name_str.endswith(">"):
        return True
    
    return False

def format_stack_frame(frames: traceback.StackSummary, exclude_library: bool = False) -> Generator[str, None, None]:
    for index, frame in enumerate(frames):
        file_path = Path(frame.filename)
        if is_library_code(file_path):
            frame_flag = "Library Code"
            if exclude_library:
                yield f"[{index}] Frame ({frame_flag}): {file_path.as_posix()}:{frame.lineno}"
                continue
        else:
            frame_flag = "App Code"
        
        yield f"[{index}] Frame ({frame_flag}): {file_path.as_posix()}:{frame.lineno}"
        yield f"    - Function: {frame.name}"
        yield f"    - Line: {frame.lineno} ~ {frame.end_lineno}"
        yield f"    - Columns: {frame.colno} ~ {frame.end_colno}"
        yield f"    - Locals:"
        indented_locals = json.dumps(frame.locals, indent=4, ensure_ascii=False).replace("\n", "\n" + " " * 8)
        yield f"        {indented_locals}"


async def format_traceback(
            time_str: str,
            exclude_library: bool = False,
            enable_code_reader: bool = False,
            traditional_stack_frame: bool = False,
            format_validation_error: bool = False,
        ):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    frames = traceback.extract_tb(exc_traceback)
    last_frame = frames[-1]
    last_code_frame: traceback.FrameSummary | None = None
    for frame in reversed(frames):
        if not is_library_code(frame.filename):
            last_code_frame = frame
            break
    total_frame_depth = len(frames)
    raiser = Path(last_frame.filename)
    line_start = last_frame.lineno
    line_end = last_frame.end_lineno
    column_start = last_frame.colno
    column_end = last_frame.end_colno
    error_name = exc_value.__class__.__name__

    if format_validation_error and isinstance(exc_value, ValidationError):
        text_buffer: list[str] = []
        errors = exc_value.errors()
        for error in errors:
            text_buffer.append(f"{'.'.join(error['loc'])} - {error['msg']}")
        message = "\n".join(text_buffer)
    else:
        message = str(exc_value)

    indented_message = message.replace("\n", "\n" + " " * 8)
    if traditional_stack_frame:
        traceback_str = traceback.format_exc()
    else:
        traceback_str = "\n".join(format_stack_frame(frames, exclude_library))
    indented_traceback = traceback_str.replace("\n", "\n" + " " * 8)

    if enable_code_reader:
        if raiser.exists() and raiser.is_file() and last_code_frame.lineno is not None and last_code_frame.lineno > 0:
            get_code = GetCode(
                raiser,
                last_code_frame.lineno,
                last_code_frame.end_lineno,
                last_code_frame.colno,
                last_code_frame.end_colno
            )
            try:
                code = await get_code.get_code_async()
            except Exception as e:
                code = f"[Get Code Error: {e}]"
        else:
            code = "[Invalid Code Frame]"
    else:
        code = "[Code Reader Disabled]"
    
    format_text = (
        f"{error_name}\n"
        "    - Time:\n"
        f"        {time_str}\n"
        "    - Depth of stack frame:\n"
        f"        {total_frame_depth}\n"
        "    - Raised from:\n"
        f"        {raiser.as_posix()}:{line_start}:{column_start}\n"
        "    - Line Range:\n"
        f"        {line_start} ~ {line_end}\n"
        "    - Column Range:\n"
        f"        {column_start} ~ {column_end}\n"
        "    - Message: \n"
        f"        {indented_message}\n"
        "    - Traceback: \n"
        f"        {indented_traceback}\n"
    )
    if enable_code_reader:
        format_text += (
            "File Context: \n"
            f"{code}\n"
        )
    
    format_text += f"\n{error_name}:\n{message}\n"
    
    return format_text
    