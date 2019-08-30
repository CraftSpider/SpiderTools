
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
    """
        Object representing a Quaternion, a complex vector with 3 imaginary number lines.
    """

    __slots__ = ("x", "y", "z", "w")

    def __init__(self, x, y=None, z=None, w=None):
        """
            Create a new quaternion. Can copy an existing quaternion, supply one value to fill all
            attributes, or specify each attribute individually
        :param x: The x component of the Quaternion
        :param y: The y component of the Quaternion
        :param z: The z component of the Quaternion
        :param w: The w component of the Quaternion
        """
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
        """
            Generate a string representing exactly this Quat
        :return: Quat in string form
        """
        return f"Quaternion(x={self.x}, y={self.y}, z={self.z}, w={self.w})"

    def __float__(self):
        """
            Get the quat as a float, interpreted as its magnitude
        :return: Float magnitude of the quat
        """
        return self.flatten()

    def __add__(self, other):
        """
            Sum this quat with another value. Supports adding other quats, vectors, and real numbers
        :param other: Value to add to this quat
        :return: New quat with value added
        """
        if isinstance(other, Quaternion):
            return Quaternion(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)
        elif isinstance(other, vector.Vector3):
            return Quaternion(self.x + other.x, self.y + other.y, self.z + other.z, self.w)
        elif isinstance(other, numbers.Real):
            return Quaternion(self.x, self.y, self.z, self.w + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        """
            Subtract a value from this quat. Supports subtracting other quats, vectors, and real numbers
        :param other: Value to subtract from this quat
        :return: New quat with value subtracted
        """
        if isinstance(other, Quaternion):
            return Quaternion(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)
        elif isinstance(other, vector.Vector3):
            return Quaternion(self.x - other.x, self.y - other.y, self.z - other.z, self.w)
        elif isinstance(other, numbers.Real):
            return Quaternion(self.x, self.y, self.z - other)
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

    def __truediv__(self, other):
        """
            Divide this quat by a value
        :param other: Value to divide by
        :return: Quat divided by value
        """
        if isinstance(other, numbers.Real):
            return Quaternion(self.x / other, self.y / other, self.z / other, self.w / other)
        else:
            return NotImplemented

    def __neg__(self):
        """
            Negate this quat. Note this is not the Quaternion Inverse, simply the negation of all its values
        :return: Negated quaternion
        """
        return Quaternion(-self.x, -self.y, -self.z, -self.w)

    def __abs__(self):
        """
            Get the absolute value/magnitude of this quat
        :return: Float magnitude of the quat
        """
        return self.flatten()

    def flatten(self):
        """
            Get the magnitude or norm of this quat
        :return: Magnitude of the quat
        """
        return (self.x**2 + self.y**2 + self.z**2 + self.w**2)**.5

    def normal(self):
        """
            Get this quat in a normal form, with magnitude of 1
        :return: Normalized Quat
        """
        return self / abs(self)

    def inverse(self):
        """
            Get the Quaternion Inverse of this quat, the value that composed with this result in a
            0 transform
        :return: Inverted form of the quat
        """
        return Quaternion(-self.x, -self.y, -self.z, self.w) / (self.x**2 + self.y**2 + self.z**2 + self.w**2)
