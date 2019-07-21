"""
    Talos utils stub file
"""

from typing import Dict, List, Tuple
import logging
import pathlib
import discord.ext.commands as dcommands
import spidertools.common.element as el


fullwidth_transform: Dict[str, str] = ...
tz_map: Dict[str, float] = ...
log_folder: pathlib.Path

def configure_logger(logger: logging.Logger, *, handlers: List[logging.Handler] = ..., formatter: logging.Formatter = ..., level: int = ..., propagate: bool = ...): ...

def words_written(time: int, wpm: int) -> int: ...

def time_to_write(words: int, wpm: int) -> int: ...

def pretty_bytes(bytes: int) -> str: ...

def key_generator(size: int = ..., chars: str = ...) -> str: ...

def log_error(logger: logging.Logger, level: int, error: Exception, message: str = ...) -> None: ...

def safe_remove(*filenames: str) -> None: ...

def replace_escapes(text: str) -> str: ...

def is_lower_snake(text: str) -> bool: ...

def is_upper_snake(text: str) -> bool: ...

def is_snake(text: str) -> bool: ...

def is_lower_camel(text: str) -> bool: ...

def is_upper_camel(text: str) -> bool: ...

def is_camel(text: str) -> bool: ...

def is_other(text: str) -> bool: ...

def get_type(text: str) -> str: ...

def split_snake(text: str, fix: bool = ...) -> Tuple[str, ...]: ...

def split_camel(text: str, fix: bool = ...) -> Tuple[str, ...]: ...

def to_snake_case(text: str, upper: bool = ...) -> str: ...

def to_camel_case(text: str, upper: bool = ...) -> str: ...

def add_spaces(text: str) -> str: ...

def zero_pad(text: str, length: int) -> str: ...

def to_dom(html: str) -> el.Document: ...

def to_nodes(html: str) -> List[el.Node]: ...
