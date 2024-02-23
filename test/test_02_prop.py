# pylint: disable = missing-docstring

from typing import Any, List
import pytest
from typed_descriptors import Attr, Prop,cached_property

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x", [0, 10])
def test_single_prop_valid(x: int, decorator: bool) -> None:
    class C:
        if not decorator:
            @cached_property
            def x(self) -> int:
                return x
        else:
            x = Prop(int, lambda _: x) # type: ignore
    c = C()
    assert c.x == x

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x", [0, 10])
def test_single_prop_cache(x: int, decorator: bool) -> None:
    class C:
        if decorator:
            @cached_property
            def x(self) -> int:
                return x
        else:
            x = Prop(int, lambda _: x) # type: ignore
    c = C()
    assert not C.x.is_cached_on(c)
    assert c.x == x
    assert C.x.is_cached_on(c)

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x", [0, 10])
def test_single_prop_cache_delete(x: int, decorator: bool) -> None:
    class C:
        if decorator:
            @cached_property
            def x(self) -> int:
                return x
        else:
            x = Prop(int, lambda _: x) # type: ignore
    c = C()
    assert c.x == x
    del c.x
    assert not C.x.is_cached_on(c)
    assert c.x == x
    assert C.x.is_cached_on(c)

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x", ["a", [0, 1]])
def test_single_prop_type_error(x: Any, decorator: bool) -> None:
    class C:
        if decorator:
            @cached_property
            def x(self) -> int:
                return x # type: ignore
        else:
            x = Prop(int, lambda _: x) # type: ignore
    c = C()
    with pytest.raises(TypeError):
        assert c.x == x

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("y", [[], [0, 1, 2]])
def test_prop_attr_dependency(y: List[int], decorator: bool) -> None:
    class C:
        if decorator:
            @cached_property
            def x(self) -> int:
                return len(self.y)
        else:
            x = Prop(int, lambda self: len(self.y)) # type: ignore
        y = Attr(List[int])
    c = C()
    c.y = y
    assert c.x == len(y)

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("y", [[], [0, 1, 2]])
def test_prop_attr_type_error(y: List[int], decorator: bool) -> None:
    class C:
        if decorator:
            @cached_property
            def x(self) -> int:
                return self.y # type: ignore
        else:
            x = Prop(int, lambda self: self.y) # type: ignore
        y = Attr(List[int])
    c = C()
    c.y = y
    with pytest.raises(TypeError):
        assert c.x == len(y)
