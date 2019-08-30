
import inspect
import pytest
import spidertools.common.reflection as reflection
from collections import namedtuple


@pytest.mark.parametrize("package", ["command_lang", "common", "discord", "math", "twitch", "webserver"])
def test_docs(package):
    result = reflection.get_undoced(f"spidertools.{package}")
    assert len(result) is 0, f"Missing documentation on: {', '.join(map(lambda x: x[0], result))}"


SKIP_DIRS = {"stubs", "__pycache__", "tests"}


def test_stub_files():
    missing = []

    for code, stub in reflection.walk_with_stub_files(".", skip_dirs=SKIP_DIRS):
        if not stub.exists() or not stub.is_file():
            missing.append(code)

    assert len(missing) == 0, f"Missing stub files for: {', '.join(map(lambda x: x.name, missing))}"


def _get_type(obj):
    if inspect.isclass(obj):
        return 'class'
    elif inspect.isroutine(obj):
        return 'async' if inspect.iscoroutinefunction(obj) or inspect.isasyncgenfunction(obj) else 'sync'
    else:
        return 'unknown'


def _gen_test_id(val):
    return val.name.replace(".", "/")


@pytest.mark.parametrize("val", reflection.walk_all_items(".", skip_dirs=SKIP_DIRS), ids=_gen_test_id)
def test_stub(val):
    name, real, stub = val
    if stub is None:
        pytest.fail(f"Missing stub for object {name}")
    elif real is None:
        pytest.fail(f"Extra stub for object {name}")

    real_type = _get_type(real)
    stub_type = _get_type(stub)

    if real_type != stub_type:
        pytest.fail(f"Type mismatch for objects: {name} - Real: {real_type}, Stub: {stub_type}")
