
from math import floor, ceil, trunc
import spidertools.math as math


def test_vec2():
    a = math.Vector2(1, 2)
    assert a.x == 1
    assert a.y == 2


def test_vec2_eq():
    a = math.Vector2(1, 1)
    b = math.Vector2(1, 1)
    c = math.Vector2(-1, 0)

    assert a == b
    assert a != c


def test_vec2_add():
    a = math.Vector2(1, 0)
    b = math.Vector2(0, 1)

    assert a + b == b + a == math.Vector2.UNIT
    assert a + 1 == math.Vector2(2, 1)


def test_vec2_sub():
    a = math.Vector2(1, 0)
    b = math.Vector2(2, 1)

    assert a - b == math.Vector2(-1, -1)
    assert b - a == math.Vector2.UNIT
    assert b - 1 == math.Vector2.UNIT_X


def test_vec2_mul():
    a = math.Vector2(3, 5)
    b = math.Vector2(2, 3)

    assert a * b == b * a == math.Vector2(6, 15)
    assert a * 2 == math.Vector2(6, 10)


def test_vec2_truediv():
    a = math.Vector2(5, 6)
    b = math.Vector2(2, 3)

    assert a / b == math.Vector2(2.5, 2)
    assert b / a == math.Vector2(.4, .5)
    assert a / 2 == math.Vector2(2.5, 3)


def test_vec2_floordiv():
    a = math.Vector2(5, 6)
    b = math.Vector2(2, 3)

    assert a // b == math.Vector2(2, 2)
    assert b // a == math.Vector2(0, 0)
    assert a // 2 == math.Vector2(2, 3)


def test_vec2_neg():
    a = math.Vector2(2, -2)

    assert -a == math.Vector2(-2, 2)


def test_vec2_abs():
    a = math.Vector2(3, 4)

    assert abs(a) == 5


def test_vec2_round():
    a = math.Vector2(1.12345, 5.12345)

    assert round(a) == math.Vector2(1, 5)
    assert round(a, 2) == math.Vector2(1.12, 5.12)


def test_vec2_trunc():
    a = math.Vector2(-1.5, 1.5)

    assert trunc(a) == math.Vector2(-1, 1)


def test_vec2_floor_ceil():
    a = math.Vector2(.5, 5.2)
    b = math.Vector2(-.5, -5.2)

    assert floor(a) == math.Vector2(0, 5)
    assert ceil(a) == math.Vector2(1, 6)

    assert floor(b) == math.Vector2(-1, -6)
    assert ceil(b) == math.Vector2(0, -5)


def test_vec2_to3d():
    a = math.Vector2(1, 2)

    assert a.to_3d() == math.Vector3(1, 2, 0)


def test_vec3():
    a = math.Vector3(1, 2, 3)

    assert a.x == 1
    assert a.y == 2
    assert a.z == 3


def test_vec3_eq():
    a = math.Vector3(1, 2, 3)
    b = math.Vector3(1, 2, 3)
    c = math.Vector3(3, 2, 1)

    assert a == b
    assert a != c


def test_vec3_add():
    a = math.Vector3(1, 0, 1)
    b = math.Vector3(0, 1, 0)

    assert a + b == b + a == math.Vector3.UNIT
    assert a + 5 == math.Vector3(6, 5, 6)


def test_vec3_sub():
    a = math.Vector3(1, 2, 3)
    b = math.Vector3(0, 1, 1)

    assert a - b == math.Vector3(1, 1, 2)
    assert b - a == math.Vector3(-1, -1, -2)
    assert a - 3 == math.Vector3(-2, -1, 0)


def test_vec3_mul():
    a = math.Vector3(2, 3, 7)
    b = math.Vector3(2, -6, 1)

    assert a * b == b * a == math.Vector3(4, -18, 7)
    assert a * 2 == math.Vector3(4, 6, 14)


def test_vec3_cross():
    a = math.Vector(1, 0, 1)
    b = math.Vector(1, 1, 0)

    assert a @ b == math.Vector3(-1, 1, 1)


def test_vec3_truediv():
    a = math.Vector3(5, 6, 10)
    b = math.Vector3(2, 3, 25)

    assert a / b == math.Vector3(2.5, 2, .4)
    assert b / a == math.Vector3(.4, .5, 2.5)
    assert a / 2 == math.Vector3(2.5, 3, 5)


def test_vec3_floordiv():
    a = math.Vector3(5, 6, 10)
    b = math.Vector3(2, 3, 25)

    assert a // b == math.Vector3(2, 2, 0)
    assert b // a == math.Vector3(0, 0, 2)
    assert a // 2 == math.Vector(2, 3, 5)


def test_vec3_dot():
    a = math.Vector(3, 4, 5)
    b = math.Vector(1, 3, 2)

    assert a | b == 25


def test_vec3_neg():
    a = math.Vector3(0, 1, -1)

    assert -a == math.Vector3(0, -1, 1)


def test_vec3_abs():
    a = math.Vector3(3, 4, 12)

    assert abs(a) == 13


def test_vec3_round():
    a = math.Vector3(1.12345, 0.12345, -.62345)

    assert round(a) == math.Vector3(1, 0, -1)
    assert round(a, 2) == math.Vector3(1.12, .12, -.62)


def test_vec3_trunc():
    a = math.Vector3(-1.5, 1.5, 8)

    assert trunc(a) == math.Vector3(-1, 1, 8)


def test_vec3_floor_ceil():
    a = math.Vector3(.5, 5.2, 0)
    b = math.Vector3(-.5, -5.2, 0)

    assert floor(a) == math.Vector3(0, 5, 0)
    assert ceil(a) == math.Vector3(1, 6, 0)

    assert floor(b) == math.Vector3(-1, -6, 0)
    assert ceil(b) == math.Vector3(0, -5, 0)


def test_vec3_to2d():
    a = math.Vector3(1, 2, 3)

    assert a.to_2d() == math.Vector2(1, 2)