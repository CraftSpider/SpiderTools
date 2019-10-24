import aiohttp
import json
from . import state, types, errors


class NanoClient:

    URL = "https://api.nanowrimo.org"

    def __init__(self, username, password):
        self.client = None

        self._state = state.NanoState(self)
        self._username = username
        self._password = password

        self._user_ids = {}

        self.__auth_token = None

    def logged_in(self):
        return self.__auth_token is not None

    async def init(self):
        self.client = aiohttp.ClientSession()
        await self.login(self._username, self._password)

    async def make_request(self, endpoint, method, data=None, *, _handle=True):
        method = method.upper()
        if method == "GET":
            params = data
            json_data = None
        else:
            params = None
            json_data = data

        headers = {}
        if self.__auth_token is not None:
            headers["Authorization"] = self.__auth_token

        async with self.client.request(method, self.URL + endpoint, params=params, json=json_data, headers=headers)\
                as response:
            status = response.status
            text = await response.text()
            if text:
                data = json.loads(text)
            else:
                data = None

            if _handle:
                if status == 401:
                    if not self.logged_in():
                        raise errors.MissingPermissions("Privileged request made while client not logged in")
                    await self.login(self._username, self._password)
                    status, data = await self.make_request(endpoint, method, data, _handle=False)
                    if status == 401:
                        if "error" in data:
                            msg = data["error"]
                        else:
                            msg = text
                        raise errors.MissingPermissions(msg) from None
                    return status, data

            return status, data

    async def login(self, username, password):
        status, data = await self.make_request(
            "/users/sign_in", "POST", {"identifier": username, "password": password}, _handle=False
        )
        if status == 401:
            raise errors.InvalidLogin(data["error"])
        self.__auth_token = data["auth_token"]

    async def logout(self):
        status, data = await self.make_request("/users/logout", "POST")
        self.__auth_token = None

    async def get_fundometer(self):
        status, data = await self.make_request("/fundometer", "GET")
        return types.Funds(data)

    async def get_user(self, username, include=()):
        if username in self._user_ids:
            id = self._user_ids[username]
        else:
            id = username
        if isinstance(include, str):
            include = [include]

        user = await self._state.get_user(id, include=include, update=True)
        self._user_ids[user.name] = user.id
        return user
