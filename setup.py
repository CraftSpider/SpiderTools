
from setuptools import setup, find_packages


setup(
    name="SpiderTools",
    version="1.0",
    description="Python utility library by CraftSpider",
    author="CraftSpider",
    author_email="runetynan@gmail.com",
    url="https://github.com/craftspider/spidertools",
    install_requires=["discord.py", "mysql-connector-python", "psycopg2"],
    packages=find_packages()
)
