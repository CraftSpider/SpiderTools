
from typing import Union, TypeVar, Callable, Any, Optional, overload, Iterator, Tuple, List, NamedTuple, Container, Set
from types import ModuleType
import inspect
import pathlib


_T = TypeVar("_T")


def unwrap(obj: _T) -> Union[Callable, _T]: ...

def has_doc(obj: Any) -> bool: ...

def get_doc(obj: Any) -> Optional[str]: ...

def is_docable(obj: Any) -> bool: ...

@overload
def classify_attr(cls: type, name: str, default: _T) -> Union[inspect.Attribute, _T]: ...
@overload
def classify_attr(cls: type, name: str) -> inspect.Attribute: ...

def _get_declared_type(type: type, predicate: Callable[[Any], bool] = ...) -> Iterator[Tuple[str, Any]]: ...

def _get_declared_mod(mod: ModuleType, predicate: Callable[[Any], bool] = ...) -> Iterator[Tuple[str, Any]]: ...

def get_declared(obj: Any, predicate: Callable[[Any], bool] = ...) -> Iterator[Tuple[str, Any]]: ...

def _get_undoc_type(type: type) -> List[Tuple[str, Any]]: ...

def _get_undoc_mod(mod: ModuleType) -> List[Tuple[str, Any]]: ...

def _get_undoc_pkg(pkg: str) -> List[Tuple[str, Any]]: ...

def get_undoced(obj: Union[type, ModuleType, str]) -> List[Tuple[str, Any]]: ...

def module_from_file(path: pathlib.Path, base: pathlib.Path = ...) -> ModuleType: ...

def walk_with_stub_files(base_path: str, stub_dir: str = ..., *, skip_dirs: Container[str] = ..., skip_files: Container[str] = ..., skip_hidden: bool = ...) -> Iterator[Tuple[pathlib.Path, pathlib.Path]]: ...

def walk_with_stub_modules(base_path: str, stub_dir: str = ..., *, skip_dirs: Container[str] = ..., skip_files: Container[str] = ...) -> Iterator[Tuple[ModuleType, ModuleType]]: ...

def _clean_name(name: str, real: Any, stub: Any) -> str: ...

class ItemGenResult(NamedTuple):
    name: str
    real: Any
    stub: Any

def _walk_items_recurse(c_orig: Any, s_orig: Any, name_cleaner: Callable[[str, Any, Any], str]) -> Set[Tuple[str, Any, Any]]: ...

def walk_all_items(base_path: str, stub_dir: str = ..., *, skip_dirs: Container[str] = ..., skip_files: Container[str] = ..., name_cleaner: Callable[[str, Any, Any], str] = ...) -> Set[Tuple[str, Any, Any]]: ...
