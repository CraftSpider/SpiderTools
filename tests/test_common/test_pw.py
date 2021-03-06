
import pytest

import datetime as dt
import spidertools.common as tutils


def test_pw_member():
    pw_member1 = tutils.PWMember({"name": "Test", "discrim": "0001"})
    d_member2 = {"name": "Test", "discrim": "0002"}
    pw_member2 = tutils.PWMember(d_member2)
    pw_member3 = tutils.PWMember(d_member2)

    assert str(pw_member1) == str({"name": "Test", "discrim": "0001"}), "Failed string conversion"

    assert pw_member1 != pw_member2, "Failed difference"
    assert pw_member2 == pw_member3, "Failed equivalence"

    assert pw_member1.get_started() is False, "Claims started before start"
    assert pw_member1.get_finished() is False, "Claims finished before finish"
    assert pw_member1.get_len() is None, "Length should be None before finish"

    with pytest.raises(ValueError):
        pw_member1.begin("Hello World!")
        pytest.fail("Allowed non-time beginning")
    d_time = dt.datetime(year=2017, month=12, day=31)
    pw_member1.begin(d_time)

    assert pw_member1.get_started() is True, "Claims not started after start"
    assert pw_member1.get_finished() is False, "Claims finished before finish"
    assert pw_member1.get_len() is None, "Length should be None before finish"

    with pytest.raises(ValueError):
        pw_member1.finish(2017.3123)
        pytest.fail("Allowed non-time ending")
    d_time = d_time.replace(minute=30)
    pw_member1.finish(d_time)

    assert pw_member1.get_started() is True, "Claims not started after start"
    assert pw_member1.get_finished() is True, "Claims not finished after finish"
    assert pw_member1.get_len() == dt.timedelta(minutes=30), "Length should be 30 minutes after finish"


def test_pw():  # TODO: Add testing for timezones, for now it's just going with UTC always
    pw = tutils.PW()

    assert pw.get_started() is False, "Claims started before start"
    assert pw.get_finished() is False, "Claims finished before finish"

    tz = dt.timezone(dt.timedelta(), "UTC")
    d_member1 = {"name": "Test", "discrim": "0001"}
    d_member2 = {"name": "Test", "discrim": "0002"}
    d_member3 = {"name": "Test", "discrim": "0003"}
    assert pw.join(d_member1, tz) is True, "New member not successfully added"
    assert pw.join(d_member1, tz) is False, "Member already in PW still added"
    assert pw.leave(d_member1, tz) is 0, "Existing member couldn't leave"
    assert d_member1 not in pw.members, "Member leaving before start is not deleted"
    assert pw.leave(d_member1, tz) is 1, "Member successfully left twice"
    assert pw.leave(d_member2, tz) is 1, "Member left before joining"

    pw = tutils.PW()

    pw.join(d_member1, tz)
    pw.begin(tz)
    assert pw.get_started() is True, "Isn't started after start"
    assert pw.get_finished() is False, "Finished before finish"
    pw.join(d_member2, tz)
    for member in pw.members:
        assert member.get_started() is True, "Member not started after start"
    pw.leave(d_member1, tz)
    pw.leave(d_member2, tz)
    assert pw.get_started() is True, "Isn't started after start"
    assert pw.get_finished() is True, "Isn't finished after all leave"
    for member in pw.members:
        assert member.get_finished() is True, "Member not finished after finish"
    assert pw.leave(d_member1, tz) is 2, "Member leaving after join not reporting "
    assert pw.join(d_member3, tz) is False, "Allowed join after finish"

    pw = tutils.PW()

    pw.join(d_member1, tz)
    pw.begin(tz)
    pw.join(d_member2, tz)
    for member in pw.members:
        assert member.get_started() is True, "Member not started after start"
    pw.finish(tz)
    assert pw.get_started() is True, "Isn't started after start"
    assert pw.get_finished() is True, "Isn't finished after finish called"
    for member in pw.members:
        assert member.get_finished() is True, "Member not finished after finish"
