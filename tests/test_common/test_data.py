import spidertools.common.data as data
import spidertools.discord.events as events
import pytest


def test_row():

    with pytest.raises(TypeError):
        row = data.Row([])


def test_multirow():

    with pytest.raises(TypeError):
        multirow = data.MultiRow({})


def test_sql_convertable():

    with pytest.raises(TypeError):
        sqlconvertable = data.SqlConvertable()


def test_event_period():

    period = events.EventPeriod("10m")

    assert period.minutes == 10
    assert period.hours == 0
    assert period.days == 0
    assert period.sql_safe() == "10m"
    assert int(period) == 600

    period = events.EventPeriod("1h")

    assert period.minutes == 0
    assert period.hours == 1
    assert period.days == 0
    assert period.sql_safe() == "1h"
    assert int(period) == 3600

    period = events.EventPeriod("1d40m")

    assert period.minutes == 40
    assert period.hours == 0
    assert period.days == 1
    assert period.sql_safe() == "1d40m"
    assert int(period) == 86400 + 2400

