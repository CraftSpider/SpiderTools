
import types


def _mangle(cls, name):
    return f"_{cls.__name__}__{name}"


def unwrap(func):
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func


def forward_func(new, old):
    new.__name__ = old.__name__
    new.__qualname__ = old.__qualname__
    new.__doc__ = old.__doc__
    new.__annotations__ = old.__annotations__
    new.__module__ = old.__module__
    new.__wrapped__ = old


forward_class = forward_func


class Singleton:

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, _mangle(cls, "instance")):
            setattr(cls, _mangle(cls, "instance"), super().__new__(cls))
            setattr(cls, _mangle(cls, "initialized"), False)
        return getattr(cls, _mangle(cls, "instance"))

    def __init_subclass__(cls, **kwargs):
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

    def wrapper(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], (types.FunctionType, type)):
            return func()(args[0])
        else:
            return func(*args, **kwargs)

    forward_func(wrapper, func)
    return wrapper


def noarg_decorator(func):

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


def _make_key(args, kwargs):
    set_vals = []

    for index, value in enumerate(args):
        if value.__hash__ is None:
            value = id(value)
        set_vals.append((index, value))
    for key, value in kwargs.items():
        if value.__hash__ is None:
            value = id(value)
        set_vals.append((key, value))

    return frozenset(set_vals)


@decorator
def invalidating_cache(*, method=False):

    def predicate(func):

        _caches[unwrap(func)] = {}

        def check_cache(*args, **kwargs):
            self = None
            if method:
                self, args = args[0], args[1:]

            _key = _make_key(args, kwargs)
            _cache = _caches[unwrap(func)]
            if _key in _cache:
                return _cache[_key]

            if method:
                out = func(self, *args, **kwargs)
            else:
                out = func(*args, **kwargs)
            _cache[_key] = out
            return out

        forward_func(check_cache, func)
        return check_cache

    return predicate


@decorator
def cache_invalidator(*, func=None, method=False, args=None, kwargs=None):

    if func is not None:
        if isinstance(func, (list, tuple, set)):
            func = tuple(func)
        else:
            func = (func,)

    if args is not None:
        if isinstance(args, (list, tuple, set)):
            args = set(args)
        else:
            raise TypeError("Args must be list of integer positions")

    if kwargs is not None:
        if isinstance(kwargs, (list, tuple, set)):
            kwargs = set(kwargs)
        else:
            raise TypeError("Kwargs must be list of string argnames")

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
                    # TODO: Remove from cache based on this functions args
                    _caches[item].clear()

            _func(*_args, **_kwargs)

        forward_func(invalidate_cache, _func)
        return invalidate_cache

    return predicate
