
from . import types


class NanoState:

    def __init__(self, client):
        self._client = client
        self._genres = {}
        self._users = {}
        self._projects = {}
        self._badges = {}
        self._external_links = {}

    async def _get_with_cache(self, type, identifier, cache):
        if identifier in cache:
            return cache[identifier]
        status, data = await self._client.make_request(f"/{type.TYPE}/{identifier}", "GET")
        obj = type(self, data["data"])
        cache[obj.id] = obj
        return obj

    async def get_user(self, identifier):
        return await self._get_with_cache(types.NanoUser, identifier, self._users)

    async def get_project(self, identifier):
        return await self._get_with_cache(types.NanoProject, identifier, self._projects)

    async def get_badge(self, identifier):
        return await self._get_with_cache(types.NanoBadge, identifier, self._badges)

    async def get_related(self, relation_link):
        status, data = await self._client.make_request(relation_link, "GET")
        out = []
        for item in data["data"]:
            cls = types.NanoObj.TYPE_MAP.get(item["type"], None)
            if cls is None:
                raise NotImplementedError(f"Found unimplemented NaNo type {item['type']}")
            out.append(cls(self, item))
        for i in range(len(out)):
            item = out[i]
            cache = getattr(self, f"_{item.TYPE}")
            if item.id in cache:
                out[i] = cache[item.id]
        return out
