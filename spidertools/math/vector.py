
import math
import numbers


class Vector2:
    """
        A 2-dimensional vector, with x and y component
    """

    __slots__ = ("x", "y")

    def __init__(self, x, y=None):
        """
            Initialize a new vector from x and y values
        :param x: x value of the vector
        :param y: y value of the vector
        """
        if not isinstance(x, numbers.Real):
            raise TypeError("Vector2 arguments must be a number or vector")
        self.x = x
        if y is None:
            self.y = x
        else:
            self.y = y

    def __repr__(self):
        """
            Get the vector as a string with precise values
        :return: Vector as a string
        """
        return f"Vector2(x={self.x}, y={self.y})"

    def __int__(self):
        """
            Vectors cannot be implicity converted to an int, throw a more helpful error if someone tries.
        :raise: TypeError
        """
        raise TypeError("Vectors cannot be implicitly converted to an integer. Use abs() or .flatten")

    def __float__(self):
        """
            Convert the vector to a float, returns the vector's magnitude
        :return: Vector magnitude
        """
        return self.flatten()

    def __eq__(self, other):
        """
            Compare this vector to another vector
        :param other: Vector to compare to
        :return: Compared values
        """
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        else:
            return NotImplemented

    def __add__(self, other):
        """
            Add a value to this vector, another vector or a real number
        :param other: Value to add
        :return: New vector with value added
        """
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        elif isinstance(other, numbers.Real):
            return Vector2(self.x + other, self.y + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        """
            Subtract a vector or real number from this vector
        :param other: Value to subtract
        :return: New vector with value subtracted
        """
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)
        elif isinstance(other, numbers.Real):
            return Vector2(self.x - other, self.y - other)
        else:
            return NotImplemented

    def __mul__(self, other):
        """
            Multiply this vector with another vector or real number
        :param other: Value to multiply
        :return: New vector with multiplied value
        """
        if isinstance(other, Vector2):
            return Vector2(self.x * other.x, self.y * other.y)
        elif isinstance(other, numbers.Real):
            return Vector2(self.x * other, self.y * other)
        else:
            return NotImplemented

    def __truediv__(self, other):
        """
            Divide this vector by a vector or real number
        :param other: Value to divide by
        :return: New vector with divided value
        """
        if isinstance(other, Vector2):
            return Vector2(self.x / other.x, self.y / other.y)
        elif isinstance(other, numbers.Real):
            return Vector2(self.x / other, self.y / other)
        else:
            return NotImplemented

    def __floordiv__(self, other):
        """
            Floordiv this vector by a vector or real number
        :param other: Value to divide by
        :return: New vector with divided value
        """
        if isinstance(other, Vector2):
            return Vector2(self.x // other.x, self.y // other.y)
        elif isinstance(other, numbers.Real):
            return Vector2(self.x // other, self.y // other)
        else:
            return NotImplemented

    def __neg__(self):
        """
            Negate this vector, return its inverse
        :return: Inverted vector
        """
        return Vector2(-self.x, -self.y)

    def __abs__(self):
        """
            Get the absolute value (magnitude) of this vector
        :return: Vector magnitude
        """
        return self.flatten()

    def __round__(self, n=None):
        """
            Round this vector to a given number of decimal places
        :param n: decimal places to round to
        :return: Rounded vector
        """
        return Vector2(round(self.x, n), round(self.y, n))

    def __trunc__(self):
        """
            Truncate this vector towards 0
        :return: Truncated vector
        """
        return Vector2(math.trunc(self.x), math.trunc(self.y))

    def __floor__(self):
        """
            Floor this vector, rounding towards negative infinity
        :return: Floored vector
        """
        return Vector2(math.floor(self.x), math.floor(self.y))

    def __ceil__(self):
        """
            Ceil this vector, rounding towards positive infinity
        :return: Ceiled vector
        """
        return Vector2(math.ceil(self.x), math.ceil(self.y))

    def flatten(self):
        """
            Get the magnitude of this vector
        :return: Vector magnitude
        """
        return (self.x**2 + self.y**2)**.5

    def to_3d(self):
        """
            Convert this vector to a 3d vector. Extended dimensions start at 0
        :return: New vector with 3 dimensions
        """
        return Vector3(self.x, self.y, 0)


Vector2.UNIT = Vector2(1)
Vector2.ZERO = Vector2(0)
Vector2.UNIT_X = Vector2(1, 0)
Vector2.UNIT_Y = Vector2(0, 1)


class Vector3:
    """
        A 3-dimensional vector, with x y and z components
    """

    __slots__ = ("x", "y", "z")

    def __init__(self, x, y=None, z=None):
        """
            Initialize a new vector from x y and z values
        :param x: x value of the vector
        :param y: y value of the vector
        :param z: z value of the vector
        """
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
        """
            Get the vector as a string with precise values
        :return: Vector as a string
        """
        return f"Vector3(x={self.x}, y={self.y}, z={self.z})"

    def __int__(self):
        """
            Vectors cannot be implicity converted to an int, throw a more helpful error if someone tries.
        :raise: TypeError
        """
        raise TypeError("Vectors cannot be implicitly converted to an integer. Use abs() or .flatten")

    def __float__(self):
        """
            Convert the vector to a float, returns the vector's magnitude
        :return: Vector magnitude
        """
        return self.flatten()

    def __eq__(self, other):
        """
            Compare this vector to another vector
        :param other: Vector to compare to
        :return: Compared values
        """
        if isinstance(other, Vector3):
            return self.x == other.x and self.y == other.y and self.z == other.z
        else:
            return NotImplemented

    def __add__(self, other):
        """
            Add a value to this vector, another vector or a real number
        :param other: Value to add
        :return: New vector with value added
        """
        if isinstance(other, Vector3):
            return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
        elif isinstance(other, numbers.Real):
            return Vector3(self.x + other, self.y + other, self.z + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        """
            Subtract a vector or real number from this vector
        :param other: Value to subtract
        :return: New vector with value subtracted
        """
        if isinstance(other, Vector3):
            return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
        elif isinstance(other, numbers.Real):
            return Vector3(self.x - other, self.y - other, self.z - other)
        else:
            return NotImplemented

    def __mul__(self, other):
        """
            Multiply this vector with another vector or real number
        :param other: Value to multiply
        :return: New vector with multiplied value
        """
        if isinstance(other, Vector3):
            return Vector3(self.x * other.x, self.y * other.y, self.z * other.z)
        elif isinstance(other, numbers.Real):
            return Vector3(self.x * other, self.y * other, self.z * other)
        else:
            return NotImplemented

    def __rmul__(self, other):
        """
            Handle multiplication when this vector is on the right side
        :param other: Value to multiply
        :return: New vector with multiplied value
        """
        return self.__mul__(other)

    def __matmul__(self, other):
        """
            Divide this vector by a vector or real number
        :param other: Value to divide by
        :return: New vector with divided value
        """
        if not isinstance(other, Vector3):
            return NotImplemented
        return self.cross(other)

    def __truediv__(self, other):
        """
            Divide this vector by a vector or real number
        :param other: Value to divide by
        :return: New vector with divided value
        """
        if isinstance(other, Vector3):
            return Vector3(self.x / other.x, self.y / other.y, self.z / other.z)
        elif isinstance(other, numbers.Real):
            return Vector3(self.x / other, self.y / other, self.z / other)
        else:
            return NotImplemented

    def __floordiv__(self, other):
        """
            Floordiv this vector by a vector or real number
        :param other: Value to divide by
        :return: New vector with divided value
        """
        if isinstance(other, Vector3):
            return Vector3(self.x // other.x, self.y // other.y, self.z // other.z)
        elif isinstance(other, numbers.Real):
            return Vector(self.x // other, self.y // other, self.z // other)
        else:
            return NotImplemented

    def __or__(self, other):
        """
            Get the dot product of this vector with another vector
        :param other: Vector to dot with this one
        :return: Float of dotted vector value
        """
        if not isinstance(other, Vector3):
            return NotImplemented
        return self.dot(other)

    def __neg__(self):
        """
            Negate this vector, return its inverse
        :return: Inverted vector
        """
        return Vector3(-self.x, -self.y, -self.z)

    def __abs__(self):
        """
            Get the absolute value (magnitude) of this vector
        :return: Vector magnitude
        """
        return self.flatten()

    def __round__(self, n=None):
        """
            Round this vector to a given number of decimal places
        :param n: decimal places to round to
        :return: Rounded vector
        """
        return Vector3(round(self.x, n), round(self.y, n), round(self.z, n))

    def __trunc__(self):
        """
            Truncate this vector towards 0
        :return: Truncated vector
        """
        return Vector3(math.trunc(self.x), math.trunc(self.y), math.trunc(self.z))

    def __floor__(self):
        """
            Floor this vector, rounding towards negative infinity
        :return: Floored vector
        """
        return Vector3(math.floor(self.x), math.floor(self.y), math.floor(self.z))

    def __ceil__(self):
        """
            Ceil this vector, rounding towards positive infinity
        :return: Ceiled vector
        """
        return Vector3(math.ceil(self.x), math.ceil(self.y), math.ceil(self.z))

    def flatten(self):
        """
            Get the magnitude of this vector
        :return: Vector magnitude
        """
        return (self.x**2 + self.y**2 + self.z**2)**.5

    def normal(self):
        """
            Get a normalized version of this vector, with length of 1
        :return: Unit vector pointing in the same direction
        """
        return self / self.flatten()

    def dot(self, other):
        """
            Get the dot product between this vector and another vector
        :param other: Vector to dot
        :return: Dot product between vectors
        """
        if not isinstance(other, Vector3):
            raise TypeError("Attempt to dot vector with invalid type")
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        """
            Get the cross product between this vector and another vector
        :param other: Vector to cross
        :return: Cross product between vectors
        """
        if not isinstance(other, Vector3):
            raise TypeError("Attempt to cross vector with invalid type")
        x = self.y * other.z - self.z * other.y
        y = self.z * other.x - self.x * other.z
        z = self.x * other.y - self.y * other.x
        return Vector3(x, y, z)

    def to_2d(self):
        """
            Convert this vector to a 2d vector. Extra dimensions are truncated
        :return: New vector with 2 dimensions
        """
        return Vector2(self.x, self.y)


def rect_list(top_left, bottom_right):
    """
        From a top-left and bottom-right vector, form the other 6 points in a rectangular prism and
        return them as a list of vectors
    :param top_left: Top left point on the prism
    :param bottom_right: Bottom right point on the prism
    :return: List of vectors forming a rectangular prism
    """
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
