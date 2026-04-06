import re

class SanitizeFilename:
    def __init__(
            self,
            pattern: str = r"[^\w\d\-_]"
        ) -> None:
        self._pattern = re.compile(pattern, re.UNICODE)
    
    @property
    def pattern(self) -> str:
        return self._pattern.pattern
    
    @pattern.setter
    def pattern(self, pattern: str) -> None:
        self._pattern = re.compile(pattern)

    def sanitize_filename(
            self,
            text: str
        ) -> str:
        """
        转义文件名中的非法字符，提供安全的字符串路径注入转义

        :param text: 任意字符串
        :return: 符合文件名格式的字符串
        """
        return self._pattern.sub("_" , text)

_sanitize_filename = SanitizeFilename()
sanitize_filename = _sanitize_filename.sanitize_filename
_sanitize_filename_with_dir = SanitizeFilename(r"[^\d\w\-_/\\]")
sanitize_filename_with_dir = _sanitize_filename_with_dir.sanitize_filename


# 示例用法
if __name__ == "__main__":
    # 测试文件名转义和缩短
    test_filename = "my/illegal:file?.name*with<long>path.txt"
    print(sanitize_filename(test_filename, prefix="doc"))  # 输出: doc_my_illegal_file_name_with_long_path_txt