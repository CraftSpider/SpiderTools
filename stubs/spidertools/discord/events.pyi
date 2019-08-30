
from typing import Callable, Awaitable, Any, Optional, Union, NoReturn
import asyncio
import spidertools.common as utils
import spidertools.discord as dutils
import datetime as dt


def align_period(period: dutils.EventPeriod) -> dt.timedelta: ...

class EventPeriod(utils.SqlConvertable):

    __slots__ = ("_seconds",)

    _seconds: int

    def __new__(cls, period: Union['EventPeriod', str, None]) -> Optional['EventPeriod']: ...

    def __init__(self, period: Union['EventPeriod', str]) -> None: ...

    def __str__(self) -> str: ...

    def __int__(self) -> int: ...

    @property
    def days(self) -> int: ...

    @property
    def hours(self) -> int: ...

    @property
    def minutes(self) -> int: ...

    @minutes.setter
    def minutes(self, value) -> None: ...

    @property
    def seconds(self) -> int: return

    @seconds.setter
    def seconds(self, value) -> None: ...

    def timedelta(self) -> dt.timedelta: ...

    def sql_safe(self) -> str: ...

class EventLoop:

    __slots__ = ("_task", "__wrapped__", "_instance", "period", "persist", "start_time", "loop", "name", "parent",
                 "description", "long_desc")

    _task: asyncio.Task
    __wrapped__: Callable[[Any], Awaitable[None]]
    period: dutils.EventPeriod
    persist: bool
    start_time: Optional[dt.datetime]
    loop: asyncio.AbstractEventLoop
    name: str
    parent: Union[dutils.TalosCog, dutils.ExtendedBot]
    description: str
    long_desc: str

    def __call__(self, *args: Any, **kwargs: Any) -> NoReturn: ...

    def __init__(self, coro: Callable[[Any], Awaitable[None]], period: str, loop: asyncio.AbstractEventLoop = ..., **kwargs: Any) -> None: ...

    def __str__(self) -> str: ...

    @property
    def callback(self) -> Callable[[Any], Awaitable]: ...

    @callback.setter
    def callback(self, value: Callable[[Any], Awaitable]) -> None: ...

    def set_start_time(self, time: dt.datetime) -> None: ...

    def start(self, *args: Any, **kwargs: Any) -> None: ...

    async def run(self, *args: Any, **kwargs: Any) -> None: ...

    def stop(self) -> None: ...

def eventloop(period: Union[str, dutils.EventPeriod], **kwargs: Any) -> Callable[[Callable[[Any], Awaitable]], EventLoop]: ...