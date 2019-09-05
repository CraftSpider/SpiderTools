
from typing import Type, Union, Tuple, Any
import discord.ext.commands as commands
import datetime as dt


class ConverterMeta(type):

    def __getitem__(cls, item: str) -> Type['ConverterMeta']: ...


class GenericConverter(type, commands.Converter, metaclass=ConverterMeta):

    num: int = ...

    def __new__(mcs, *args: Any, **kwargs: Any) -> Type['GenericConverter']: ...

    async def convert(cls, ctx: commands.Context, argument: str) -> Any: ...


class DateConverter(GenericConverter):

    datefmt: Tuple[str, ...]

    def __init__(cls, datefmt: Union[str, Tuple[str, ...]] = ...) -> None: ...

    async def convert(cls, ctx: commands.Context, argument: str) -> dt.date: ...

class TimeConverter(GenericConverter):

    timefmt: Tuple[str, ...]

    def __init__(cls, timefmt: Union[str, Tuple[str, ...]] = ...) -> None: ...

    async def convert(cls, ctx: commands.Context, argument: str) -> dt.time: ...
