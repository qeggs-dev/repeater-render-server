from __future__ import annotations
from typing import Callable, Coroutine

class CriticalException(Exception):
    """
    关键异常，抛出后程序将会崩溃
    """
    def __init__(
        self,
        message: str,
        wait: float | Callable[[CriticalException], float] | Callable[[CriticalException], Coroutine[None, None, float]] | None = None
    ):
        """
        创建一个CriticalException对象

        :param message: 异常信息
        :param wait: 可选的等待函数，用于在抛出异常后等待一段时间再退出程序，方便程序进行清理操作(返回值如果是float则在操作结束后等待该时间，None则直接退出)

        :type message: str
        :type wait: float | Callable[[], float] | None

        :return: None
        """
        super().__init__(message)
        self.message: str = message
        self.wait: float | Callable[[CriticalException], float] | Callable[[CriticalException], Coroutine[None, None, float]] | None = wait