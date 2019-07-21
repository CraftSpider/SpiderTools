
from distutils.core import setup


setup(
    name="SpiderTools",
    version="1.0",
    description="Python utility library by CraftSpider",
    author="CraftSpider",
    author_email="runetynan@gmail.com",
    url="https://github.com/craftspider/spidertools",
    packages=[
        "spidertools",
        "spidertools.common",
        "spidertools.discord",
        "spidertools.twitch",
        "spidertools.webserver",
        "spidertools.command_lang"
    ]
)
