
import spidertools.math as math
import pytest


def test_quat():
    q = math.Quaternion(1, 2, 3, 4)

    assert q.x == 1
    assert q.y == 2
    assert q.z == 3
    assert q.w == 4


def test_quat_add():
    pytest.skip()


def test_quat_sub():
    pytest.skip()


def test_quat_mul():
    pytest.skip()


def test_quat_truediv():
    pytest.skip()


def test_quat_neg():
    pytest.skip()


def test_quat_abs():
    pytest.skip()


def test_quat_normal():
    pytest.skip()


def test_quat_inverse():
    pytest.skip()


def test_rotate_vector():
    quat = math.Quaternion(x=0, y=0.707106, z=0, w=0.707106)
    quat2 = quat * quat

    assert math.Vector(1, 0, 0) * quat == math.Vector(0, 0, -1)
    assert math.Vector(1, 0, 0) * quat2 == math.Vector(-1, 0, 0)

    assert math.Vector(0, 1, 0) * quat == math.Vector(0, 1, 0)
    assert math.Vector(0, 1, 0) * quat2 == math.Vector(0, 1, 0)
