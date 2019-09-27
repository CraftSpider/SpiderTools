
from typing import Dict, Type, Union, List, TypeVar
import spidertools.common.nano.types as types
import spidertools.common.nano.client as nclient

_N = TypeVar("_N", bound=types.NanoObj)

class NanoState:

    _client: nclient.NanoClient
    _genres: Dict[int, types.NanoGenre]
    _users: Dict[int, types.NanoUser]
    _projects: Dict[int, types.NanoProject]
    _badges: Dict[int, types.NanoBadge]
    _groups: Dict[int, types.NanoGroup]
    _external_links: Dict[int, types.NanoExternalLink]
    _project_challenges: Dict[int, types.NanoProjectChallenge]

    def __init__(self, client: nclient.NanoClient) -> None: ...

    async def _get_with_cache(self, type: Type[_N], identifier: Union[str, int], cache: Dict[int, _N]) -> List[_N]: ...

    async def update(self, obj: _N) -> None: ...

    async def get_user(self, identifier: Union[int, str]) -> types.NanoUser: ...

    async def get_project(self, identifier: Union[int, str]) -> types.NanoProject: ...

    async def get_badge(self, identifier: int) -> types.NanoBadge: ...

    async def get_group(self, identifier: int) -> types.NanoGroup: ...

    async def get_location(self, identifier: int) -> types.NanoLocation: ...

    async def get_related(self, relation_link: str) -> List[_N]: ...