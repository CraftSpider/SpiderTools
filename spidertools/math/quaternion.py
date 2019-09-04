
import numbers
import math
import functools

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
    """
        Object representing a Quaternion, a complex vector with 3 imaginary number lines.
    """

    __slots__ = ("x", "y", "z", "w")

    def __init__(self, x, y=None, z=None, w=None):
        """
            Create a new quaternion. Cam supply one value to fill all attributes, or specify each attribute individually
        :param x: The x component of the Quaternion
        :param y: The y component of the Quaternion
        :param z: The z component of the Quaternion
        :param w: The w component of the Quaternion
        """
        if y is None and z is None and w is None:
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
        """
            Generate a string representing exactly this Quat
        :return: Quat in string form
        """
        return f"Quaternion(x={self.x}, y={self.y}, z={self.z}, w={self.w})"

    def __eq__(self, other):
        """
            Check whether this quaternion is equal to another quaternion
        :param other: Quaternion to compare to
        :return: Whether quaternions are equal
        """
        if isinstance(other, Quaternion):
            return self.x == other.x and self.y == other.y and self.z == other.z and self.w == other.w
        else:
            return NotImplemented

    def __add__(self, other):
        """
            Sum this quat with another value. Supports adding other quats and real numbers
        :param other: Value to add to this quat
        :return: New quat with value added
        """
        if isinstance(other, Quaternion):
            return Quaternion(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)
        elif isinstance(other, numbers.Real):
            return Quaternion(self.x + other, self.y + other, self.z + other, self.w + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        """
            Subtract a value from this quat. Supports subtracting other quats and real numbers
        :param other: Value to subtract from this quat
        :return: New quat with value subtracted
        """
        if isinstance(other, Quaternion):
            return Quaternion(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)
        elif isinstance(other, numbers.Real):
            return Quaternion(self.x - other, self.y - other, self.z - other, self.w - other)
        else:
            return NotImplemented

    def __mul__(self, other):
        """
            Multiply together two quaternions, or a quaternion and a real number.
        :param other: Value to multiply with this Quat
        :return: New quat from multiplied value
        """
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

    def __truediv__(self, other):
        """
            Divide this quat by a real value or quaternion
        :param other: Value to divide by
        :return: Quat divided by value
        """
        if isinstance(other, Quaternion):
            mag_other = other.magnitude_squared()
            w = (self.w * other.w + self.x * other.x + self.y * other.y + self.z * other.z) / mag_other
            x = (self.w * other.x - self.x * other.w - self.y * other.z + self.z * other.y) / mag_other
            y = (self.w * other.y + self.x * other.z - self.y * other.w - self.z * other.x) / mag_other
            z = (self.w * other.z - self.x * other.y + self.y * other.x - self.z * other.w) / mag_other
            return Quaternion(x, y, z, w)
        elif isinstance(other, numbers.Real):
            return Quaternion(self.x / other, self.y / other, self.z / other, self.w / other)
        else:
            return NotImplemented

    def __rmul__(self, other):
        """
            Add special right-hand case for transforming a vector with this quat
        :param other: Value to multiply or vector to transform
        :return: Quat with value multiplied, or new vector with transform applied
        """
        if isinstance(other, vector.Vector3):
            vec = vector.Vector3(self.x, self.y, self.z)
            return _float_correct(other + 2*vec @ (vec @ other + self.w*other))
        else:
            return self.__mul__(other)

    def __neg__(self):
        """
            Negate this quat. Note this is not the Quaternion Inverse, simply the negation of all its values
        :return: Negated quaternion
        """
        return Quaternion(-self.x, -self.y, -self.z, -self.w)

    def __pos__(self):
        """
            Get the result of the unary plus operator on the quaternion
        :return: Positive quaternion
        """
        return Quaternion(+self.x, +self.y, +self.z, +self.w)

    def __abs__(self):
        """
            Get the absolute value/magnitude of this quat
        :return: Magnitude of the quat
        """
        return self.magnitude()

    def __invert__(self):
        """
            Get the inversion of this quaternion. This, unlike neg, is the actual Quaternion Inverse.
        :return: Inverted quaternion
        """
        return self.inverse()

    @classmethod
    def from_vectors(cls, start, end=None):
        """
            Get a quaternion representing the rotation from position start to position end
        :param start: Start vector for the rotation
        :param end: End vector for the rotation
        :return: Quaternion representing rotation from start to end
        """
        if end is None:
            end = start
            start = vector.Vector3.UNIT_X
        cross = start @ end
        val = (start.magnitude_squared() * end.magnitude_squared())**.5 + (start | end)
        return Quaternion(cross.x, cross.y, cross.z, val).normal()

    @classmethod
    @functools.lru_cache()
    def from_angles(cls, x, y, z):
        """
            Get a quaternion representing a rotation of a given number of degrees around each
            of three primary angles.
        :param x: Rotation around X axis
        :param y: Rotation around Y axis
        :param z: Rotation around Z axis
        :return: Quaternion representing set of rotation angles
        """
        x = math.radians(x)
        y = math.radians(y)
        z = math.radians(z)

        cx = math.cos(x * 0.5)
        sx = math.sin(x * 0.5)

        cy = math.cos(y * 0.5)
        sy = math.sin(y * 0.5)

        cz = math.cos(z * 0.5)
        sz = math.sin(z * 0.5)

        w = cz * cy * cx + sz * sy * sx
        x = cz * cy * sx - sz * sy * cx
        y = sz * cy * sx + cz * sy * cx
        z = sz * cy * cx - cz * sy * sx

        return Quaternion(x, y, z, w).normal()

    def conjugate(self):
        """
            Get the conjugate of this quaternion
        :return: Quaternion conjugate
        """
        return Quaternion(-self.x, -self.y, -self.z, self.w)

    def magnitude(self):
        """
            Get the magnitude or norm of this quat
        :return: Magnitude of the quat
        """
        return (self.x**2 + self.y**2 + self.z**2 + self.w**2)**.5

    def magnitude_squared(self):
        """
            Get the magnitude of this quaternion squared. More efficient than sqrt + square
        :return: Magnitude squared of the quat
        """
        return self.x**2 + self.y**2 + self.z**2 + self.w**2

    def normal(self):
        """
            Get this quat in a normal form, with magnitude of 1
        :return: Normalized quat
        """
        return self / abs(self)

    def inverse(self):
        """
            Get the Quaternion Inverse of this quat, the value that composed with this result in a
            0 transform
        :return: Inverted form of the quat
        """
        return self.conjugate() / self.magnitude_squared()
