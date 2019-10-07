
import pytest
import spidertools.math as math


def test_rot_vec():
    a = math.Vector(1, 0, 0)
    b = math.Vector(0, 1, 0)
    c = math.Vector(0, 0, 1)

    rot = math.Rotator(90, 0, 0)
    assert a * rot == a
    assert b * rot == c
    assert c * rot == -b

    rot = math.Rotator(0, 90, 0)
    assert a * rot == -c
    assert b * rot == b
    assert c * rot == a

    rot = math.Rotator(0, 0, 90)
    assert a * rot == b
    assert b * rot == -a
    assert c * rot == c


def test_from_vec():
    pytest.skip()
    a = math.Vector(1, 0, 0)
    b = math.Vector(0, 1, 0)
    c = math.Vector(0, 0, 1)

    rot = math.Rotator.from_vectors(a, b)
    assert a * rot == b
    rot = math.Rotator.from_vectors(a, c)
    assert a * rot == c

    rot = math.Rotator.from_vectors(b, a)
    assert b * rot == a
    rot = math.Rotator.from_vectors(b, c)
    assert b * rot == c

    rot = math.Rotator.from_vectors(c, a)
    assert c * rot == a
    rot = math.Rotator.from_vectors(c, b)
    assert c * rot == b
