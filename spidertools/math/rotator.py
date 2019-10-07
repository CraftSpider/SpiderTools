
import numbers
import math

from . import vector as vector


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
    """
        Class representing a rotation around 3 axis
    """

    __slots__ = ("x", "y", "z")

    def __init__(self, x, y=None, z=None, radians=False):
        """
            Construct a rotator from a set of degrees/radians around three axis
        :param x: x value of the rotator
        :param y: y value of the rotator
        :param z: z value of the rotator
        :param radians: Whether the above values are in radians
        """
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
        """
            String form of this rotator, as exact values
        :return: Rotator as a string
        """
        return f"Rotator(x={self.x}, y={self.y}, z={self.z}, radians=True)"

    def __add__(self, other):
        """
            Add this rotator and another one, or add a fixed rotation in all angles in radians
        :param other: Rotation to add
        :return: New rotator
        """
        if isinstance(other, Rotator):
            return Rotator(self.x + other.x, self.y + other.y, self.z + other.z, radians=True)
        elif isinstance(other, numbers.Real):
            return Rotator(self.x + other, self.y + other, self.z + other, radians=True)
        else:
            return NotImplemented

    def __sub__(self, other):
        """
            Subtract a different rotator from this one, or a fixed rotation in radians from all angles
        :param other: Rotation to subtract
        :return: New rotator
        """
        if isinstance(other, Rotator):
            return Rotator(self.x - other.x, self.y - other.y, self.z - other.z, radians=True)
        elif isinstance(other, numbers.Real):
            return Rotator(self.x - other, self.y - other, self.z - other, radians=True)
        else:
            return NotImplemented

    def __mul__(self, other):
        """
            Multiply this rotator by a value, or transform a vector
        :param other: Value to multiply or vector to transform
        :return: New rotator or vector
        """
        if isinstance(other, Rotator):
            return Rotator(self.x * other.x, self.y * other.y, self.z * other.z, radians=True)
        elif isinstance(other, numbers.Real):
            return Rotator(self.x * other, self.y * other, self.z * other, radians=True)
        elif isinstance(other, vector.Vector3):
            if self.x:
                other = (math.cos(self.x) * other) + \
                    math.sin(self.x) * (other.UNIT_X @ other) + \
                    (1 - math.cos(self.x)) * (other.UNIT_X * other) * other.UNIT_X
            if self.y:
                other = (math.cos(self.y) * other) + \
                    math.sin(self.y) * (other.UNIT_Y @ other) + \
                    (1 - math.cos(self.y)) * (other.UNIT_Y * other) * other.UNIT_Y
            if self.z:
                other = (math.cos(self.z) * other) + \
                    math.sin(self.z) * (other.UNIT_Z @ other) + \
                    (1 - math.cos(self.z)) * (other.UNIT_Z * other) * other.UNIT_Z
            _float_correct(other)
            return other
        else:
            return NotImplemented

    def __truediv__(self, other):
        """
            Divide this rotator by a value
        :param other: Value to divide
        :return: New rotator
        """
        if isinstance(other, Rotator):
            return Rotator(self.x / other.x, self.y / other.y, self.z / other.z, radians=True)
        elif isinstance(other, numbers.Real):
            return Rotator(self.x / other, self.y / other, self.z / other, radians=True)
        else:
            return NotImplemented

    def __rmul__(self, other):
        """
            Case for if the rotator is on the right-hand side of the equation
        :param other: Value to multiply
        :return: Multiplied value
        """
        return self.__mul__(other)

    @classmethod
    def from_vectors(cls, start, end=None):
        """
            Get a rotator representing the rotation from position start to position end
        :param start: Start vector for the rotation
        :param end: End vector for the rotation
        :return: Rotator representing rotation from start to end
        """
        if end is None:
            end = start
            start = vector.Vector3.UNIT_X
        raise NotImplementedError()  # TODO
