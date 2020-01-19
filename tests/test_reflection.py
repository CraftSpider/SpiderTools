
import inspect
import pytest
import spidertools.common.reflection as reflection


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
    return val.qualname.replace(".", "/")


SKIP_NAMES = {"__doc__", "__annotations__", "__cached__", "__cog_commands__", "__cog_listeners__", "__cog_name__",
              "__cog_settings__"}


@pytest.mark.parametrize("val", reflection.walk_all_items(".", skip_dirs=SKIP_DIRS, skip_names=SKIP_NAMES),
                         ids=_gen_test_id)
def test_stub(val):
    name, _, real, stub = val

    # Special case for us, because we actually see the Empty class while walking
    if inspect.isclass(stub) and stub.__name__ == "Empty" and real is reflection.Empty:
        return

    if stub is reflection.Empty:
        pytest.fail(f"Missing stub for object {name}")
    elif real is reflection.Empty:
        pytest.fail(f"Extra stub for object {name}")

    real_type = _get_type(real)
    stub_type = _get_type(stub)

    if real_type != stub_type:
        pytest.fail(f"Type mismatch for objects: {name} - Real: {real_type}, Stub: {stub_type}")

    # Doesn't work due to @overload not wrapping the original function
    """
    real_unwrapped = reflection.unwrap(real)
    stub_unwrapped = reflection.unwrap(stub)
    if inspect.isfunction(real_unwrapped) or inspect.iscoroutinefunction(real_unwrapped):
        realsig = inspect.signature(real_unwrapped)
        stubsig = inspect.signature(stub_unwrapped)
        if stubsig.return_annotation is inspect._empty:
            pytest.fail(f"Missing return annotation for stub function: {name}")
        if len(realsig.parameters) != len(stubsig.parameters):
            pytest.fail(f"Number of parameters of stub function {name} doesn't match real")

        for i in stubsig.parameters:
            param: inspect.Parameter = stubsig.parameters[i]
            if param.name in {"self", "cls", "mcs"}:
                continue
            if param.annotation is inspect._empty:
                pytest.fail(f"Missing annotation for stub parameter: {name}.{param.name}")
    """
