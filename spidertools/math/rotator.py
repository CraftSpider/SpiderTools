
import numbers
import math

from . import vector as vec


def _float_correct(vector):
    """
        A lazy way to handle floating point error
    :param vector: vector to correct
    :return: corrected float values
    """
    vector.x = round(vector.x, 5)
    vector.y = round(vector.y, 5)
    vector.z = round(vector.z, 5)


class Rotator:

    __slots__ = ("x", "y", "z")

    def __init__(self, x, y=None, z=None, radians=False):
        if not isinstance(x, numbers.Real):
            raise TypeError("Rotator arguments must be a number or rotator")

        if not radians:
            x = math.radians(x)
            if z is not None:
                y = math.radians(y)
                z = math.radians(z)

        self.x = x
        if z is None:
            self.y = x
            self.z = x
        else:
            self.y = y
            self.z = z

    def __repr__(self):
        return f"Rotator(x={self.x}, y={self.y}, z={self.z}, radians=True)"

    def __mul__(self, other):
        if isinstance(other, vec.Vector):
            if self.x:
                other = (math.cos(self.x) * other) + \
                    math.sin(self.x) * (vec.UnitX @ other) + \
                    (1 - math.cos(self.x)) * (vec.UnitX * other) * vec.UnitX
            if self.y:
                other = (math.cos(self.y) * other) + \
                    math.sin(self.y) * (vec.UnitY @ other) + \
                    (1 - math.cos(self.y)) * (vec.UnitY * other) * vec.UnitY
            if self.z:
                other = (math.cos(self.z) * other) + \
                    math.sin(self.z) * (vec.UnitZ @ other) + \
                    (1 - math.cos(self.z)) * (vec.UnitZ * other) * vec.UnitZ
            _float_correct(other)
            return other
        else:
            return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, vec.Vector):
            return self.__mul__(other)
        else:
            return NotImplemented
