
import spidertools.common.nano as nano


async def test_nanoclient():
    client = nano.NanoClient("talosbot", "***REMOVED***")
    await client.init()

    marcy = await client.get_user("marcyt")
    projects = await marcy.get_projects()
    user = await projects[0].get_user()
    assert marcy == user
