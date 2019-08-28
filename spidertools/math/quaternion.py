
import numbers

from . import vector


def _float_correct(item):
    """
        A lazy way to handle floating point error
    :param vector: vector to correct
    :return: corrected float values
    """
    for i in ['w', 'x', 'y', 'z']:
        if not hasattr(item, i):
            continue
        setattr(item, i, round(getattr(item, i), 5))
    return item


class Quaternion:

    __slots__ = ("x", "y", "z", "w")

    def __init__(self, x, y=None, z=None, w=None):
        if isinstance(x, Quaternion):
            self.x = x.x
            self.y = x.y
            self.z = x.z
            self.w = x.w
        elif not isinstance(x, numbers.Real):
            raise TypeError("Quaternion arguments must be a number or quaternion")
        elif y is None and z is None and w is None:
            self.x = x
            self.y = x
            self.z = x
            self.w = x
        else:
            self.x = x or 0
            self.y = y or 0
            self.z = z or 0
            self.w = w or 0

    def __repr__(self):
        return f"Quaternion(x={self.x}, y={self.y}, z={self.z}, w={self.w})"

    def __add__(self, other):
        if isinstance(other, Quaternion):
            return Quaternion(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)
        elif isinstance(other, vector.Vector3):
            return Quaternion(self.x + other.x, self.y + other.y, self.z + other.z, self.w)
        elif isinstance(other, numbers.Real):
            return Quaternion(self.x, self.y, self.z, self.w + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Quaternion):
            return Quaternion(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)
        elif isinstance(other, vector.Vector3):
            return Quaternion(self.x - other.x, self.y - other.y, self.z - other.z, self.w)
        elif isinstance(other, numbers.Real):
            return Quaternion(self.x, self.y, self.z - other)
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, Quaternion):
            w = self.w * other.w - self.x * other.x - self.y * other.y - self.z - other.z
            x = self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y
            y = self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x
            z = self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w
            return _float_correct(Quaternion(x, y, z, w))
        elif isinstance(other, numbers.Real):
            return Quaternion(self.x * other, self.y * other, self.z * other, self.w * other)
        else:
            return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, vector.Vector3):
            vec = vector.Vector3(self.x, self.y, self.z)
            return _float_correct(other + 2*vec @ (vec @ other + self.w*other))
        else:
            return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, numbers.Real):
            return Quaternion(self.x / other, self.y / other, self.z / other, self.w / other)
        else:
            return NotImplemented

    def __neg__(self):
        return Quaternion(-self.x, -self.y, -self.z, -self.w)

    def __abs__(self):
        return self.flatten()

    def flatten(self):
        return (self.x**2 + self.y**2 + self.z**2 + self.w**2)**.5

    def normal(self):
        return self / abs(self)

    def inverse(self):
        return Quaternion(-self.x, -self.y, -self.z, self.w) / (self.x**2 + self.y**2 + self.z**2 + self.w**2)
