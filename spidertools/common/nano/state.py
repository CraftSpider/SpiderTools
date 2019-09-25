
from . import types


class NanoState:

    def __init__(self, client):
        self._client = client
        self._users = {}
        self._projects = {}
        self._external_links = {}

    async def get_user(self, identifier):
        if identifier in self._users:
            return self._users[identifier]
        status, data = await self._client.make_request(f"/users/{identifier}", "GET", )
        user = types.NanoUser(self, data["data"])
        self._users[user.id] = user
        return user

    async def get_external_link(self, identifier):
        if identifier in self._external_links:
            return self._external_links[identifier]
        status, data = await self._client.make_request(f"/external-links/{identifier}", "GET")
        link = types.NanoExternalLink(self, data)
        self._external_links[link.id] = link
        return link

    async def get_related(self, relation_link):
        status, data = await self._client.make_request(relation_link, "GET")
        out = []
        for item in data["data"]:
            out.append(types.NanoObj.TYPE_MAP[item["type"]](self, item))
        for i in range(len(out)):
            item = out[i]
            cache = getattr(self, f"_{item.TYPE}")
            if item.id in cache:
                out[i] = cache[item.id]
        return out
