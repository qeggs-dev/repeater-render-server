import os
from pathlib import Path

def validate_path(
        base_path: str | os.PathLike,
        new_path: str | os.PathLike,
        embed:bool = True,
        allow_symlinks: bool = False,
        verify_original_path_exists: bool = False
    ) -> bool:
    """
    验证路径是否合法

    :param base_path: 基础路径
    :param new_path: 新路径
    :param embed: 是否嵌入基础路径
    :param allow_symlinks: 是否允许符号链接
    :param verify_original_path_exists: 是否验证原始路径是否存在
    :return: 是否合法
    """
    # 转换为Path对象以便于操作
    base = Path(base_path)
    new = Path(new_path)

    if allow_symlinks:
        # 允许符号链接
        base = base.resolve()
    else:
        # 禁用符号链接
        base = base.absolute()
    
    if embed:
        # 获取基础路径的绝对路径
        requested_path = (base / new).absolute()
    else:
        requested_path = new.absolute()
    
    if verify_original_path_exists:
        # 验证原始路径是否是存在的路径
        if not base.exists():
            return False
        if not requested_path.exists():
            return False
    
    # 检查路径是否在base_path的子目录内
    return requested_path.is_relative_to(base)