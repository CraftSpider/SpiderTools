
import aiohttp
import io
import logging
import json
import datetime as dt

from spidertools.common import utils


log = logging.getLogger("talos.utils.client")


class TalosHTTPClient:
    """
        Extension of the aiohttp ClientSession to provide utility methods for getting certain sites and such,
        and automatically handling various tokens for those sites.
    """

    __slots__ = ("nano_tries", "last_guild_count", "__tokens", "client")

    TALOS_URL = "https://talosbot.org/"
    BOTLIST_URL = "https://discordbots.org/"
    BTN_URL = "https://www.behindthename.com/"
    CAT_URL = "https://api.thecatapi.com/v1/"
    XKCD_URL = "https://xkcd.com/"
    SMBC_URL = "https://smbc-comics.com/"

    def __init__(self, *args, tokens=None, **kwargs):
        """
            Create a Talos HTTP Client object
        :param args: arguments to pass on
        :param kwargs: keyword args to use and pass on
        """
        self.__tokens = tokens if tokens else {}
        self.nano_tries = 0
        self.last_guild_count = 0
        self.client = aiohttp.ClientSession(*args, **kwargs)

    async def close(self):
        """
            Close this HTTP Client object
        """
        await self.client.close()

    async def get_site(self, url, **kwargs):
        """
            Get the text of a given URL
        :param url: url to get text from
        :param kwargs: keyword args to pass to the GET call
        :return: text of the requested page
        """
        async with self.client.get(url, **kwargs) as response:
            return utils.to_dom(await response.text())

    async def server_post_commands(self, commands):
        """
            Post a commands JSON object to the Talos Server. Relies on the 'webserver' token existing.
        :param commands: Dict representing a Command JSON object
        """
        headers = {
            "Token": self.__tokens["webserver"],
            "User": "Talos"
        }
        await self.client.post(self.TALOS_URL + "api/commands", json=commands, headers=headers)

    async def botlist_post_guilds(self, num):
        """
            Post a number of guilds to the discord bot list. Will only post if there's a botlist token available
            and the passed number is different from the last passed number
        :param num: Number of guilds to post
        """
        if num == self.last_guild_count or self.__tokens.get("botlist", "") == "":
            return
        log.info("Posting guilds to Discordbots")
        self.last_guild_count = num
        headers = {
            'Authorization': self.__tokens["botlist"]
        }
        data = {'server_count': num}
        api_url = self.BOTLIST_URL + 'api/bots/199965612691292160/stats'
        await self.client.post(api_url, json=data, headers=headers)

    async def btn_get_names(self, gender="", usage="", number=1, surname=False):
        """
            Get names from Behind The Name
        :param gender: gender to restrict names to. m or f
        :param usage: usage to restrict names to. eng for english, see documentation
        :param number: number of names to generate. Between 1 and 6.
        :param surname: whether to generate a random surname. Yes or No
        :return: List of names generated or None if failed
        """
        surname = "yes" if surname else "no"
        gender = "&gender="+gender if gender else gender
        usage = "&usage="+usage if usage else usage
        url = self.BTN_URL + f"api/random.php?key={self.__tokens['btn']}&randomsurname={surname}&number={number}"\
                             f"{gender}{usage}"
        async with self.client.get(url) as response:
            if response.status == 200:
                doc = utils.to_dom(await response.text())
                return [x.innertext for x in doc.get_by_tag("name")]
            else:
                log.warning(f"BTN returned {response.status}")
                return []

    async def get_cat_pic(self):
        """
            Get a random cat picture from The Cat API
        :return: A discord.File with a picture of a cat.
        """
        async with self.client.get(self.CAT_URL + f"images/search?api_key={self.__tokens['cat']}&type=jpg,png") as response:
            data = json.loads(await response.text())[0]
        async with self.client.get(data["url"]) as response:
            data["filename"] = data["url"].split("/")[-1]
            data["img_data"] = io.BytesIO(await response.read())
        return data

    async def get_xkcd(self, xkcd):
        """
            Get the data from an XKCD comic and return it as a dict
        :param xkcd: XKCD to get, or None if current
        :return: Dict of JSON data
        """
        async with self.client.get(self.XKCD_URL + (f"{xkcd}/" if xkcd else "") + "info.0.json") as response:
            data = await response.text()
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return None
        async with self.client.get(data["img"]) as response:
            data["filename"] = data["img"].split("/")[-1]
            data["img_data"] = io.BytesIO(await response.read())
        return data

    async def get_smbc_list(self):
        """
            Get the list of current SMBC comics from the smbc archive
        :return: List of elements
        """
        async with self.client.get(self.SMBC_URL + "comic/archive/") as response:
            dom = utils.to_dom(await response.text())
            selector = dom.get_by_name("comic")
            return selector.child_nodes[1:]

    async def get_smbc(self, smbc):
        """
            Get the data for an SMBC from its ID
        :param smbc: SMBC to get, or None if current
        :return: Dict of JSON data
        """
        data = {}
        if isinstance(smbc, int):
            url = self.SMBC_URL + f"index.php?db=comics&id={smbc}"
        else:
            url = self.SMBC_URL + f"comic/{smbc}"
        async with self.client.get(url, headers={"user-agent": ""}) as response:
            dom = utils.to_dom(await response.text())
            data["title"] = "-".join(dom.get_by_tag("title")[0].innertext.split("-")[1:]).strip()
            comic = dom.get_by_id("cc-comic")
            if comic is None:
                return None
            data["img"] = comic.get_attribute("src")
            data["alt"] = comic.get_attribute("title")
            time = dom.get_by_class("cc-publishtime")[0]
            date = dt.datetime.strptime(time.innertext, "Posted %B %d, %Y at %I:%M %p")
            data["time"] = date
        async with self.client.get(data["img"]) as response:
            data["filename"] = data["img"].split("/")[-1]
            data["img_data"] = io.BytesIO(await response.read())
        return data
