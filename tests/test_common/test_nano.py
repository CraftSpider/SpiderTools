
import spidertools.common.nano as nano
import os


async def test_nanoclient():
    client = nano.NanoClient("talosbot", os.getenv("TALOS_PSWD"))
    await client.init()

    marcy = await client.get_user("marcyt")
    projects = await marcy.get_projects()
    user = await projects[0].get_user()
    assert marcy == user

    await client.get_fundometer()
