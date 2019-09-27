
from typing import Optional, Dict, Tuple, Any
import spidertools.common.nano.state as state
import spidertools.common.nano.types as types
import aiohttp


class NanoClient:

    URL: str = ...

    client: Optional[aiohttp.ClientSession]
    _state: state.NanoState
    _username: str
    _password: str
    _user_ids: Dict[str, int]
    __auth_token: Optional[str]

    def __init__(self, username: str, password: str) -> None: ...

    async def init(self) -> None: ...

    async def make_request(self, endpoint: str, method: str, data: Dict[str, Any] = ...) -> Tuple[int, Optional[Dict[str, Any]]]: ...

    async def login(self, username: str, password: str) -> None: ...

    async def logout(self) -> None: ...

    async def get_fundometer(self) -> types.Funds: ...

    async def get_user(self, username: str) -> types.NanoUser: ...
