
from typing import Any, List, Dict, TypeVar, Callable
import aiohttp

import spidertools.twitch.types as types


_T = TypeVar("_T")
_TK = TypeVar("_TK")


class InsufficientPerms(Exception):

    def __init__(self, required: str, *args: Any) -> None: ...

class NotASubscriber(Exception):
    pass

def needs_open(func: Callable[[_T, Any], _TK]) -> Callable[[_T, Any], _TK]: ...

class TwitchApp:

    __slots__ = ("_cid", "_secret", "_redirect", "_oauths", "session", "_users", "_open")

    _cid: str
    _secret: str
    _redirect: str
    _oauths: Dict[str, types.OAuth]
    session: aiohttp.ClientSession
    _users: Dict[str, types.User]
    _open: bool

    def __init__(self, cid: str, secret: str, redirect: str = ...) -> None: ...

    @property
    def client_id(self) -> str: ...

    @property
    def redirect(self) -> str: ...

    async def open(self) -> None: ...

    def _get_token(self, name: str) -> str: ...

    def build_v5_headers(self, name: str) -> Dict[str, str]: ...

    def build_helix_headers(self, name: str = ...) -> Dict[str, str]: ...

    async def get_helix(self, endpoint: str, name: str, **kwargs: Any): ...

    async def get_oauth(self, code: str) -> None: ...

    async def _get_user_oauth(self, oauth: types.OAuth) -> None: ...

    async def get_user(self, id: List[str] = ..., login: List[str] = ...) -> types.User: ...

    async def get_all_subs(self, name: str) -> List[types.Subscription]: ...

    async def close(self) -> None: ...
