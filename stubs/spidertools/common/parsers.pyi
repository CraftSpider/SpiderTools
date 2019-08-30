
from typing import Tuple, Dict, List, Iterable, Union, Optional, Sequence, overload, TypeVar
from spidertools.common.element import Node, Element
import html.parser as parser

def attrs_to_dict(attrs: Iterable[Tuple[str, str]]) -> Dict[str, Union[str, List[str]]]: ...

class TreeGen(parser.HTMLParser):

    heads: List[Element]
    cur: Optional[Node]

    def __init__(self) -> None: ...

    def reset(self) -> None: ...

    def close(self) -> List[Element]: ...

    def error(self, message: str) -> None: ...

    def handle_starttag(self, tag: str, attrs: Tuple[Tuple[str, str]]) -> None: ...

    def handle_endtag(self, tag: str) -> None: ...

    def handle_data(self, data: str) -> None: ...

_KT = TypeVar("_KT")

class _Sentinel:
    pass

_Sentinel = _Sentinel()

class ArgParser:

    source: Sequence[str]
    args: List[str]
    flags: List[str]
    options: Dict[str, str]

    def __init__(self, args: Sequence[str]) -> None: ...

    @overload
    def get_arg(self, pos) -> str: ...
    @overload
    def get_arg(self, pos, default: _KT) -> Union[str, _KT]: ...

    def has_flag(self, *, short: Optional[str] = ..., long: Optional[str] = ...) -> bool: ...

    def has_option(self, name: str) -> bool: ...

    @overload
    def get_option(self, name: str) -> str: ...
    @overload
    def get_option(self, name: str, default: _KT) -> Union[str, _KT]: ...

