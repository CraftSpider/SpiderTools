
import types


def _mangle(cls, name):
    """
        Given a class and a name, apply python name mangling to it
    :param cls: Class to mangle with
    :param name: Name to mangle
    :return: Mangled name
    """
    return f"_{cls.__name__}__{name}"


def unwrap(func):
    """
        Fully unwrap a wrapped object
    :param func: Function to unwrap
    :return: Unwrapped function
    """
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func


def forward_func(new, old):
    """
        'Forward' a function / class, by setting the first arg's special values
        to those of the second arg. This allows wrappers returned by decorators to
        look right in call stacks and etc, while setting __wrapped__ so they are recognized
        as decorators
    :param new: Function / class to forward
    :param old: Function / class it is wrapping
    """
    new.__name__ = old.__name__
    new.__qualname__ = old.__qualname__
    new.__doc__ = old.__doc__
    new.__annotations__ = old.__annotations__
    new.__module__ = old.__module__
    new.__wrapped__ = old


forward_class = forward_func


class Singleton:
    """
        Class that is only constructed and initialized once, then future constructions
        return the already constructed class. When used in a class hierarchy, all children of a
        singleton can call their parent's constructors exactly once
    """

    def __new__(cls, *args, **kwargs):
        """
            Construct a new Singleton. Checks for an instance, if one doesn't exist,
            creates one
        :param args: Ignored
        :param kwargs: Ignored
        :return: New or existing instance
        """
        if not hasattr(cls, _mangle(cls, "instance")):
            setattr(cls, _mangle(cls, "instance"), super().__new__(cls))
            setattr(cls, _mangle(cls, "initialized"), False)
        return getattr(cls, _mangle(cls, "instance"))

    def __init_subclass__(cls, **kwargs):
        """
            Prepare a subclass to only have its init run once. Wraps the init to check if it
            has been run before
        :param kwargs: Ignored
        """
        if cls.__init__ != object.__init__:
            old_init = cls.__init__

            def new_init(self, *args, **kwargs):
                _cls = type(self)
                if getattr(_cls, _mangle(_cls, "initialized")) is not True:
                    old_init(self, *args, **kwargs)
                    setattr(_cls, _mangle(_cls, "initialized"), True)

            forward_func(new_init, old_init)
            cls.__init__ = new_init


def decorator(func):
    """
        Mark a function as a decorator. Allows usage when decorating with or without (), without
        is the same as a no-arg call. All decorators must return a predicate that will be actually
        called with the func. This function itself must not have ()
    :param func: Function to mark as decorator
    :return: Forwarded function wrapper
    """

    def wrapper(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], (types.FunctionType, type)):
            return func()(args[0])
        else:
            return func(*args, **kwargs)

    forward_func(wrapper, func)
    return wrapper


def noarg_decorator(func):
    """
        Mark a function as a no-arg decorator. Allows usage when decorating with or without ().
        Either way ends up just calling the function with what it is decorating, no predicate
        required (Unlike decorator) allowing for more readable / less complex code
    :param func: Function to mark as no-arg decorator
    :return: Forwarded function wrapper
    """

    def wrapper(_func=None):
        if isinstance(_func, (types.FunctionType, type)):
            return func(_func)
        elif _func is None:
            return wrapper
        else:
            raise TypeError(f"Decorator is no-arg, expected nothing, not {_func}")

    forward_func(wrapper, func)
    return wrapper


_caches = {}


def _make_unique(key, val):
    if type(val).__hash__ is None:
        val = str(val)
    return key, val


def _make_key(args, kwargs):
    """
        Generate a unique key from a set of arguments. If the arguments are all hashable,
        then their hash is used. Otherwise, their ID is used. Hashables are thus compared
        same by value equality, non-hashables by identity
    :param args: Positional arguments to key on
    :param kwargs: Keyword arguments to key on
    :return: FrozenSet that represents this set of arguments
    """
    set_vals = []

    for index, value in enumerate(args):
        set_vals.append(_make_unique(index, value))
    for key, value in kwargs.items():
        set_vals.append(_make_unique(key, value))

    return frozenset(set_vals)


@decorator
def invalidating_cache(*, method=False):
    """
        Mark a function as using an 'invalidating cache', a cache that remains the same till invalidated
        by a different function call
    :param method: Whether this is a method, if so 'self' param will be ignored
    :return: Forwarded function wrapper
    """

    def predicate(func):

        _caches[unwrap(func)] = {}

        def check_cache(*args, **kwargs):
            self = None
            if method:
                self, args = args[0], args[1:]

            _key = _make_key(args, kwargs)
            _cache = _caches[unwrap(func)]
            if _key in _cache:
                print("Cache hit")
                return _cache[_key]

            if method:
                out = func(self, *args, **kwargs)
            else:
                out = func(*args, **kwargs)
            print(f"Adding {_key}")
            _cache[_key] = out
            return out

        forward_func(check_cache, func)
        return check_cache

    return predicate


def _check_cache(to_check, args, cache, generic):
    to_remove = set()
    for i in to_check:
        if generic:
            pair = (i, type(args[i]))
        else:
            pair = _make_unique(i, args[i])

        if isinstance(args, (list, tuple)) and i >= len(args):
            break
        elif isinstance(args, dict) and i not in args:
            break

        for j in cache:
            if generic:
                for k in j:
                    if k[0] == pair[0] and k[1] == pair[1]:
                        to_remove.add(j)
            else:
                if pair in j:
                    to_remove.add(j)

    return to_remove


@decorator
def cache_invalidator(*, func=None, method=False, args=None, kwargs=None, generic=True):
    """
        Mark a function as invalidating the cache of associated function(s). Optionally
        can only invalidate part of the cache, based on args/kwargs positions
    :param func: Function / tuple of functions to invalidate. If missing, invalidates everything
    :param method: Whether this function is a method. Only used if args/kwargs to key on are specified
    :param args: Optional tuple of arguments that are compared, only invalidating cached calls
                 that use the same args in the same position as the tuple
    :param kwargs: Optional tuple of argument names that are compared, only invalidating cached calls
                   that use the same kwargs as the tuple specifies
    :return: Forwarded function wrapper
    """

    if func is not None:
        if isinstance(func, (list, tuple, set)):
            func = tuple(func)
        else:
            func = (func,)

    if args is not None:
        if isinstance(args, (list, tuple, set)):
            args = set(args)
        elif isinstance(args, int):
            args = {args}
        else:
            raise TypeError("Args must be list of integer positions or single integer position")

    if kwargs is not None:
        if isinstance(kwargs, (list, tuple, set)):
            kwargs = set(kwargs)
        elif isinstance(kwargs, str):
            kwargs = {args}
        else:
            raise TypeError("Kwargs must be list of string argnames, or single string argname")

    def predicate(_func):

        def invalidate_cache(*_args, **_kwargs):

            if func is None:
                search = _caches.keys()
            else:
                search = func

            for item in search:
                item = unwrap(item)
                if args is None and kwargs is None:
                    _caches[item].clear()
                else:
                    self = None
                    if method:
                        self, _args = _args[0], _args[1:]

                    to_remove = set()
                    if args is not None:
                        to_remove |= _check_cache(args, _args, _caches[item], generic)
                    if kwargs is not None:
                        to_remove |= _check_cache(kwargs, _kwargs, _caches[item], generic)
                    for i in to_remove:
                        print(f"Removing {i}")
                        del _caches[item][i]

                    if method:
                        _args = (self,) + _args

            _func(*_args, **_kwargs)

        forward_func(invalidate_cache, _func)
        return invalidate_cache

    return predicate
