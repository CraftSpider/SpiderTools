
from typing import Dict, List, Any, Sequence, Union, Iterable, Optional, Iterator
import abc
import datetime as dt
import discord.ext.commands as commands

SqlRow = Sequence[Union[str, int]]

class _EmptyVal:

    def __eq__(self, other: Any) -> bool: ...

class Row(metaclass=abc.ABCMeta):

    __slots__ = ()

    def __init__(self, row: SqlRow, conv_bool: bool = ...) -> None: ...

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    def __eq__(self, other) -> bool: ...

    def to_row(self) -> List[Union[str, int]]: ...

    @classmethod
    def table_name(cls) -> str: ...

class MultiRow(metaclass=abc.ABCMeta):

    __slots__ = ("_removed",)

    _removed: Iterable[type(Row)]

    def __init__(self, data: Dict[str, Union[type(Row), List[type(Row)], Dict[Any, type(Row)]]]) -> None: ...

    def __iter__(self) -> Iterator[type(Row)]: ...

    def __eq__(self, other: Any) -> bool: ...

    def items(self) -> Iterator[type(Row)]: ...

    @abc.abstractmethod
    def removed_items(self) -> Iterable[type(Row)]: ...

class SqlConvertable(metaclass=abc.ABCMeta):

    __slots__ = ()

    def __eq__(self, other) -> bool: ...

    @abc.abstractmethod
    def sql_safe(self) -> Union[str, int]: ...


class Table(Row):

    __slots__ = ("catalog", "schema", "name", "type", "engine", "version", "row_format", "num_rows", "avg_row_len",
                 "data_len", "max_data_len", "index_len", "data_free", "auto_increment", "create_time", "update_time",
                 "check_time", "table_collation", "checksum", "create_options", "table_commentx")

class Column(Row):

    __slots__ = ("catalog", "schema", "table_name", "name", "position", "default", "nullable", "type", "char_max_len",
                 "bytes_max_len", "numeric_precision", "numeric_scale", "datetime_precision", "char_set_name",
                 "collation_name", "column_type", "column_key", "extra", "privileges", "comment", "generation_expr")

    catalog: str
    schema: str
    table_name: str
    name: str
    position: int
    default: Any
    nullable: str
    type: str
    char_max_len: Optional[int]
    bytes_max_len: Optional[int]
    numeric_precision: int
    numeric_scale: int
    datetime_precision: Optional[str]
    char_set_name: Optional[str]
    collation_name: Optional[str]
    column_type: str
    column_key: str
    extra: str
    privileges: str
    comment: str
    generation_expr: str


