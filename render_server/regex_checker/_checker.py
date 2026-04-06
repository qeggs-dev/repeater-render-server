import re
from pathlib import Path
from typing import (
    Iterator,
    Callable,
)
from ._obj import (
    CheckDetailsData,
    LoaderDetailsData,
    CheckerMode
)

class RegexChecker:
    """
    **RegexChecker**

    A multi-pattern single data matching module
    """
    def __init__(self, flags: int | re.RegexFlag = 0):
        """
        :param flags: The regex flags to use
        """
        self._mode: CheckerMode = CheckerMode.SERIES
        self._regexs: list[tuple[re.Pattern, bool]] = []
        self._flags = flags

    def check(self, text: str, func: Callable[[str | re.Pattern[str], str, int | re.RegexFlag], re.Match[str] | None] = re.search) -> CheckDetailsData:
        r"""
        Check the text with the regexs.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> if regex_checker.check("test@example.com"):
            ...     print("Matched")
            ... else:
            ...     print("Not matched")
            Matched


        :param text: The text to check.
        :param func: The function to use to check the text.
        :return: True if the text matches all the regexs, False otherwise.
        """
        if not self._regexs:
            return CheckDetailsData(regex=None, matched=False)
        
        if self._mode == CheckerMode.SERIES:
            for regex, enable in self._regexs:
                if enable and not func(regex, text, self._flags):
                    return CheckDetailsData(regex=regex, matched=False)
            return CheckDetailsData(regex=None, matched=True)
        elif self._mode == CheckerMode.PARALLEL:
            for regex, enable in self._regexs:
                if enable and func(regex, text, self._flags):
                    return CheckDetailsData(regex=regex, matched=True)
            return CheckDetailsData(regex=None, matched=False)
    
    def full_check(self, text: str) -> CheckDetailsData:
        r"""
        Check the text with the regexs.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> if regex_checker.full_check("test@example.com"):
            ...     print("Matched")
            ... else:
            ...     print("Not matched")
            Matched

        :param text: The text to check.
        :return: True if the text matches all the regexs, False otherwise.
        """
        if not self._regexs:
            return CheckDetailsData(regex=None, matched=False)
        
        if self._mode == CheckerMode.SERIES:
            for regex, enable in self._regexs:
                if enable and not regex.findall(text):
                    return CheckDetailsData(regex=regex, matched=False)
            return CheckDetailsData(regex=None, matched=True)
        elif self._mode == CheckerMode.PARALLEL:
            for regex, enable in self._regexs:
                if enable and regex.findall(text):
                    return CheckDetailsData(regex=regex, matched=True)
            return CheckDetailsData(regex=None, matched=False)
        
    
    def check_all(self, texts: list[str]) -> list[CheckDetailsData]:
        r"""
        Check the texts with the regexs.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> results = regex_checker.check_all(["test@example.com", "test2 @example.com"])

            >>> for result in results:
            ...     if result:
            ...         print("Matched")
            ...     else:
            ...         print("Not matched")
            Matched
            Not matched

        :param texts: The texts to check.
        :return: A list of booleans, True if the text matches all the regexs, False otherwise.
        """
        return [self.check(text) for text in texts]
    
    def load_strstream(self, stream: Iterator[str]) -> LoaderDetailsData:
        r"""
        Load the regexs from the stream.

        example:
            >>> regex_checker = RegexChecker()
            >>> with open("regexs.txt", "r") as f:
            ...     def stream():
            ...         for line in f:
            ...             yield line
            ...     regex_checker.load_strstream(stream())

        :param stream: The stream to load the regexs from.
        :return: A LoaderDetailsData object containing the number of successful and unusual.
        """
        regexs: list[tuple[re.Pattern, bool]] = []
        successful: int = 0
        unusual: int = 0
        for index, line in enumerate(stream):
            line = line.strip()
            if index == 0:
                if line == "[REGEX SERIES FILE]":
                    self._mode = CheckerMode.SERIES
                elif line == "[REGEX PARALLEL FILE]":
                    self._mode = CheckerMode.PARALLEL
                else:
                    raise ValueError(f"Invalid file format at line {index + 1}")
            else:
                try:
                    regexs.append((re.compile(line, self._flags), True))
                    successful += 1
                except re.error as e:
                    unusual += 1
        
        self._regexs = regexs
        return LoaderDetailsData(successful, unusual)
    
    def load(self, file: str) -> LoaderDetailsData:
        r"""
        Load the regexs from the file.

        example:
            >>> checker = RegexChecker()

            >>> with open("regexs.txt", "r") as f:

            >>>     checker.load(f.read())

        :param file: The file to load the regexs from.
        :return: A LoaderDetailsData object containing the number of successful and unusual regexs.
        """
        self.load_strstream(iter(file.splitlines()))
    
    def loads_from_iterator(self, stream: Iterator[tuple[str, bool]], mode:CheckerMode = CheckerMode.SERIES) -> LoaderDetailsData:
        r"""
        Load the regexs from the iterator.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.loads_from_iterator(iter([("[a-z]+", True), ("[a-z", False)]))
            LoaderDetailsData(successful=1, unusual=1)

        :param stream: The iterator to load the regexs from.
        :return: A LoaderDetailsData object containing the number of successful and unusual regexs.
        """
        self._mode = mode

        successful: int = 0
        unusual: int = 0
        for regex, enable in stream:
            try:
                self._regexs.append((re.compile(regex, self._flags), enable))
                successful += 1
            except re.error as e:
                unusual += 1
        return LoaderDetailsData(successful, unusual)
        

    def loads(self, regexs:list[tuple[str, bool]], mode:CheckerMode = CheckerMode.SERIES) -> LoaderDetailsData:
        r"""
        Load the regexs from the list.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.load([("[a-z]+", True), ("[a-z", False)])
            LoaderDetailsData(successful=1, unusual=1)

        :param regexs: The list of regexs to load.
        :param mode: The mode to use when checking the regexs. Default is CheckerMode.SERIES.
        :return: The LoaderDetailsData object containing the number of successful and unusual regexs.
        """
        return self.loads_from_iterator(iter(regexs), mode)
    
    def dump_strstream(self) -> Iterator[str]:
        r"""
        Dump the regexs to the stream.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> for line in regex_checker.dump_strstream():
            ...     print(line)
            [REGEX SERIES FILE]
            [\S]+@[\S]+\.[\S]+

        :return: An iterator of strings containing the regexs.
        """
        yield f"[REGEX {self._mode.value} FILE]\n"
        for regex, enable in self._regexs:
            yield f"{regex.pattern}\n"
    
    def dump(self) -> str:
        r"""
        Dump the regexs to the file.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> with open("regexs.txt", "w") as f:
            ...     f.write(regex_checker.dump())

        """
        file = ""
        for line in self.dump_strstream():
            file += line
        return file
    
    def dumps_to_iterator(self) -> tuple[Iterator[tuple[str, bool]], CheckerMode]:
        r"""
        Dump the regexs to the iterator.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regexs, mode = regex_checker.dumps_to_iterator()

            >>> print(mode)
            CheckerMode.SERIES

            >>> for regex, enabled in regexs:
            ...     print(f"'{regex}' | {enabled}")
            '[\S]+@[\S]+\.[\S]+' | True

        :return: The iterator of regexs and the mode.
        """
        def iterator(regexs: list[tuple[re.Pattern, bool]]) -> Iterator[tuple[str, bool]]:
            for regex, enable in regexs:
                yield (regex.pattern, enable)
        
        return iterator(self._regexs), self._mode
    
    def dumps(self) -> tuple[list[tuple[str, bool]], CheckerMode]:
        r"""
        Dump the regexs to the list.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regexs, mode = regex_checker.dumps()

            >>> print(mode)
            CheckerMode.SERIES

            >>> for regex, enabled in regexs:
            ...     print(f"'{regex}' | {enabled}")
            '[\S]+@[\S]+\.[\S]+' | True

        :return: The list of regexs and the mode.
        """
        return list(self.dumps_to_iterator()[0]), self._mode
    
    def add_regex(self, regex:str) -> bool:
        r"""
        Add a regex to the loader.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

        :param regex: The regex to add.
        :return: True if the regex was added successfully, False otherwise.
        """
        try:
            self._regexs.append((re.compile(regex, self._flags), True))
            return True
        except re.error:
            return False
    
    def __getitem__(self, index:int | slice) -> str:
        r"""
        Get the regex at the index.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker[0]
            '[\\S]+@[\\S]+\.[\\S]+'

        :param index: The index of the regex.
        :return: The regex.
        """
        if isinstance(index, slice):
            return [self._regexs[i] for i in range(*index.indices(len(self._regexs)))]
        
        if isinstance(index, int):
            if index < 0:
                index += len(self._regexs)
            if index >= len(self._regexs):
                raise IndexError("Index out of range")
            regex, enable = self._regexs[index]
            return regex.pattern
    
    def __setitem__(self, index:int | slice, regex:str) -> None:
        r"""
        Set the regex at the index.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker[0] = r"[\S]+@[\S]+\.[\S]+"
            '[\S]+@[\S]+\.[\S]+'

        :param index: The index of the regex.
        :param regex: The regex to set.
        """
        regex = re.compile(regex, self._flags)
        if isinstance(index, slice):
            for i in range(*index.indices(len(self._regexs))):
                self._regexs[i] = (regex, True)
        else:
            if index < 0:
                index += len(self._regexs)
            if index >= len(self._regexs):
                raise IndexError("Index out of range")
            self._regexs[index] = (regex, True)
    
    def __delitem__(self, index:int | slice) -> None:
        r"""
        Delete the regex at the index.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> del regex_checker[0]

            >>> len(regex_checker)
            0

        :param index: The index of the regex.
        """
        del self._regexs[index]
    
    def __len__(self) -> int:
        r"""
        Get the length of the regexs.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> len(regex_checker)
            1

        :return: The length of the regexs.
        """
        return len(self._regexs)
    
    def __iter__(self) -> Iterator[re.Pattern]:
        r"""
        Iterate over the regexs.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> for regex in regex_checker:
            ...     print(regex.pattern)
            '[\S]+@[\S]+\.[\S]+'

        :return: An iterator over the regexs.
        """
        for regex, enable in self._regexs:
            if enable:
                yield regex
    
    def __eq__(self, other: "RegexChecker") -> bool:
        r"""
        Check if the regexs are equal.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker == RegexChecker()
            False

        :param other: The other regexs to compare to.
        :return: True if the regexs are equal, False otherwise.
        """
        for index, (regex, enable) in enumerate(self._regexs):
            if regex.pattern != other[index] or enable != other.enable:
                return False
        return True

    
    def clear(self) -> None:
        r"""
        Clear the regexs.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker.clear()

            >>> len(regex_checker)
            0
        """
        self._regexs.clear()
    
    @property
    def mode(self) -> CheckerMode:
        r"""
        Get the mode of the loader.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.mode
            CheckerMode.SERIES

        :return: The mode of the loader.
        """
        return self._mode
    
    @mode.setter
    def mode(self, mode: CheckerMode) -> None:
        r"""
        Set the mode of the loader.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.mode = CheckerMode.PARALLEL
            CheckerMode.PARALLEL

        :param mode: The mode to set.
        """
        self._mode = mode
    
    def enable(self, index:int) -> None:
        r"""
        Enable the regex at the index.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker.enable(0)

        :param index: The index of the regex to enable.
        """
        self._regexs[index] = (self._regexs[index][0], True)

    def disable(self, index:int) -> None:
        r"""
        Disable the regex at the index.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker.disable(0)

        :param index: The index of the regex to disable.
        """
        self._regexs[index] = (self._regexs[index][0], False)
    
    def find_regex(self, text:str) -> int | None:
        r"""
        Find the regex index that matches the text.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker.find_regex(r"[\S]+@[\S]+\.[\S]+")
            0

        :param text: The text to search for.
        :return: The index of the regex that matches the text, or None if no match is found.
        """
        for index, (regex, enabled) in enumerate(self._regexs):
            if regex.pattern == text:
                return index
        return None
    
    def recompile(self) -> None:
        r"""
        Recompile all regexs.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker.recompile()
        """
        regexs: list[tuple[re.Pattern, bool]] = []
        for regex, enabled in self._regexs:
            regexs.append((re.compile(regex.pattern, self._flags), enabled))
        self._regexs = regexs
    
    def set_flags(self, flags: int | re.RegexFlag) -> None:
        r"""
        Set the regex flags.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker.set_flags(re.IGNORECASE)

        :param flags: The regex flags to set.
        """
        self._flags = flags
        self.recompile()
    
    def get_all_enabled(self) -> list[str]:
        r"""
        Get all enabled regexs.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker.get_all_enabled()
            ['[\S]+@[\S]+\.[\S]+']

        :return: A list of all enabled regexs.
        """
        return [regex.pattern for regex, enabled in self._regexs if enabled]

    def get_all_disabled(self) -> list[str]:
        r"""
        Get all disabled regexs.

        example:
            >>> regex_checker = RegexChecker()

            >>> regex_checker.add_regex(r"[\S]+@[\S]+\.[\S]+")
            True

            >>> regex_checker.disable(0)
            
            >>> regex_checker.get_all_disabled()
            ['[\S]+@[\S]+\.[\S]+']

        :return: A list of all disabled regexs.
        """
        return [regex.pattern for regex, enabled in self._regexs if not enabled]