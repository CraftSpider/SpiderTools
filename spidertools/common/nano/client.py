import aiohttp
import json
from . import state, types, errors


class NanoClient:
    """
        Client to communicate with the NaNoWriMo API. Represents a user, with all the abilities
        of one, in theory.
    """

    URL = "https://api.nanowrimo.org"

    def __init__(self, username, password):
        """
            Create a new Nano client. Takes a username and password, and uses them to authenticate with the service.
        :param username: Username of the user to auth as
        :param password: Password of the user to auth as
        """
        self.client = None

        self._state = state.NanoState(self)
        self._username = username
        self._password = password

        self._user_ids = {}

        self.__auth_token = None

    def logged_in(self):
        """
            Check whether this client is currently logged in
        :return: Whether the client is logged in
        """
        return self.__auth_token is not None

    async def init(self):
        """
            Initialize this Nano client. Must be called before the client is used
        """
        self.client = aiohttp.ClientSession()
        await self.login()

    async def make_request(self, endpoint, method, data=None, *, _handle=True):
        """
            Make a request against a NaNo endpoint and get the raw result, with some error handling
        :param endpoint: Nano API endpoint to request against
        :param method: HTTP method to use (GET, POST, etc)
        :param data: Dict of data to send to the endpoint, as params or JSON
        :param _handle: Whether to automatically attempt to resolve errors
        :return: (status code, returned data) tuple
        """
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
                    self.__auth_token = None
                    await self.login()
                    status, data = await self.make_request(endpoint, method, data, _handle=False)
                    if status == 401:
                        if "error" in data:
                            msg = data["error"]
                        else:
                            msg = text
                        raise errors.MissingPermissions(msg) from None
                    return status, data

            return status, data

    async def login(self):
        """
            Log in the client. Makes a login request, and saves the token if it succeeds.
            Raises an InvalidLogin error on failure
        """
        status, data = await self.make_request(
            "/users/sign_in", "POST", {"identifier": self._username, "password": self._password}, _handle=False
        )
        if status == 401:
            raise errors.InvalidLogin(data["error"])
        self.__auth_token = data["auth_token"]

    async def logout(self):
        """
            Log out the client. Makes a logout request, and sets the auth token to none if it succeeds.
        """
        status, data = await self.make_request("/users/logout", "POST")
        self.__auth_token = None

    async def get_fundometer(self):
        """
            Get the current state of the fundometer. Doesn't require being logged in
        :return: Fundometer state object
        """
        status, data = await self.make_request("/fundometer", "GET")
        return types.Funds(data)

    async def get_user(self, username, include=()):
        """
            Get info about a user based on their username, optionally pre-loading various data about the user
        :param username: Username to load
        :param include: User traits to include
        :return: User object with fetched data
        """
        if username in self._user_ids:
            id = self._user_ids[username]
        else:
            id = username
        if isinstance(include, str):
            include = [include]

        user = await self._state.get_user(id, include=include, update=True)
        self._user_ids[user.name] = user.id
        return user
