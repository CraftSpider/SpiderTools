
from typing import Tuple, Dict, List, Union, Optional, Any, Iterable, TypeVar, Type, FrozenSet, Callable, Sequence
from spidertools.common.data import *
from spidertools.common.accessors import base
import mysql.connector.cursor_cext as cursor_cext
import mysql.connector.abstracts as mysql_abstracts

_T = TypeVar("_T")
_Row = TypeVar("_Row", bound=Row)

def and_from_dict(kwargs: Dict[str, Any]) -> str: ...

def key_from_dict(kwargs: Dict[str, Any]) -> FrozenSet[str]: ...

_caches: Dict[Callable, Dict[type, Dict[FrozenSet[str], Any]]] = ...

def cached(func: Callable[[Any, Type[Row], Any, Any], Any]) -> Callable[[Any, Type[Row], Any, Any], Any]: ...

def invalidate(func: Callable[[Any, _Row, Any, Any], _Row]) -> Callable[[Any, _Row, Any, Any], _Row]: ...

class GenericDatabase:

    __slots__ = ("_accessor", "_username", "_password", "_schema", "_host", "_port", "_schemadef")

    _accessor: base.DatabaseAccessor
    _username: str
    _password: str
    _schema: str
    _host: str
    _port: int
    _schemadef: Dict[str, Dict[str, Any]]

    def __init__(self, address: str, port: int, username: str, password: str, schema: str, schemadef: Dict[str, Dict[str, Any]], *, connect: bool = ...) -> None: ...

    def verify_schema(self) -> Dict[str, int]: ...

    def commit(self) -> bool: ...

    def is_connected(self) -> bool: ...

    def reset_connection(self) -> None: ...

    def raw_exec(self, statement: str, *args: Any) -> List: ...

    def execute(self, statement: str, args: Optional[Sequence[Any]] = ...) -> None: ...

    # Meta methods

    def get_schemata(self) -> List[Schema]: ...

    def has_schema(self, schema: str) -> bool: ...

    def get_tables(self) -> List[Table]: ...

    def has_table(self, table: str) -> bool: ...

    def get_columns(self, table_name: str) -> List[Column]: ...

    def has_column(self, table: str, column: str) -> bool: ...

    def get_triggers(self) -> List[Trigger]: ...

    # Generic methods

    def get_item(self, type: Type[_Row], *, order: str = ..., default: _T = ..., **kwargs: Any) -> Union[_Row, _T]: ...

    def get_items(self, type: Type[_Row], *, limit: Union[int, Tuple[int, int]] = ..., order: str = ..., **kwargs: Any) -> List[_Row]: ...

    def get_count(self, type: Type[_Row], **kwargs: Any) -> int: ...

    def save_item(self, item: Union[type(Row), type(MultiRow)]) -> None: ...

    def remove_item(self, item: Union[type(Row), type(MultiRow)], general: bool = ...) -> None: ...

    def remove_items(self, type: Type[_Row], *, limit: Union[int, Tuple[int, int]] = ..., order: str = ..., **kwargs: Any) -> None: ...
