
import spidertools.common.accessors.base as base

from typing import Tuple, List, Optional, Union, Dict

_Sql = Union[str, int, bool]
_Sentinel: object = ...

class PostgresAccessor(base.DatabaseAccessor):

    __slots__ = ("_schema",)

    _schema: str

    def create_connection(self, *, user: str, password: str, host: str, port: int, schema: str, autocommit: bool) -> None: ...

    def execute(self, query: str, params: Optional[Union[List[_Sql], Dict[str, _Sql]]] = ..., multi: bool = ...) -> None: ...

    def get_schemata(self) -> List[Tuple[_Sql, ...]]: ...

    def current_schema(self) -> Optional[str]: ...

    def create_schema(self, schema: str) -> None: ...

    def has_schema(self, schema: str) -> bool: ...

    def create_table(self, name: str, columns: List[Dict[str, _Sql]], primary_keys: Optional[List[str]] = ..., foreign_keys: Optional[List[Dict[str, str]]] = ...) -> None: ...

    def get_tables(self) -> List[Tuple[_Sql, ...]]: ...

    def has_table(self, name: str) -> bool: ...

    def drop_table(self, name: str) -> None: ...

    def add_column(self, table: str, column: Dict[str, _Sql], *, after: Optional[str] = ...) -> None: ...

    def get_columns(self, table: str) -> List[Tuple[_Sql, ...]]: ...

    def has_column(self, table: str, column: str) -> bool: ...

    def alter_column(self, table: str, column: Dict[str, _Sql]) -> None: ...

    def drop_column(self, table: str, column: str) -> None: ...

    def insert(self, table: str, *, values: List[_Sql], names: Optional[List[str]] = ..., update: bool = ...) -> None: ...

    def count(self, table: str, *, where: str, params: Optional[Union[List[_Sql], Dict[str, _Sql]]] = ..., limit: Optional[str] = ...) -> int: ...

    def select(self, table: str, *, where: str, params: Optional[Union[List[_Sql], Dict[str, _Sql]]] = ..., order: Optional[str] = ..., limit: Optional[str] = ...) -> List[Tuple[_Sql, ...]]: ...

    def delete(self, table: str, *, where: str, params: Optional[Union[List[_Sql], Dict[str, _Sql]]] = ..., order: Optional[str] = ..., limit: Optional[str] = ...) -> None: ...

    def get_triggers(self) -> List[Tuple[_Sql, ...]]: ...

    def drop_trigger(self, trigger: str) -> None: ...

