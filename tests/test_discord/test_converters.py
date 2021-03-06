
import spidertools.discord as dutils
import datetime as dt


async def test_dateconverter():

    dconv = dutils.DateConverter()()

    assert await dconv.convert(None, "5-3-2018") == dt.date(year=2018, month=3, day=5)
    assert await dconv.convert(None, "5/3/2018") == dt.date(year=2018, month=3, day=5)
    dconv.datefmt = ("%Y-%m-%d",)
    assert await dconv.convert(None, "2018-5-3") == dt.date(year=2018, month=5, day=3)
    assert await dconv.convert(None, "2018/5/3") == dt.date(year=2018, month=5, day=3)


async def test_timeconverter():

    tconv = dutils.TimeConverter()()

    assert await tconv.convert(None, "1:53 PM") == dt.time(hour=13, minute=53)
    tconv.timefmt = ("%H:%M",)
    assert await tconv.convert(None, "13:53") == dt.time(hour=13, minute=53)
