
import json
import logging
import secrets
import aiohttp.web as web
import spidertools.common.clstools as clstools

from .base_handler import BaseHandler


log = logging.getLogger("spidertools.webserver.api")


@clstools.decorator
def api_handler(*, name=None):
    """
        Decorator for API handlers with method names not matching
        their command names.
    :param name: Command name for the function
    :return: Wrapper function to set the name
    """

    def predicate(func):
        func.__api_name__ = name if name else func.__name__
        return func

    return predicate


@clstools.noarg_decorator
def auth_required(func):
    func.__api_auth__ = True
    return func


class APIHandler(BaseHandler):
    """
        Handler for a Webserver API. Parses and dispatches requests, returning their result
    """

    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        """
            Initialize a subclass of this API handler. Handles methods
            with an API path different from their actual name
        :param kwargs: Arguments to class creation
        """
        cls._handlers = {}
        for name in dir(cls):
            item = getattr(cls, name)
            if hasattr(item, "__api_name__"):
                cls._handlers[item.__api_name__] = item
            elif name.startswith("on_"):
                cls._handlers[name[3:]] = item
        super().__init_subclass__(**kwargs)

    def _check_token(self, user, token):
        """
            Check whether a token for a given user is correct
        :param user: Username to check against
        :param token: Token sent by user
        :return: Whether token is correct
        """
        if not user or not token:
            return False

        server_token = self.app["settings"]["tokens"].get(user, None)
        if server_token is None:
            return False
        known = secrets.compare_digest(token, server_token)
        if not known:
            return False
        return True

    def _path_to_name(self, path):
        """
            Convert a request path into an API command name
        :param path: Request path
        :return: Command name
        """
        remove = 0
        if self.path is not None:
            remove = self.path.count("/") + 1
        return "_".join(path.lstrip("/").split("/")[remove:])

    async def get(self, request):
        """
            GET a page from the API
        :param request: aiohttp Request
        :return: Response object
        """
        log.info("API GET")
        return await self.dispatch_request("GET", request)

    async def post(self, request):
        """
            POST to the Talos API
        :param request: aiohttp Request
        :return: Response object
        """
        log.info("API POST")
        return await self.dispatch_request("POST", request)

    def json_error(self, text, status=400):
        """
            Return a JSON response indicating an error in a standard form
        :param text: Text of the error
        :param status: Status code of the response
        :return: Response object
        """
        return web.json_response(data={"error": text}, status=status)

    async def dispatch_request(self, method, request):
        """
            Dispatch a request to the API
        :param method: Method of the request, GET, POST, etc
        :param request: aiohttp Request
        :return: Response object
        """
        headers = request.headers

        # Verify token
        if hasattr(self, "__api_auth__"):
            user_token = headers.get("token")
            username = headers.get("username")
            if not self._check_token(username, user_token):
                return self.json_error("Invalid Token/Unknown User", status=403)

        # And finally we can do what the request is asking
        try:
            path = self._path_to_name(request.path)
            data = await request.json()
            return await self.dispatch(path, method, data)
        except json.JSONDecodeError:
            return self.json_error("Malformed JSON in request")

    def _get_handler(self, method, name):
        """
            Find a handler for a given method and name, if one exists
        :param method: HTTP method
        :param name: Name of the command
        :return: Handler, if one exists
        """
        handler = self._handlers.get(f"{method}_{name}", None)
        if handler is None:
            return self._handlers.get(name, None), None
        else:
            return handler, method

    async def dispatch(self, name, method, data):
        """
            Dispatch an API command for a given path with given data
        :param name: API endpoint path
        :param data: Data sent to this endpoint
        :return: Web response to return
        """
        method = method.lower()

        parser = getattr(self, "handle_" + name, None)
        if parser is not None:
            data = parser(method, data)

        handler, method = self._get_handler(method, name)
        if handler is not None:
            if method is None:
                result = await handler(self, method, data)
            else:
                result = await handler(self, data)
            return result
        else:
            return self.json_error("Unknown API Command")

