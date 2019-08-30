
from typing import Optional, Dict, List, Union, Sequence, Any
from spidertools.common.element import Document, Element
from spidertools.common.nano import NanoUser, NanoNovel
import aiohttp
import io

class TalosHTTPClient(aiohttp.ClientSession):

    __slots__ = ("nano_tries", "last_guild_count", "__tokens")

    TALOS_URL: str = ...
    BOTLIST_URL: str = ...
    NANO_URL: str = ...
    BTN_URL: str = ...
    CAT_URL: str = ...
    XKCD_URL: str = ...
    SMBC_URL: str = ...

    nano_tries: int
    last_guild_count: int
    __tokens: Dict[str, Union[str, Sequence[str]]]

    # noinspection PyMissingConstructor
    def __init__(self, *args, **kwargs) -> None: ...

    async def get_site(self, url: str, **kwargs) -> Document: ...

    async def server_post_commands(self, commands: Dict[str, Any]) -> None: ...

    async def botlist_post_guilds(self, num: int) -> None: ...

    async def btn_get_names(self, gender: str = ..., usage: str = ..., number: int = ..., surname: bool = ...) -> List[str]: ...

    async def nano_get_page(self, url: str) -> Optional[Document]: ...

    async def nano_get_user(self, username: str) -> NanoUser: ...

    async def nano_get_novel(self, username: str, title: str = ...) -> NanoNovel: ...

    async def nano_login_client(self) -> int: ...

    async def get_cat_pic(self) -> Dict[str, Union[str, io.BytesIO]]: ...

    async def get_xkcd(self, xkcd: int) -> Dict[str, Union[str, io.BytesIO]]: ...

    async def get_smbc_list(self) -> List[Element]: ...

    async def get_smbc(self, smbc: str) -> Dict[str, Union[str, io.BytesIO]]: ...