
from typing import Tuple, Dict, List, Union, Sequence, Any
from spidertools.common.element import Document, Element
import aiohttp
import io

class TalosHTTPClient:

    __slots__ = ("nano_tries", "last_guild_count", "__tokens", "client", "_args", "_kwargs")

    TALOS_URL: str = ...
    BOTLIST_URL: str = ...
    BTN_URL: str = ...
    CAT_URL: str = ...
    XKCD_URL: str = ...
    SMBC_URL: str = ...

    nano_tries: int
    last_guild_count: int
    __tokens: Dict[str, Union[str, Sequence[str]]]
    client: aiohttp.ClientSession
    _args: Dict[str, Any]
    _kwargs: Tuple[Any, ...]

    # noinspection PyMissingConstructor
    def __init__(self, *args: Any, tokens: Dict[str, Union[str, Sequence[str]]] = ..., **kwargs: Any) -> None: ...

    async def init(self) -> None: ...

    async def close(self) -> None: ...

    async def get_site(self, url: str, **kwargs: Any) -> Document: ...

    async def server_post_commands(self, commands: Dict[str, Any]) -> None: ...

    async def botlist_post_guilds(self, num: int) -> None: ...

    async def btn_get_names(self, gender: str = ..., usage: str = ..., number: int = ..., surname: bool = ...) -> List[str]: ...

    async def get_cat_pic(self) -> Dict[str, Union[str, io.BytesIO]]: ...

    async def get_xkcd(self, xkcd: int) -> Dict[str, Union[str, io.BytesIO]]: ...

    async def get_smbc_list(self) -> List[Element]: ...

    async def get_smbc(self, smbc: str) -> Dict[str, Union[str, io.BytesIO]]: ...