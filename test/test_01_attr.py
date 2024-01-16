# pylint: disable = missing-docstring

from typing import Any
import pytest
from typed_descriptors import Attr

@pytest.mark.parametrize("x", [0, 10])
def test_single_attr_valid(x: Any) -> None:
    class C:
        x = Attr(int, lambda _, x: x >= 0)
        def __init__(self, x: int) -> None:
            self.x = x
    C(x)

@pytest.mark.parametrize("x", ["hello", 1.0])
def test_single_attr_type_error(x: Any) -> None:
    class C:
        x = Attr(int, lambda _, x: x >= 0)
        def __init__(self, x: int) -> None:
            self.x = x
    with pytest.raises(TypeError):
        C("hello") # type: ignore
    with pytest.raises(TypeError):
        c = C(0)
        c.x = x

@pytest.mark.parametrize("x", [-1])
def test_single_attr_value_error(x: Any) -> None:
    class C:
        x = Attr(int, lambda _, x: x >= 0)
        def __init__(self, x: int) -> None:
            self.x = x
    with pytest.raises(ValueError):
        C(x)
    with pytest.raises(ValueError):
        C(0).x = x

@pytest.mark.parametrize("x", [1])
def test_single_attr_readonly(x: Any) -> None:
    class C:
        x = Attr(int, lambda _, x: x >= 0, readonly=True)
        def __init__(self, x: int) -> None:
            self.x = x
    C(x)
    with pytest.raises(AttributeError):
        C(0).x = x

@pytest.mark.parametrize("x, y", [(0, 2), (1, 1)])
def test_two_attr_valid(x: Any, y: Any) -> None:
    class C:
        x = Attr(int, lambda _, x: x >= 0)
        y = Attr(int, lambda self, y: y >= self.x)
        def __init__(self, x: int, y: int) -> None:
            self.x = x
            self.y = y
    C(x, y)

@pytest.mark.parametrize("x, y", [(0, -1), (-1, 2), (3, 2)])
def test_two_attr_value_error(x: Any, y: Any) -> None:
    class C:
        x = Attr(int, lambda _, x: x >= 0)
        y = Attr(int, lambda self, y: y >= self.x)
        def __init__(self, x: int, y: int) -> None:
            self.x = x
            self.y = y
    with pytest.raises(ValueError):
        C(x, y)
    with pytest.raises(ValueError):
        C(x, x+1).y = y
