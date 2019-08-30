
import discord.ext.commands as commands
import spidertools.discord as dutils
import os
import sys
import inspect
import importlib
import importlib.util
import importlib.machinery
import pkgutil
import pathlib
import typing
from collections import namedtuple


def unwrap(obj):
    """
        Unwrap a wrapped object. Different from 'inspect.unwrap' in that it will
        also unwrap method objects into the function they wrap. If the object wraps
        no other objects, it will be returned unchanged
    :param obj: Object to unwrap
    :return: Unwrapped object
    """
    while hasattr(obj, "__func__") or hasattr(obj, "__wrapped__"):
        if getattr(obj, "__func__", None) is not None:
            obj = obj.__func__
        elif getattr(obj, "__wrapped__", None) is not None:
            obj = obj.__wrapped__
    return obj


def has_doc(obj):
    """
        Return whether an object has a docstring
    :param obj: Object to check for docstring on
    :return: Whether the object has a docstring
    """
    return hasattr(obj, "__doc__") and isinstance(obj.__doc__, str)


def get_doc(obj):
    """
        Get the docstring of an object. This differs from the inspect equivalent
        in that it will not attempt to find a doc on parent classes or such, only
        returning the immediate docstring, though it will unwrap the object first
    :param obj: Object to get docstring from
    :return: Docstring for the object, if it exists
    """
    try:
        doc = obj.__doc__
    except AttributeError:
        return None
    if not isinstance(doc, str):
        return None
    return inspect.cleandoc(doc)


def is_docable(obj):
    """
        Check whether an object 'can' have a doc. This doesn't determine whether a `__doc__` method could
        be present, but whether the object is something which could be reasonably expected
        to have said attribute. Example include a function or a property, but not a string attribute or
        an instance of any arbitrary class.
    :param obj: Object to check for docability
    :return: Whether the object is 'docable'
    """
    if isinstance(obj, commands.Command) or isinstance(obj, dutils.EventLoop):
        return True
    return inspect.isroutine(obj) or inspect.isclass(obj) or isinstance(obj, property) or hasattr(obj, "__wrapped__")


def classify_attr(cls, name, default=...):
    """
        Classify a class attribute. Determine on which class it is defines, and guess at its type
    :param cls: Class to classify an attribute on
    :param name: Name of the attribute to classify
    :param default: Default value to return if attribute isn't found
    :return: inspect.Attribute object with info about the desired attribute
    """
    import types
    mro = inspect.getmro(cls)
    metamro = inspect.getmro(type(cls))  # for attributes stored in the metaclass
    metamro = tuple(cls for cls in metamro if cls not in (type, object))
    class_bases = (cls,) + mro
    all_bases = class_bases + metamro

    homecls = None
    get_obj = None
    dict_obj = None
    try:
        if name == '__dict__':
            raise Exception("__dict__ is special, don't want the proxy")
        get_obj = getattr(cls, name)
    except Exception:
        pass
    else:
        homecls = getattr(get_obj, "__objclass__", homecls)
        if homecls not in class_bases:
            # if the resulting object does not live somewhere in the
            # mro, drop it and search the mro manually
            homecls = None
            last_cls = None
            # first look in the classes
            for srch_cls in class_bases:
                srch_obj = getattr(srch_cls, name, None)
                if srch_obj is get_obj:
                    last_cls = srch_cls
            # then check the metaclasses
            for srch_cls in metamro:
                try:
                    srch_obj = srch_cls.__getattr__(cls, name)
                except AttributeError:
                    continue
                if srch_obj is get_obj:
                    last_cls = srch_cls
            if last_cls is not None:
                homecls = last_cls
    for base in all_bases:
        if name in base.__dict__:
            dict_obj = base.__dict__[name]
            if homecls not in metamro:
                homecls = base
            break
    if homecls is None:
        # unable to locate the attribute anywhere, most likely due to
        # buggy custom __dir__; discard and move on
        if default is ...:
            raise AttributeError(f"type object '{cls.__name__}' has no attribute '{name}'")
        else:
            return default
    obj = get_obj if get_obj is not None else dict_obj
    # Classify the object or its descriptor.
    if isinstance(dict_obj, (staticmethod, types.BuiltinMethodType)):
        kind = "static method"
        obj = dict_obj
    elif isinstance(dict_obj, (classmethod, types.ClassMethodDescriptorType)):
        kind = "class method"
        obj = dict_obj
    elif isinstance(dict_obj, property):
        kind = "property"
        obj = dict_obj
    elif inspect.isroutine(obj):
        kind = "method"
    else:
        kind = "data"
    return inspect.Attribute(name, kind, homecls, obj)


def _get_declared_type(type, predicate=None):
    """
        Get all the attributes of a type that are declared by that type
    :param type: Type to get declared attributes of
    :param predicate: Predicate to filter out attributes
    :return: Tuple containing name and value of declared attributes
    """
    attrs = inspect.classify_class_attrs(type)
    for item in attrs:
        if item.defining_class != type or\
                (inspect.isfunction(item.object) and getattr(item.object, "__module__", None) != type.__module__):
            continue
        if predicate is None or predicate(item.object):
            yield item.name, item.object


MOD_VARS = {"__cached__", "__doc__", "__file__", "__name__", "__package__"}


def _get_declared_mod(mod, predicate=None):
    """
        Get all the attributes of a module that are declared by that module
    :param mod: Module to get declared attributes of
    :param predicate: Predicate to filter out attributes
    :return: Tuple containing name and value of declared attributes
    """
    mod_path = getattr(mod, "__file__", None)
    if mod_path is not None:
        mod_path = pathlib.Path(mod_path).resolve()

    unsure = []
    modules = []
    for name, obj in inspect.getmembers(mod):
        if inspect.ismodule(obj):
            modules.append(obj)
            continue
        elif name == "__builtins__" or not (predicate is None or predicate(obj)):
            continue

        try:
            obj_path = pathlib.Path(inspect.getfile(obj)).resolve()
            if obj_path == mod_path:
                yield name, obj
        except TypeError:
            if hasattr(obj, "__module__") and mod.__name__ == obj.__module__:
                yield name, obj
            elif name in MOD_VARS:
                yield name, obj
            elif not hasattr(obj, "__module__"):
                print(f"Not sure whether part of module or not: {name} - {obj}")
                unsure.append((name, obj))

    for name, obj in unsure:
        for submod in modules:
            if hasattr(submod, name):
                break
        else:
            yield name, obj


def get_declared(obj, predicate=None):
    """
        Get all the attributes on an arbitrary object
    :param obj: Object to get attributes of
    :param predicate: Predicate to filter out attributes
    :return: Tuple containing name and value of declared attributes
    """
    if inspect.ismodule(obj):
        yield from _get_declared_mod(obj, predicate)
    elif inspect.isclass(obj):
        yield from _get_declared_type(obj, predicate)
    else:
        yield from _get_declared_type(obj.__class__, predicate)


def _get_undoc_type(type):
    """
        Get a list of all the undocumented attributes of a type
    :param type: Type to get undoced attributes of
    :return: List of undocumented attributes
    """
    out = []

    if not has_doc(type):
        out.append((type.__name__, type))

    for name, obj in get_declared(type, is_docable):
        if inspect.isclass(obj):
            out.extend(get_undoced(obj))
        elif isinstance(obj, commands.Command) or isinstance(obj, dutils.EventLoop):
            if not has_doc(obj.callback) or obj.description is "":
                out.append((name, obj))
        else:
            obj = unwrap(obj)
            if not has_doc(obj):
                out.append((name, obj))
    return out


def _get_undoc_mod(mod):
    """
        Get a list of all the undocumented attributes of a module
    :param mod: Module to get undoced attributes of
    :return: List of undocumented attributes
    """
    out = []
    for name, member in get_declared(mod, is_docable):
        if inspect.isclass(member):
            out.extend(get_undoced(member))
        elif not has_doc(member):
            out.append((name, member))
    return out


def _get_undoc_pkg(pkg):
    """
        Get a list of all the undocumented attributes of a package
    :param type: Package path to get undoced attributes of
    :return: List of undocumented attributes
    """
    found = False
    result = []
    for finder, pname, ispkg in pkgutil.walk_packages([f"./{pkg.replace('.', '/')}"], f"{pkg}."):
        found = True
        if ispkg:
            continue
        mod = importlib.import_module(pname)
        result.extend(_get_undoc_mod(mod))
    if not found:
        raise FileNotFoundError("Unable to find any packages for the specified name")
    return result


def get_undoced(obj):
    """
        Get a list of all the undocumented attributes of any object
    :param type: Object to get undoced attributes of
    :return: List of undocumented attributes
    """
    if inspect.isclass(obj):
        return _get_undoc_type(obj)
    elif inspect.ismodule(obj):
        return _get_undoc_mod(obj)
    elif isinstance(obj, str):
        return _get_undoc_pkg(obj)
    else:
        raise TypeError("get_undoced only valid for class, module, or package name")


def module_from_file(path, base=None):
    """
        From a path, load the file as a python module and add it to `sys.modules`.
        Assumes the module name is just the filename of the path, unless base is supplied,
        in which case the module path is computer relative to base
    :param path: Path of a file to load as a module
    :param base: Base path for modules that are interpreted as part of packages
    :return: New module object from path
    """
    path = path.resolve()
    base = base.resolve()

    # Figure out what name this module/package should have
    temp = path.with_suffix("")
    package = path.is_dir()
    if base is None:
        name = temp.name
    else:
        temp = temp.relative_to(base)
        name = ".".join(temp.parts)

    if name in sys.modules:
        return sys.modules[name]

    # Need to make sure parent packages are imported first
    parent_mod = None
    child_name = None
    if "." in name:
        _, _, child_name = name.rpartition(".")
        parent_mod = module_from_file(path.parent, base=base)

    # Actually load and execute the
    if package:
        path = path / "__init__.py"

    loader = importlib.machinery.SourceFileLoader(name, path.__fspath__())
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    mod = importlib.util.module_from_spec(spec)
    if name not in sys.modules:
        sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except BaseException as e:
        del sys.modules[name]
        raise

    if parent_mod is not None:
        setattr(parent_mod, child_name, mod)

    return mod


def walk_with_stub_files(base_path, stub_dir="stubs", *, skip_dirs=None, skip_files=None, skip_hidden=True):
    """
        Walk a directory, from base_path, yielding all files not in `skip_files` and not in a directory in `skip_dirs`.
        Also yields the path for an associated stub file based on `stub_dir`, whether or not the file exists
    :param base_path: Base path to walk
    :param stub_dir: Subdirectory where stub files are located
    :param skip_dirs: Directory names to skip while walking
    :param skip_files: Filenames to skip while walking
    :param skip_hidden: Whether to skip hidden directories
    :return: Tuple of (Code path, Stub path)
    """

    base_path = pathlib.Path(base_path)
    base_stub_path = base_path / stub_dir
    if skip_dirs is None:
        skip_dirs = {stub_dir, "__pycache__"}
    if skip_files is None:
        skip_files = {"__init__.py", "__main__.py", "setup.py"}

    for path, dirs, files in os.walk(base_path):
        root_path = pathlib.Path(path)
        stub_path = base_stub_path / root_path.relative_to(base_path)

        remove = []
        for item in dirs:
            if (skip_hidden and item.startswith(".")) or item in skip_dirs:
                remove.append(item)
        for item in remove:
            dirs.remove(item)

        files = list(filter(lambda x: x not in skip_files and x.endswith(".py"), files))

        for file in files:
            code_file = root_path / file
            stub_file = (stub_path / file).with_suffix(".pyi")
            yield code_file, stub_file


def walk_with_stub_modules(base_path, stub_dir="stubs", *, skip_dirs=None, skip_files=None):
    """
        Walk a directory as with `walk_with_stub_files`, but load each file as a python module as
        well. Does not yield a code module if the associated stub module doesn't exist.
    :param base_path: Base path to walk
    :param stub_dir: Subdirectory where stub files are located
    :param skip_dirs: Directory names to skip while walking
    :param skip_files: Filenames to skip while walking
    :return: Tuple of (Code module, Stub module)
    """
    base_path = pathlib.Path(base_path)

    for code, stub in walk_with_stub_files(base_path, stub_dir, skip_dirs=skip_dirs, skip_files=skip_files):
        if not code.exists() or not stub.exists():
            continue

        code_mod = module_from_file(code, base_path)
        stub_mod = module_from_file(stub, base_path)

        yield code_mod, stub_mod


def _clean_name(name, qualname, real, stub):
    """
        Return a 'cleaned' name of an object from walking items.
    :param name: Name to clean
    :param real: Real object
    :param stub: Stub object
    :return: New 'clean' name
    """
    return name


class ItemGenResult(typing.NamedTuple):
    name: str
    qualname: str
    code: typing.Any
    stub: typing.Any

    def __hash__(self):
        """
            Generate a hash for an ItemGenResult. Hash only on the qualname, it's the only value
            we care about the hash of
        :param self: ItemGenResult object
        :return: Hash of self
        """
        return hash(self.qualname)


class Empty:
    """
        Sentinel value for the recursive walk function
    """


def _walk_items_recurse(c_orig, s_orig, *state, qual=None):
    """
        Inner recursion loop for walking all the items in a module
    :param c_orig: Code object to walk
    :param s_orig: Stub object to walk
    :return: Set of names, code objects, and stub objects
    """
    pred, name_cleaner, skip_names = state
    if qual is None:
        qual = c_orig.__name__
    else:
        qual += "." + c_orig.__name__

    out = set()
    # TODO: Use custom predicate, fix hashability issues
    # pred = lambda x: inspect.isroutine(x) or inspect.isclass(x) or inspect.ismethoddescriptor(x)

    for name, c_obj in get_declared(c_orig, predicate=pred):
        if name in skip_names:
            continue
        s_obj = getattr(s_orig, "__dict__", {}).get(name, None) or getattr(s_orig, name, Empty)
        new_qual = qual + "." + name
        out.add(ItemGenResult(name_cleaner(name, new_qual, c_obj, s_obj), new_qual, c_obj, s_obj))
        if isinstance(c_obj, type) and s_obj is not Empty:
            out.update(_walk_items_recurse(c_obj, s_obj, *state, qual=qual))
    for name, s_obj in get_declared(s_orig, predicate=pred):
        if name in skip_names:
            continue
        c_obj = getattr(c_orig, "__dict__", {}).get(name, None) or getattr(c_orig, name, Empty)
        new_qual = qual + "." + name
        out.add(ItemGenResult(name_cleaner(name, new_qual, c_obj, s_obj), new_qual, c_obj, s_obj))
        if isinstance(s_obj, type) and c_obj is not Empty:
            out.update(_walk_items_recurse(c_obj, s_obj, *state, qual=qual))

    return out


def walk_all_items(base_path, stub_dir="stubs", predicate=None, *, skip_dirs=None, skip_files=None, skip_names=None, name_cleaner=_clean_name):
    """
        Walk a directory as with `walk_with_stub_files`, but yield every single python variable, function, and class
        in all modules along the way. A very powerful introspection function, as it recurses into classes, but
        automatically filters out all values not declared in that file
    :param base_path: Base path to walk
    :param stub_dir: Subdirectory where stub files are located
    :param predicate: A function applied to each object, should return whether to skip the object. Skipped object's
                      child attributes will also be skipped
    :param skip_dirs: Directory names to skip while walking
    :param skip_files: Filenames to skip while walking
    :param skip_names: Attribute names to skip while walking
    :param name_cleaner: A callable accepting 4 parameters (name, qualname, code, stub) that will return the name of
                         the object/attribute
    :return: Set of namedtuple containing the clean name, real value, and stub value of every object found
    """
    if skip_names is None:
        skip_names = {"__doc__", "__annotations__", "__cached__"}
    if predicate is None:
        predicate = lambda x: not isinstance(x, (typing.TypeVar, typing._SpecialForm))

    out = set()
    for code, stub in walk_with_stub_modules(base_path, stub_dir=stub_dir, skip_dirs=skip_dirs, skip_files=skip_files):
        out.update(_walk_items_recurse(code, stub, predicate, name_cleaner, skip_names))
    return sorted(list(out), key=lambda x: x.qualname)
