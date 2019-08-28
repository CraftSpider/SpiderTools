
import math
import numbers


class Vector2:

    __slots__ = ("x", "y")

    def __init__(self, x, y=None):
        if not isinstance(x, numbers.Real):
            raise TypeError("Vector2 arguments must be a number or vector")
        self.x = x
        if y is None:
            self.y = x
        else:
            self.y = y

    def __repr__(self):
        return f"Vector2(x={self.x}, y={self.y})"

    def __int__(self):
        raise TypeError("Vectors cannot be implicitly converted to an integer. Use abs() or .flatten")

    def __float__(self):
        return self.flatten()

    def __eq__(self, other):
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        else:
            return NotImplemented

    def __add__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        elif isinstance(other, numbers.Real):
            return Vector2(self.x + other, self.y + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)
        elif isinstance(other, numbers.Real):
            return Vector2(self.x - other, self.y - other)
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x * other.x, self.y * other.y)
        elif isinstance(other, numbers.Real):
            return Vector2(self.x * other, self.y * other)
        else:
            return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x / other.x, self.y / other.y)
        elif isinstance(other, numbers.Real):
            return Vector2(self.x / other, self.y / other)
        else:
            return NotImplemented

    def __floordiv__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x // other.x, self.y // other.y)
        elif isinstance(other, numbers.Real):
            return Vector2(self.x // other, self.y // other)
        else:
            return NotImplemented

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __abs__(self):
        return self.flatten()

    def __round__(self, n=None):
        return Vector2(round(self.x, n), round(self.y, n))

    def __trunc__(self):
        return Vector2(math.trunc(self.x), math.trunc(self.y))

    def __floor__(self):
        return Vector2(math.floor(self.x), math.floor(self.y))

    def __ceil__(self):
        return Vector2(math.ceil(self.x), math.ceil(self.y))

    def flatten(self):
        return (self.x**2 + self.y**2)**.5

    def to_3d(self):
        return Vector3(self.x, self.y, 0)


Vector2.UNIT = Vector2(1)
Vector2.ZERO = Vector2(0)
Vector2.UNIT_X = Vector2(1, 0)
Vector2.UNIT_Y = Vector2(0, 1)


class Vector3:

    __slots__ = ("x", "y", "z")

    def __init__(self, x, y=None, z=None):
        if not isinstance(x, numbers.Real):
            raise TypeError("Vector3 arguments must be a number or vector")
        self.x = x
        if y is None and z is None:
            self.y = x
            self.z = x
        else:
            self.y = y or 0
            self.z = z or 0

    def __repr__(self):
        return f"Vector3(x={self.x}, y={self.y}, z={self.z})"

    def __int__(self):
        raise TypeError("Vectors cannot be implicitly converted to an integer. Use abs() or .flatten")

    def __float__(self):
        return self.flatten()

    def __eq__(self, other):
        if isinstance(other, Vector3):
            return self.x == other.x and self.y == other.y and self.z == other.z
        else:
            return NotImplemented

    def __add__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
        elif isinstance(other, numbers.Real):
            return Vector3(self.x + other, self.y + other, self.z + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
        elif isinstance(other, numbers.Real):
            return Vector3(self.x - other, self.y - other, self.z - other)
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x * other.x, self.y * other.y, self.z * other.z)
        elif isinstance(other, numbers.Real):
            return Vector3(self.x * other, self.y * other, self.z * other)
        else:
            return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __matmul__(self, other):
        if not isinstance(other, Vector3):
            return NotImplemented
        return self.cross(other)

    def __truediv__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x / other.x, self.y / other.y, self.z / other.z)
        elif isinstance(other, numbers.Real):
            return Vector3(self.x / other, self.y / other, self.z / other)
        else:
            return NotImplemented

    def __floordiv__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x // other.x, self.y // other.y, self.z // other.z)
        elif isinstance(other, numbers.Real):
            return Vector(self.x // other, self.y // other, self.z // other)
        else:
            return NotImplemented

    def __or__(self, other):
        if not isinstance(other, Vector3):
            return NotImplemented
        return self.dot(other)

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)

    def __abs__(self):
        return self.flatten()

    def __round__(self, n=None):
        return Vector3(round(self.x, n), round(self.y, n), round(self.z, n))

    def __trunc__(self):
        return Vector3(math.trunc(self.x), math.trunc(self.y), math.trunc(self.z))

    def __floor__(self):
        return Vector3(math.floor(self.x), math.floor(self.y), math.floor(self.z))

    def __ceil__(self):
        return Vector3(math.ceil(self.x), math.ceil(self.y), math.ceil(self.z))

    def flatten(self):
        return (self.x**2 + self.y**2 + self.z**2)**.5

    def dot(self, other):
        if not isinstance(other, Vector3):
            raise TypeError("Attempt to dot vector with invalid type")
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        if not isinstance(other, Vector3):
            raise TypeError("Attempt to cross vector with invalid type")
        x = self.y * other.z - self.z * other.y
        y = self.z * other.x - self.x * other.z
        z = self.x * other.y - self.y * other.x
        return Vector3(x, y, z)

    def to_2d(self):
        return Vector2(self.x, self.y)


def rect_list(top_left, bottom_right):
    out = [
        top_left,
        None,
        None,
        None,
        None,
        None,
        None,
        bottom_right
    ]
    out[1] = Vector3(out[7].x, out[0].y, out[0].z)
    out[2] = Vector3(out[0].x, out[0].y, out[7].z)
    out[3] = Vector3(out[7].x, out[0].y, out[7].z)
    out[4] = Vector3(out[0].x, out[7].y, out[0].z)
    out[5] = Vector3(out[7].x, out[7].y, out[0].z)
    out[6] = Vector3(out[0].x, out[7].y, out[7].z)
    return out


Vector = Vector3


UNIT_X = Vector3(1, 0, 0)
UNIT_Y = Vector3(0, 1, 0)
UNIT_Z = Vector3(0, 0, 1)

Vector3.UNIT = Vector3(1)
Vector3.ZERO = Vector3(0)
Vector3.UNIT_X = UNIT_X
Vector3.UNIT_Y = UNIT_Y
Vector3.UNIT_Z = UNIT_Z
