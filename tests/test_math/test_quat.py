
import spidertools.math as math
import pytest


def test_quat():
    q = math.Quaternion(1, 2, 3, 4)

    assert q.x == 1
    assert q.y == 2
    assert q.z == 3
    assert q.w == 4


def test_quat_add():
    q = math.Quaternion(1, 2, 3, 4)
    q2 = math.Quaternion(2, 3, 4, 5)

    assert q + q2 == q2 + q == math.Quaternion(3, 5, 7, 9)
    assert q + 5 == math.Quaternion(6, 7, 8, 9)


def test_quat_sub():
    q = math.Quaternion(1, 2, 3, 4)
    q2 = math.Quaternion(2, 3, 4, 5)

    assert q - q2 == math.Quaternion(-1, -1, -1, -1)
    assert q2 - q == math.Quaternion(1, 1, 1, 1)
    assert q - 1 == math.Quaternion(0, 1, 2, 3)


def test_quat_mul():
    w = math.Quaternion(0, 0, 0, 1)
    x = math.Quaternion(1, 0, 0, 0)
    y = math.Quaternion(0, 1, 0, 0)
    z = math.Quaternion(0, 0, 1, 0)

    assert w * w == w
    assert w * x == x
    assert w * y == y
    assert w * z == z

    assert x * w == x
    assert x * x == -w
    assert x * y == z
    assert x * z == -y

    assert y * w == y
    assert y * x == -z
    assert y * y == -w
    assert y * z == x

    assert z * w == z
    assert z * x == y
    assert z * y == -x
    assert z * z == -w


def test_quat_truediv():
    w = math.Quaternion(0, 0, 0, 1)
    x = math.Quaternion(1, 0, 0, 0)
    y = math.Quaternion(0, 1, 0, 0)
    z = math.Quaternion(0, 0, 1, 0)

    assert w / w == w
    assert w / x == x
    assert w / y == y
    assert w / z == z

    assert x / w == -x
    assert x / x == w
    assert x / y == -z
    assert x / z == y

    assert y / w == -y
    assert y / x == z
    assert y / y == w
    assert y / z == -x

    assert z / w == -z
    assert z / x == -y
    assert z / y == x
    assert z / z == w


def test_quat_neg():
    q = math.Quaternion(1, 2, 3, 4)
    q2 = math.Quaternion(3, 0, 2, 0)

    assert -q == math.Quaternion(-1, -2, -3, -4)
    assert -q2 == math.Quaternion(-3, 0, -2, 0)


def test_quat_abs():
    q = math.Quaternion(1, 1, 1, 1)
    q2 = math.Quaternion(-2, -2, -2, -2)

    assert abs(q) == 2
    assert abs(q2) == 4


def test_quat_normal():
    q = math.Quaternion(1, 2, 3, 4)

    assert abs(q) != 1
    assert abs(q.normal()) == 1


def test_quat_inverse():
    q = math.Quaternion(1, 2, 3, 4)
    q2 = math.Quaternion(4, 3, 2, 1)

    assert q * q.inverse() == math.Quaternion(0, 0, 0, 1)
    assert q2 * q2.inverse() == math.Quaternion(0, 0, 0, 1)


def test_rotate_vector():
    quat = math.Quaternion(x=0, y=0.707106, z=0, w=0.707106)
    quat2 = quat * quat

    assert math.Vector(1, 0, 0) * quat == math.Vector(0, 0, -1)
    assert math.Vector(1, 0, 0) * quat2 == math.Vector(-1, 0, 0)

    assert math.Vector(0, 1, 0) * quat == math.Vector(0, 1, 0)
    assert math.Vector(0, 1, 0) * quat2 == math.Vector(0, 1, 0)


def test_from_angles():
    quat = math.Quaternion.from_angles(0, 90, 0)
    quat2 = math.Quaternion.from_angles(90, 0, 180)

    assert math.Vector(1, 0, 0) * quat == math.Vector(0, 0, -1)
    assert math.Vector(1, 0, 0) * quat2 == math.Vector(-1, 0, 0)

    assert math.Vector(0, 1, 0) * quat == math.Vector(0, 1, 0)
    assert math.Vector(0, 1, 0) * quat2 == math.Vector(0, 0, 1)
