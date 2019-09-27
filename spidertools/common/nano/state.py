
from . import types, errors


class NanoState:

    def __init__(self, client):
        self._client = client
        self._genres = {}
        self._users = {}
        self._projects = {}
        self._badges = {}
        self._groups = {}
        self._locations = {}
        self._external_links = {}
        self._project_challenges = {}

    def _resolve_type(self, cls):
        if isinstance(cls, type):
            return cls
        out = types.NanoObj.TYPE_MAP.get(cls, None)
        if out is None:
            raise NotImplementedError(f"Found unimplemented NaNo type {cls}")
        return out

    def _resolve_cache(self, cls):
        if isinstance(cls, type):
            cls = cls.TYPE
        return getattr(self, f"_{cls.replace('-', '_')}")

    def _make_with_cache(self, data):
        type_str = data["type"]
        cache = self._resolve_cache(type_str)
        if int(data["id"]) in cache:
            return cache[int(data["id"])]
        type = self._resolve_type(type_str)
        obj = type(self, data)
        cache[obj.id] = obj
        return obj

    def _get_cache_obj(self, type, id):
        cache = self._resolve_cache(type)
        return cache.get(id, None)

    async def _get_with_cache(self, type, identifier, cache, include=()):
        if identifier in cache:
            return cache[identifier]
        data = {}
        if include:
            data["include"] = ",".join(include)
        status, data = await self._client.make_request(f"/{type.TYPE}/{identifier}", "GET", data)
        if status == 404:
            raise errors.NotFound(type, identifier)
        for i in data.get("included", ()):
            self._make_with_cache(i)
        obj = type(self, data["data"])
        cache[obj.id] = obj
        return obj

    async def update(self, obj):
        status, data = await self._client.make_request(obj._self, "GET")
        obj._from_data(data["data"]["attributes"])

    async def get_obj(self, type, id, include=()):
        return await self._get_with_cache(self._resolve_type(type), id, self._resolve_cache(type), include)

    async def get_user(self, identifier, include=()):
        return await self._get_with_cache(types.NanoUser, identifier, self._users, include)

    async def get_project(self, identifier, include=()):
        return await self._get_with_cache(types.NanoProject, identifier, self._projects, include)

    async def get_badge(self, identifier):
        return await self._get_with_cache(types.NanoBadge, identifier, self._badges)

    async def get_group(self, identifier):
        return await self._get_with_cache(types.NanoGroup, identifier, self._groups)

    async def get_location(self, identifier):
        return await self._get_with_cache(types.NanoLocation, identifier, self._locations)

    async def get_related(self, relation_link):
        status, data = await self._client.make_request(relation_link, "GET")
        return [self._make_with_cache(x) for x in data["data"]]
