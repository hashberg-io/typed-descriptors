# pylint: disable = missing-docstring

from typing import Any, List
import pytest
from typed_descriptors import Attr, Prop


@pytest.mark.parametrize("x", [0, 10])
def test_single_prop_valid(x: int) -> None:
    class C:
        x = Prop(int, lambda _: x)
    c = C()
    assert c.x == x

@pytest.mark.parametrize("x", [0, 10])
def test_single_prop_cache(x: int) -> None:
    class C:
        x = Prop(int, lambda _: x)
    c = C()
    assert not C.x.is_cached_on(c)
    assert c.x == x
    assert C.x.is_cached_on(c)

@pytest.mark.parametrize("x", [0, 10])
def test_single_prop_cache_delete(x: int) -> None:
    class C:
        x = Prop(int, lambda _: x)
    c = C()
    assert c.x == x
    del c.x
    assert not C.x.is_cached_on(c)
    assert c.x == x
    assert C.x.is_cached_on(c)

@pytest.mark.parametrize("x", ["a", [0, 1]])
def test_single_prop_type_error(x: Any) -> None:
    class C:
        x = Prop(int, lambda _: x)
    c = C()
    with pytest.raises(TypeError):
        assert c.x == x


@pytest.mark.parametrize("y", [[], [0, 1, 2]])
def test_prop_attr_dependency(y: List[int]) -> None:
    class C:
        x = Prop(int, lambda self: len(self.y))
        y = Attr(List[int])
    c = C()
    c.y = y
    assert c.x == len(y)

@pytest.mark.parametrize("y", [[], [0, 1, 2]])
def test_prop_attr_type_error(y: List[int]) -> None:
    class C:
        x = Prop(int, lambda self: self.y)
        y = Attr(List[int])
    c = C()
    c.y = y
    with pytest.raises(TypeError):
        assert c.x == len(y)
