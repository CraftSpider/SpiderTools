
from typing import Any, Type, Dict
import spidertools.common.nano.types as types


class NanoException(Exception):

    def __init__(self) -> None: ...

    def _set_message(self, *args: Any) -> None: ...

class InvalidLogin(NanoException):

    def __init__(self, msg: str) -> None: ...

class NotFound(NanoException):

    TYPE_MAP: Dict[str, Type['NotFound']]
    TYPE: str

    def __new__(cls, t: Type[types.NanoObj], msg: str) -> 'NotFound': ...

    def __init__(self, t: Type[types.NanoObj], msg: str) -> None: ...

    def __init_subclass__(cls, **kwargs) -> None: ...

class UserNotFound(NotFound):
    ...

class ProjectNotFound(NotFound):
    ...
