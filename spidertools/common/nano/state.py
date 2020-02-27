
from . import types, errors


class NanoState:
    """
        Represents the state of a Nano client, with the currently loaded cached data and
        known links between objects. Helps avoid unnecessary object retrieval and updating
        of objects sanely.
    """

    def __init__(self, client):
        """
            Create a new NanoState instance
        :param client: NanoClient object associated with this state
        """
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
        """
            Get the NanoObj subclass associated with a type passed by the NaNo API
        :param cls: Class to resolve. May already be the type
        :return: NanoObj subclass representing that type
        """
        if isinstance(cls, type):
            return cls
        out = types.NanoObj.TYPE_MAP.get(cls, None)
        if out is None:
            raise NotImplementedError(f"Found unimplemented NaNo type {cls}")
        return out

    def _resolve_cache(self, cls):
        """
            Get the cache associated with a NanoObj type, as every one uses its own cache
        :param cls: Type to get cache for
        :return: Cache associated with that type
        """
        if isinstance(cls, type):
            cls = cls.TYPE
        return getattr(self, f"_{cls.replace('-', '_')}")

    def _make_with_cache(self, data):
        """
            Create a new object from raw JSON, inserting it into the cache
            Returns already cached object, if it exists
        :param data: Object data in JSON
        :return: Object, new or retrieved from cache
        """
        type_str = data["type"]
        cache = self._resolve_cache(type_str)
        if int(data["id"]) in cache:
            return cache[int(data["id"])]
        type = self._resolve_type(type_str)
        obj = type(self, data)
        cache[obj.id] = obj
        return obj

    def _get_cache_obj(self, type, id):
        """
            Get an object of a given type with given ID from the associated cache, or None
        :param type: Type of object
        :param id: ID of object
        :return: Object retrieved from cache, or None
        """
        cache = self._resolve_cache(type)
        return cache.get(id, None)

    async def _get_with_cache(self, type, identifier, cache, *, include=(), update=False):
        """
            Retrieve an object from the API, with cache usage. Returns object if it's in the cache,
            otherwise goes out to the API and requests it.
        :param type: Type of object to retrieve
        :param identifier: ID of object to retrieve
        :param cache: Cache to use
        :param include: What extra data to pre-fetch in the request
        :param update: Whether to update the object even if it is found in cache
        :return: Retrieved object
        """
        if identifier in cache:
            obj = cache[identifier]
            if update:
                await self.update(obj)
            return obj
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
        """
            Update an object's data set from the API
        :param obj: Object to update
        """
        status, data = await self._client.make_request(obj._self, "GET")
        obj._from_data(data["data"]["attributes"])

    async def get_obj(self, type, id, **kwargs):
        """
            Get an object by type and ID
        :param type: Type of object to retrieve
        :param id: ID of object
        :param kwargs: Extra arguments to pass
        :return: New object
        """
        return await self._get_with_cache(self._resolve_type(type), id, self._resolve_cache(type), **kwargs)

    async def get_user(self, identifier, **kwargs):
        """
            Get a user by identifier (username or user ID)
        :param identifier: Username or user ID to retrieve
        :param kwargs: Extra arguments to pass
        :return: Retrieved user
        """
        return await self._get_with_cache(types.NanoUser, identifier, self._users, **kwargs)

    async def get_project(self, identifier, **kwargs):
        """
            Get a project by identifier (name or project ID)
        :param identifier: Project name or ID to retrieve
        :param kwargs: Extra arguments to pass
        :return: Retrieved project
        """
        return await self._get_with_cache(types.NanoProject, identifier, self._projects, **kwargs)

    async def get_badge(self, identifier):
        """
            Get a badge by identifier (ID)
        :param identifier: Badge ID to retrieve
        :return: Retrieved badge
        """
        return await self._get_with_cache(types.NanoBadge, identifier, self._badges)

    async def get_group(self, identifier):
        """
            Get a group by identifier (name or group ID)
        :param identifier: Group name or ID to retrieve
        :return: Retrieved group
        """
        return await self._get_with_cache(types.NanoGroup, identifier, self._groups)

    async def get_location(self, identifier):
        """
            Get a location by identifier (name or location ID)
        :param identifier: Location name or ID to retrieve
        :return: Retrieved location
        """
        return await self._get_with_cache(types.NanoLocation, identifier, self._locations)

    async def get_related(self, relation_link):
        """
            Get all the objects associated with another object by relation link
        :param relation_link: API endpoint to get related objects at
        :return: List of related objects
        """
        status, data = await self._client.make_request(relation_link, "GET")
        return [self._make_with_cache(x) for x in data["data"]]

    async def patch_obj(self, obj, data):
        """
            Send a request to alter an object's data on the API, if we have permission to alter that object
        :param obj: Object to patch to API
        :param data: New object data to send
        """
        payload = {"data": data}
        status, data = self._client.make_request(f"/{type(obj).TYPE}/{obj.id}", "PATCH", payload)
