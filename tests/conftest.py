
import spidertools.discord.bot as bot
import pytest


class TestBot(bot.ExtendedBot):
    startup_extensions = ("extension1",)
    extension_dir = "tests.test_extensions"


@pytest.fixture()
def testbot():
    return TestBot("^")

