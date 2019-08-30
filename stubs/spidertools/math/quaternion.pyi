
from typing import overload, TypeVar, Union
import numbers
import spidertools.math.vector as vector


_T = TypeVar('_T')


def _float_correct(item: _T) -> _T: ...


ValidQuat = Union['Quaternion', numbers.Real]


class Quaternion:

    __slots__ = ("x", "y", "z", "w")

    w: numbers.Real
    x: numbers.Real
    y: numbers.Real
    z: numbers.Real

    @overload
    def __init__(self, x: numbers.Real, y: numbers.Real = ..., z: numbers.Real = ..., w: numbers.Real = ...) -> None: ...
    @overload
    def __init__(self, x: 'Quaternion') -> None: ...

    def __repr__(self) -> str: ...

    def __float__(self) -> float: ...

    def __add__(self, other: ValidQuat) -> 'Quaternion': ...

    def __sub__(self, other: ValidQuat) -> 'Quaternion': ...

    def __mul__(self, other: ValidQuat) -> 'Quaternion': ...

    @overload
    def __rmul__(self, other: ValidQuat) -> 'Quaternion': ...
    @overload
    def __rmul__(self, other: vector.Vector3) -> vector.Vector3: ...

    def __truediv__(self, other: numbers.Real) -> 'Quaternion': ...

    def __neg__(self) -> 'Quaternion': ...

    def __abs__(self) -> float: ...

    def flatten(self) -> float: ...

    def normal(self) -> 'Quaternion': ...

    def inverse(self) -> 'Quaternion': ...
