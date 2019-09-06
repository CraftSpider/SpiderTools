
import math
import numbers


def _getdef(list, num, default=None):
    """
        Get value from list with default
    :param list: List to get value from
    :param num: Index to get
    :param default: Default to return if index isn't in list
    :return: Value at index, or default
    """
    if num < len(list):
        return list[num]
    return default


def _narrow(list, l):
    """
        Possibly narrow a vector value list, if any of the values past `l` are not 0
    :param list: List to narrow
    :param l: Minimum length
    :return: Original list or list narrowed to length `l`
    """
    for i in range(l, len(list)):
        if i != 0:
            return list
    return list[:l]


def _cut_matrix(matrix, pos):
    """
        'Cut' a matrix, removing a vertical and horizontal line, returning the rest
    :param matrix: Matrix to cut
    :param pos: Column to remove
    :return: Matrix reduced in size
    """
    return tuple(tuple(x for i, x in enumerate(matrix[j]) if i != pos) for j in range(1, len(matrix)))


def _determinant(matrix):
    """
        Calculate the determinant of an N-Dimensional square matrix
    :param matrix: Matrix to calculate determinant of
    :return: Determinant of matrix
    """
    if len(matrix) == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    return sum(_determinant(_cut_matrix(matrix, i)) * (1 if i % 2 == 0 else -1) for i in range(len(matrix)))


def _semi_determinant(matrix):
    """
        Get a tuple containing each of the determinant values for a matrix, for use in getting orthogonal vectors
    :param matrix: Matrix to get determinant components of
    :return: Tuple of determinant components
    """
    return tuple(_determinant(_cut_matrix(matrix, i)) * (1 if i % 2 == 0 else -1) for i in range(len(matrix)))


def _vecs_to_tuple(vecs, dims):
    """
        Convert a list of vectors into a matrix of them, stacked vertically, with the given number of dimensions.
        A One Vector is prepended, to allow determinant calculation
    :param vecs: Vectors to convert to a matrix
    :param dims: Number of dimensions of the vectors
    :return: Matrix made from vectors
    """
    return (tuple(1 for _ in range(vecs[0].dimensions)),) + tuple(x.to_tuple(dims) for x in vecs)


class Vector:
    """
        A generic vector type, supporting any number of dimensions. Will delegate to subclasses
        that are registered for a specific number of dimensions, if such a subclass exists.
    """

    __slots__ = ("dimensions", "_vals")

    _registry = {}
    _numeric = {}

    def __new__(cls, *args):
        """
            Create a new vector. Returns a standard vector if there's no
            registered special class for this number of dimensions, in which
            case it returns a new instance of that class
        :param args: Initialization args
        :return: New vector
        """
        if len(args) == 0:
            raise ValueError("Length of vector initialization args must be at least 1")
        elif len(args) in cls._numeric:
            cls = cls._numeric[len(args)]

        for i in args:
            if not isinstance(i, numbers.Real):
                raise TypeError("Vector arguments must be real numbers")

        self = object.__new__(cls)
        return self

    def __init__(self, *args):
        """
            Initialize a standard vector. Set the number of dimensions and
            the values of those dimensions
        :param args: Dimensions values of this vector
        """
        self._vals = []
        if len(args) == 1:
            self.dimensions = int(args[0])
            for _ in range(self.dimensions):
                self._vals.append(0)
        else:
            self.dimensions = len(args)
            for i in args:
                self._vals.append(i)

    def __repr__(self):
        """
            Return a string representing this vector, with number of dimensions
            and individual values
        :return: String form of vector
        """
        return f"Vector{self.dimensions}({', '.join(map(str, self._vals))})"

    def __eq__(self, other):
        """
            Determine whether this vector is equal to another vector
        :param other: Vector to compare against
        :return: Whether vectors are equal
        """
        if isinstance(other, Vector):
            d = max(self.dimensions, other.dimensions)
            for i in range(d):
                a = _getdef(self._vals, i, 0)
                b = _getdef(other._vals, i, 0)
                if a != b:
                    return False
            return True
        else:
            return NotImplemented

    def __init_subclass__(cls, *args, **kwargs):
        """
            Initialize a new vector subclass. If the subclass name ends with a number,
            it will be implicitly assigned that number of dimensions. Alternatively,
            passing the `dimensions` keyword will assign the vector to that dimension number
        :param args: Subclass arguments
        :param kwargs: Subclass keyword arguments
        """
        dims = kwargs.pop("dimensions", None)
        super().__init_subclass__(**kwargs)
        name = cls.__name__

        Vector._registry[name] = cls
        if dims is not None:
            if not isinstance(dims, int):
                raise TypeError("Vector dimensions must be integer")
            Vector._numeric[dims] = cls
            return

        i = 0
        for i in reversed(range(len(name))):
            if not name[i].isnumeric():
                break
        i += 1
        print(name[i:])
        if name[i:]:
            num = int(name[i:])
            if num in Vector._numeric:
                raise TypeError("Attempt to register a specialized vector that already has associated type")
            Vector._numeric[num] = cls

    def __getitem__(self, item):
        """
            Get the value of a dimension of this vector
        :param item: Dimension to get value of
        :return: Value of dimension
        """
        if item < 0:
            raise ValueError("Vector dimension index must be non-negative")
        elif item >= self.dimensions:
            raise ValueError("Vector dimension index out of range")
        return self._vals[item]

    def __setitem__(self, key, value):
        """
            Set the value of a dimension of this vector
        :param key: Dimension to set value of
        :param value: Value to set dimension to
        """
        if key < 0:
            raise ValueError("Vector dimension index must be non-negative")
        elif key >= self.dimensions:
            raise ValueError("Vector dimension index out of range")
        self._vals[key] = value

    def __add__(self, other):
        """
            Sum two vectors, or a vector and an integer. If one is wider than the other, the
            resultant vector will be widened if the result of any of the components beyond
            the smaller vector is non-zero
        :param other: Vector or real number to add across vector components
        :return: Resultant vector
        """
        if isinstance(other, Vector):
            new = []
            d = max(self.dimensions, other.dimensions)
            l = min(self.dimensions, other.dimensions)
            for i in range(d):
                new.append(_getdef(self._vals, i, 0) + _getdef(other._vals, i, 0))
            return Vector(*_narrow(new, l))
        elif isinstance(other, numbers.Real):
            new = []
            for i in self._vals:
                new.append(i + other)
            return Vector(*new)
        else:
            return NotImplemented

    def __sub__(self, other):
        """
            Subtract a vector, or an integer, from this vector. If one vector is wider than the other, the
            resultant vector will be widened if the result of any of the components beyond
            the smaller vector is non-zero
        :param other: Vector or real number to subtract across vector components
        :return: Resultant vector
        """
        if isinstance(other, Vector):
            new = []
            d = max(self.dimensions, other.dimensions)
            l = min(self.dimensions, other.dimensions)
            for i in range(d):
                new.append(_getdef(self._vals, i, 0) - _getdef(other._vals, i, 0))
            return Vector(*_narrow(new, l))
        elif isinstance(other, numbers.Real):
            new = []
            for i in self._vals:
                new.append(i - other)
            return Vector(*new)
        else:
            return NotImplemented

    def __mul__(self, other):
        """
            Multiply two vectors, or a vector and an integer. If one is wider than the other, the
            resultant vector will be widened if the result of any of the components beyond
            the smaller vector is non-zero
        :param other: Vector or real number to multiply across vector components
        :return: Resultant vector
        """
        if isinstance(other, Vector):
            new = []
            d = max(self.dimensions, other.dimensions)
            l = min(self.dimensions, other.dimensions)
            for i in range(d):
                new.append(_getdef(self._vals, i, 0) * _getdef(other._vals, i, 0))
            return Vector(*_narrow(new, l))
        elif isinstance(other, numbers.Real):
            new = []
            for i in self._vals:
                new.append(i * other)
            return Vector(*new)
        else:
            return NotImplemented

    def __truediv__(self, other):
        """
            Divide two vectors, or a vector and an integer. If one is wider than the other, the
            resultant vector will be widened if the result of any of the components beyond
            the smaller vector is non-zero
        :param other: Vector or real number to divide across vector components
        :return: Resultant vector
        """
        if isinstance(other, Vector):
            if other.dimensions < self.dimensions:
                raise ValueError("Cannot divide vector by smaller vector")
            new = []
            for i in range(other.dimensions):
                new.append(_getdef(self._vals, i, 0) / other._vals[i])
            return Vector(*_narrow(new, other.dimensions))
        elif isinstance(other, numbers.Real):
            new = []
            for i in self._vals:
                new.append(i / other)
            return Vector(*new)
        else:
            return NotImplemented

    def __floordiv__(self, other):
        """
            Floor-divide two vectors, or a vector and an integer. If one is wider than the other, the
            resultant vector will be widened if the result of any of the components beyond
            the smaller vector is non-zero
        :param other: Vector or real number to divide across vector components
        :return: Resultant vector
        """
        if isinstance(other, Vector):
            if other.dimensions < self.dimensions:
                raise ValueError("Cannot divide vector by smaller vector")
            new = []
            for i in range(other.dimensions):
                new.append(_getdef(self._vals, i, 0) // other._vals[i])
            return Vector(*_narrow(new, other.dimensions))
        elif isinstance(other, numbers.Real):
            new = []
            for i in self._vals:
                new.append(i // other)
            return Vector(*new)
        else:
            return NotImplemented

    def __mod__(self, other):
        """
            Modulo two vectors, or a vector and an integer. If one is wider than the other, the
            resultant vector will be widened if the result of any of the components beyond
            the smaller vector is non-zero
        :param other: Vector or real number to add across vector components
        :return: Resultant vector
        """
        if isinstance(other, Vector):
            new = []
            d = max(self.dimensions, other.dimensions)
            l = min(self.dimensions, other.dimensions)
            for i in range(d):
                new.append(_getdef(self._vals, i, 0) % _getdef(other._vals, i, 0))
            return Vector(*_narrow(new, l))
        elif isinstance(other, numbers.Real):
            new = []
            for i in self._vals:
                new.append(i % other)
            return Vector(*new)
        else:
            return NotImplemented

    def __pow__(self, power, modulo=None):
        """
            Get this vector to a given power, optionally with a given modulo
        :param power: Power to raise this vector to
        :param modulo: Optional modulo to apply to the power operation
        :return: Resultant vector
        """
        if isinstance(power, numbers.Real):
            new = []
            for i in self._vals:
                new.append(pow(i, power, modulo))
            return Vector(*new)
        else:
            return NotImplemented

    def __or__(self, other):
        """
            Get the inner, or dot, product of this vector with another vector
        :param other: Vector to dot with
        :return: Dot product of the two vectors
        """
        if isinstance(other, Vector):
            return self.dot(other)
        else:
            return NotImplemented

    def __rmul__(self, other):
        """
            Handle when the vector is on the right-hand side of an equation
        :param other: Value to multiply by
        :return: Multiplied vector
        """
        return self.__mul__(other)

    def __neg__(self):
        """
            Return the negation of this vector
        :return: Negated vector
        """
        return Vector(*[-x for x in self._vals])

    def __pos__(self):
        """
            Return the positive form of this vector
        :return: Positive vector
        """
        return Vector(*[+x for x in self._vals])

    def __abs__(self):
        """
            Get the absolute value/norm/magnitude of this vector
        :return: Vector magnitude
        """
        return self.magnitude()

    def __invert__(self):
        """
            Get the inversion of this vector
        :return: Inverted Vector
        """
        return Vector(*[-x for x in self._vals])

    def __round__(self, n=None):
        """
            Round this vector to a given number of places
        :param n: Places to round to
        :return: Rounded vector
        """
        new = []
        for i in range(self.dimensions):
            new.append(round(self._vals[i], n))
        return Vector(*new)

    def __trunc__(self):
        """
            Truncate this vector towards 0
        :return: Truncated vector
        """
        new = []
        for i in range(self.dimensions):
            new.append(math.trunc(self._vals[i]))
        return Vector(*new)

    def __floor__(self):
        """
            Floor this vector towards -inf
        :return: Floored vector
        """
        new = []
        for i in range(self.dimensions):
            new.append(math.floor(self._vals[i]))
        return Vector(*new)

    def __ceil__(self):
        """
            Ceil this vector towards inf
        :return: Ceiled vector
        """
        new = []
        for i in range(self.dimensions):
            new.append(math.ceil(self._vals[i]))
        return Vector(*new)

    @property
    def x(self):
        """
            Get the X component of this vector, or the first dimension
        :return: X component
        """
        return self._vals[0]

    @x.setter
    def x(self, val):
        """
            Set the X component of this vector, or the first dimension
        :param val: Value to set X component to
        """
        self._vals[0] = val

    @property
    def y(self):
        """
            Get the Y component of this vector, or the second dimension, if it exists
        :return: Y component
        """
        if self.dimensions < 2:
            raise TypeError(f"Vector{self.dimensions} does not have y component")
        return self._vals[1]

    @y.setter
    def y(self, val):
        """
            Set the Y component of this vector, or the second dimension, if it exists
        :param val: Value to set Y component to
        """
        if self.dimensions < 2:
            raise TypeError(f"Vector{self.dimensions} does not have y component")
        self._vals[1] = val

    @property
    def z(self):
        """
            Get the Z component of this vector, or the third dimension, if it exists
        :return: Z component
        """
        if self.dimensions < 3:
            raise TypeError(f"Vector{self.dimensions} does not have y component")
        return self._vals[2]

    @z.setter
    def z(self, val):
        """
            Set the Z component of this vector, or the third dimension, if it exists
        :param val: Value to set Z component to
        """
        if self.dimensions < 3:
            raise TypeError(f"Vector{self.dimensions} does not have y component")
        self._vals[2] = val

    @classmethod
    def get_orthogonal(cls, *vecs):
        """
            From a number of dimensions, get a single vector that represents a vector orthogonal to all of them.
            This may be a Zero Vector if any vectors are parallel. Returned vector will be of the highest
            dimensionality in the input vectors
        :param vecs: Vectors to get orthogonal vector from
        :return: Vector orthogonal to all input vectors
        """
        high_dim = max(vecs, key=lambda x: x.dimensions).dimensions
        if len(vecs) != high_dim - 1:
            raise ValueError(f"Incorrect number of arguments to get_orthogonal. Expected {high_dim - 1} vectors, got "
                             f"{len(vecs)}")

        matrix = _vecs_to_tuple(vecs, high_dim)
        return Vector(*_semi_determinant(matrix))

    def dot(self, other):
        """
            Get the inner, or dot, product of this vector with another vector
        :param other: Vector to dot with
        :return: Dot product of the two vectors
        """
        if not isinstance(other, Vector):
            raise TypeError(f"Attempt to cross Vector{self.dimensions} with invalid type")
        d = max(self.dimensions, other.dimensions)
        out = 0
        for i in range(d):
            out += _getdef(self._vals, i, 0) * _getdef(other._vals, i, 0)
        return out

    def magnitude(self):
        """
            Get the absolute value/norm/magnitude of this vector
        :return: Vector norm
        """
        return sum([x**2 for x in self._vals])**.5

    def magnitude_squared(self):
        """
            Get the magnitude of this vector squared. Avoid an extra sqrt + square
            operation in some cases.
        :return: Vector magnitude squared
        """
        return sum([x**2 for x in self._vals])

    def normal(self):
        """
            Get this vector as a unit/normal vector
        :return: Unit vector of this vector
        """
        return self / self.magnitude()

    def to_dim(self, d):
        """
            Convert this vector to a given number of dimensions. Any dimensions truncated by
            this operation become 0, and all new dimensions are set to 0
        :param d: Number of dimensions for the resulting vector
        :return: New vector with given number of dimensions
        """
        new = []
        for i in range(d):
            new.append(_getdef(self._vals, i, 0))
        return Vector(*new)

    def to_tuple(self, d=None):
        """
            Convert this vector to a tuple, optionally with the given number of dimensions. Conversion follows the
            same rules as to_dim for trancate and extend.
        :param d: Number of dimensions for the resulting tuple
        :return: Tuple containing values of vector
        """
        if d is None:
            d = self.dimensions
        return tuple(_getdef(self._vals, i, 0) for i in range(d))


class Vector3(Vector):
    """
        Specialization of a Vector for 3 dimensions, adding support for cross-product of 3D vectors
    """

    def __matmul__(self, other):
        """
            Cross this 3D vector with another 3D vector
        :param other: Vector to cross this vector with
        :return: Cross product of two vectors
        """
        if isinstance(other, Vector3):
            return self.cross(other)
        else:
            return NotImplemented

    def cross(self, other):
        """
            Cross this 3D vector with another 3D vector
        :param other: Vector to cross this vector with
        :return: Cross product of two vectors
        """
        if not isinstance(other, Vector3):
            raise TypeError("Attempt to cross Vector3 with invalid type")
        x = self.y * other.z - self.z * other.y
        y = self.z * other.x - self.x * other.z
        z = self.x * other.y - self.y * other.x
        return Vector3(x, y, z)


Vector3.UNIT_X = Vector3(1, 0, 0)
Vector3.UNIT_Y = Vector3(0, 1, 0)
Vector3.UNIT_Z = Vector3(0, 0, 1)


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
