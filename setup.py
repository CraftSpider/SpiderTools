
from distutils.core import setup
import pkgutil


setup(
    name="SpiderTools",
    version="1.0",
    description="Python utility library by CraftSpider",
    author="CraftSpider",
    author_email="runetynan@gmail.com",
    url="https://github.com/craftspider/spidertools",
    packages=pkgutil.walk_packages("spidertools")
)
