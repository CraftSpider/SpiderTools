
from typing import Union, overload
import numbers
from spidertools.math.vector import Vector3


ValidRotator = Union['Rotator', numbers.Real]


def _float_correct(vec: Vector3) -> None: ...


class Rotator:

    __slots__ = ("x", "y", "z")

    x: numbers.Real
    y: numbers.Real
    z: numbers.Real

    def __init__(self, x: numbers.Real, y: numbers.Real = ..., z: numbers.Real = ..., radians: bool = ...) -> None: ...

    def __repr__(self) -> str: ...

    def __add__(self, other: ValidRotator) -> 'Rotator': ...

    def __sub__(self, other: ValidRotator) -> 'Rotator': ...

    @overload
    def __mul__(self, other: Vector3) -> Vector3: ...
    @overload
    def __mul__(self, other: ValidRotator) -> 'Rotator': ...

    def __truediv__(self, other: ValidRotator) -> 'Rotator': ...

    @overload
    def __rmul__(self, other: Vector3) -> Vector3: ...
    @overload
    def __rmul__(self, other: ValidRotator) -> 'Rotator': ...

    def from_vectors(self, start: Vector3, end: Vector3 = ...) -> 'Rotator': ...
