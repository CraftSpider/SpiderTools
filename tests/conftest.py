
import spidertools.discord.bot as bot
import pytest
import _pytest.python as py
import asyncio


class AsyncFunction(pytest.Function):

    def runtest(self):
        loop = asyncio.get_event_loop()
        testfunction = self.obj
        funcargs = self.funcargs
        testargs = {}
        for arg in self._fixtureinfo.argnames:
            testargs[arg] = funcargs[arg]
        loop.run_until_complete(testfunction(**testargs))
        return True


def pytest_pycollect_makeitem(collector, name, obj):
    if collector.istestfunction(obj, name) and asyncio.iscoroutinefunction(obj):
        module = collector.getparent(pytest.Module).obj
        clscol = collector.getparent(pytest.Class)
        cls = clscol and clscol.obj or None
        fm = collector.session._fixturemanager

        definition = py.FunctionDefinition(name=name, parent=collector, callobj=obj)
        fixinfo = fm.getfixtureinfo(definition, obj, cls)

        metafunc = py.Metafunc(definition, fixinfo, collector.config, cls=cls, module=module)

        if not metafunc._calls:
            return AsyncFunction(name, parent=collector, fixtureinfo=fixinfo)
        else:
            output = []
            for callspec in metafunc._calls:
                subname = f"{name}[{callspec.id}]"
                output.append(AsyncFunction(
                    name=subname,
                    parent=collector,
                    callspec=callspec,
                    callobj=obj,
                    fixtureinfo=fixinfo,
                    keywords={callspec.id: True},
                    originalname=name
                ))
            return output


class TestBot(bot.ExtendedBot):
    startup_extensions = ("extension1",)
    extension_dir = "tests.test_extensions"


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    import logging
    import sys
    log = logging.getLogger("spidertools")
    log.setLevel(logging.DEBUG)
    format = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handle = logging.StreamHandler(stream=sys.stdout)
    handle.setFormatter(format)
    log.addHandler(handle)


@pytest.fixture()
def testbot():
    return TestBot("^")

