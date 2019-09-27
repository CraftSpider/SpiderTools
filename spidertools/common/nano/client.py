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

    async def make_request(self, endpoint, method, data=None):
        method = method.upper()
        if method == "GET":
            params = data
            json_data = None
        elif method == "POST":
            params = None
            json_data = data
        else:
            params = None
            json_data = data

        headers = {}
        if self.__auth_token is not None:
            headers["Authorization"] = self.__auth_token

        async with self.client.request(method, self.URL + endpoint, params=params, json=json_data, headers=headers)\
                as response:  # TODO: check status code
            status = response.status

            if status == 401:
                raise errors.InvalidLogin("Privileged request made while client not logged in")

            text = await response.text()
            if text:
                out = json.loads(text)
            else:
                out = None
            return status, out

    async def login(self, username, password):
        status, data = await self.make_request("/users/sign_in", "POST", {"identifier": username, "password": password})
        if status == 401:
            raise errors.InvalidLogin(data["error"])
        self.__auth_token = data["auth_token"]

    async def logout(self):
        status, data = await self.make_request("/users/logout", "POST")
        self.__auth_token = None

    async def get_fundometer(self):
        status, data = await self.make_request("/fundometer", "GET")
        return types.Funds(data)

    async def get_user(self, username, include):
        if username in self._user_ids:
            id = self._user_ids[username]
        else:
            id = username
        if isinstance(include, str):
            include = [include]

        user = await self._state.get_user(id, include=include)
        self._user_ids[user.name] = user.id
        return user
