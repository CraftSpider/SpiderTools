
from typing import Tuple, Dict, List, Union, Optional, Any, Iterable, TypeVar, Type, FrozenSet, Callable, Sequence
from spidertools.common.data import *
import mysql.connector.cursor_cext as cursor_cext
import mysql.connector.abstracts as mysql_abstracts

_T = TypeVar("_T")
_Row = TypeVar("_Row", bound=Row)

levels: Dict[str, int] = ...

class EmptyCursor(mysql_abstracts.MySQLCursorAbstract):

    __slots__ = ()

    DEFAULT_ONE: None = ...
    DEFAULT_ALL: list = ...

    # noinspection PyMissingConstructor
    def __init__(self) -> None: ...

    def __iter__(self) -> iter: ...

    @property
    def description(self) -> Tuple: return ...
    @property
    def rowcount(self) -> int: return ...
    @property
    def lastrowid(self) -> type(None): return ...

    def callproc(self, procname: str, args: Tuple[Any, ...] = ...) -> None: ...

    def close(self) -> None: ...

    def execute(self, query: str, params: Iterable = ..., multi: bool = ...) -> None: ...

    def executemany(self, operation: str, seqparams: Iterable[Iterable]) -> None: ...

    def fetchone(self) -> type(DEFAULT_ONE): ...

    def fetchmany(self, size: int = ...) -> type(DEFAULT_ALL): ...

    def fetchall(self) -> type(DEFAULT_ALL): ...

talos_create_table: str = ...
talos_add_column: str = ...
talos_modify_column: str = ...
talos_create_trigger: str = ...

def and_from_dict(kwargs: Dict[str, Any]) -> str: ...

def key_from_dict(kwargs: Dict[str, Any]) -> FrozenSet[str]: ...

_caches: Dict[Callable, Dict[type, Dict[FrozenSet[str], Any]]] = ...

def cached(func: Callable[[Any, Type[Row], Any, Any], Any]) -> Callable[[Any, Type[Row], Any, Any], Any]: ...

def invalidate(func: Callable[[Any, _Row, Any, Any], _Row]) -> Callable[[Any, _Row, Any, Any], _Row]: ...

class GenericDatabase:

    __slots__ = ("_sql_conn", "_cursor", "_username", "_password", "_schema", "_host", "_port", "_schemadef")

    _sql_conn: Optional[mysql_abstracts.MySQLConnectionAbstract]
    _cursor: Union[cursor_cext.CMySQLCursor, EmptyCursor]
    _username: str
    _password: str
    _schema: str
    _host: str
    _port: int
    _schemadef: Dict[str, Dict[str, Any]]

    def __init__(self, address: str, port: int, username: str, password: str, schema: str, schemadef: Dict[str, Dict[str, Any]]) -> None: ...

    def verify_schema(self) -> Dict[str, int]: ...

    def commit(self) -> bool: ...

    def is_connected(self) -> bool: ...

    def reset_connection(self) -> None: ...

    def raw_exec(self, statement: str, *args: Any) -> List: ...

    def execute(self, statement: str, args: Optional[Sequence[Any]] = ...) -> None: ...

    # Meta methods

    def create_schema(self, schema: str, charset: str = ...) -> None: ...

    def create_table(self, table: str, columns: List[str], primary: str = ..., foreign: str = ..., engine: str = ..., charset: str = ...) -> None: ...

    def drop_table(self, table: str) -> None: ...

    def add_column(self, table: str, column: str, type: str, num: int = ..., constraint: str = ..., after: str = ...) -> None: ...

    def modify_column(self, table: str, column: str, type: str, num: int = ...) -> None: ...

    def remove_column(self, table: str, column: str) -> None: ...

    def has_schema(self, schema: str) -> bool: ...

    def get_tables(self) -> List[Table]: ...

    def has_table(self, table: str) -> bool: ...

    def get_columns(self, table_name: str) -> List[Column]: ...

    def has_column(self, table: str, column: str) -> bool: ...

    # Generic methods

    def get_item(self, type: Type[_Row], *, order: str = ..., default: _T = ..., **kwargs: Any) -> Union[_Row, _T]: ...

    def get_items(self, type: Type[_Row], *, limit: Union[int, Tuple[int, int]] = ..., order: str = ..., **kwargs: Any) -> List[_Row]: ...

    def get_count(self, type: Type[_Row], **kwargs: Any) -> int: ...

    def save_item(self, item: Union[type(Row), type(MultiRow)]) -> None: ...

    def remove_item(self, item: Union[type(Row), type(MultiRow)], general: bool = ...) -> None: ...

    def remove_items(self, type: Type[_Row], *, limit: Union[int, Tuple[int, int]] = ..., order: str = ..., **kwargs: Any) -> None: ...
