
from . import types


class NanoException(Exception):
    """
        Base exception for Nano errors
    """

    def __init__(self):
        """
            Initialize exception, takes no arguments
        """
        super().__init__()

    def _set_message(self, *args):
        """
            Internal method used to set the exception message after creation
        :param args: Arguments to set for message
        """
        super().__init__(args)


class InvalidLogin(NanoException):
    """
        Thrown if the client couldn't log-in to the site
    """

    def __init__(self, msg):
        """
            Initialize exception. Take the login failure message
        :param msg: Message returned by failure
        """
        self._set_message(msg)


class NotFound(NanoException):
    """
        If the requested NaNo User does not exist or is innacessible
    """

    TYPE_MAP = {}

    def __new__(cls, t, msg):
        if issubclass(t, types.NanoObj):
            return super().__new__(cls.TYPE_MAP[t.TYPE])
        return super().__new__(cls)

    def __init__(self, t, msg):
        """
            Initialize exception. Takes the username that couldn't be found as an input
        :param obj: Username of the User that couldn't be found
        """
        self._set_message(msg)

    def __init_subclass__(cls, **kwargs):
        NotFound.TYPE_MAP[cls.TYPE] = cls


class UserNotFound(NotFound):
    """
        Error thrown if the object not found is a user
    """

    TYPE = "users"


class ProjectNotFound(NotFound):
    """
        Error thrown if the object not found is a novel
    """

    TYPE = "projects"
