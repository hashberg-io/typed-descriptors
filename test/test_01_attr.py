# pylint: disable = missing-docstring

from typing import Any, Optional
import pytest
from typed_descriptors import Attr

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x", [0])
@pytest.mark.parametrize("backed_by", [None, "x", "_x", "_y", "__x", "__y"])
def test_single_attr_valid(x: Any, decorator: bool, backed_by: Optional[str]) -> None:
    class C:
        if decorator:
            # pylint: disable = method-hidden
            if backed_by is None:
                @Attr.validator
                def x(self, value: int) -> bool:
                    return value >= 0
            else:
                @Attr.validator(backed_by=backed_by)
                def x(self, value: int) -> bool:
                    return value >= 0
        else:
            x = Attr(int, lambda _, x: x >= 0, backed_by=backed_by)
        def __init__(self, x: int) -> None:
            self.x = x
    C(x)

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x", [0])
@pytest.mark.parametrize("backed_by", [None, "_x", "_y", "__x", "__y"])
def test_single_attr_valid_slots(x: Any, decorator: bool, backed_by: Optional[str]) -> None:
    if backed_by is None:
        backing_attr = "__x"
    else:
        backing_attr = backed_by
    class C:
        if decorator:
            # pylint: disable = method-hidden
            if backed_by is None:
                @Attr.validator
                def x(self, value: int) -> bool:
                    return value >= 0
            else:
                @Attr.validator(backed_by=backed_by)
                def x(self, value: int) -> bool:
                    return value >= 0
        else:
            x = Attr(int, lambda _, x: x >= 0, backed_by=backed_by)

        __slots__ = (backing_attr,)
        def __init__(self, x: int) -> None:
            self.x = x
    C(x)


@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x", [1])
@pytest.mark.parametrize("backed_by", [None, "x", "_x", "_y", "__x", "__y"])
def test_single_attr_readonly(x: Any, decorator: bool, backed_by: Optional[str]) -> None:
    class C:
        if decorator:
            # pylint: disable = method-hidden
            @Attr.validator(readonly=True, backed_by=backed_by)
            def x(self, value: int) -> bool:
                return value >= 0
        else:
            x = Attr(int, lambda _, x: x >= 0, readonly=True, backed_by=backed_by)
        def __init__(self, x: int) -> None:
            self.x = x
    C(x)
    with pytest.raises(AttributeError):
        C(0).x = x

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x", [1])
@pytest.mark.parametrize("backed_by", [None, "_x", "_y", "__x", "__y"])
def test_single_attr_readonly_slots(x: Any, decorator: bool, backed_by: Optional[str]) -> None:
    if backed_by is None:
        backing_attr = "__x"
    else:
        backing_attr = backed_by
    class C:
        if decorator:
            # pylint: disable = method-hidden
            @Attr.validator(readonly=True, backed_by=backed_by)
            def x(self, value: int) -> bool:
                return value >= 0
        else:
            x = Attr(int, lambda _, x: x >= 0, readonly=True, backed_by=backed_by)
        __slots__ = (backing_attr,)
        def __init__(self, x: int) -> None:
            self.x = x
    C(x)
    with pytest.raises(AttributeError):
        C(0).x = x

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x, y", [(0, 2), (1, 1)])
def test_two_attr_valid(x: Any, y: Any, decorator: bool) -> None:
    class C:
        if decorator:
            # pylint: disable = method-hidden
            @Attr.validator
            def x(self, value: int) -> bool:
                return value >= 0
            @Attr.validator
            def y(self, value: int) -> bool:
                return value >= self.x
        else:
            x = Attr(int, lambda _, x: x >= 0)
            y = Attr(int, lambda self, y: y >= self.x)
        def __init__(self, x: int, y: int) -> None:
            self.x = x
            self.y = y
    C(x, y)

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x, y", [(0, 2), (1, 1)])
def test_two_attr_valid_slots(x: Any, y: Any, decorator: bool) -> None:
    class C:
        if decorator:
            # pylint: disable = method-hidden
            @Attr.validator
            def x(self, value: int) -> bool:
                return value >= 0
            @Attr.validator
            def y(self, value: int) -> bool:
                return value >= self.x
        else:
            x = Attr(int, lambda _, x: x >= 0)
            y = Attr(int, lambda self, y: y >= self.x)
        __slots__ = ("__x", "__y")
        def __init__(self, x: int, y: int) -> None:
            self.x = x
            self.y = y
    C(x, y)

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x", ["hello", 1.0])
def test_single_attr_type_error(x: Any, decorator: bool) -> None:
    class C:
        if decorator:
            # pylint: disable = method-hidden
            @Attr.validator
            def x(self, value: int) -> bool:
                return value >= 0
        else:
            x = Attr(int, lambda _, x: x >= 0)
        def __init__(self, x: int) -> None:
            self.x = x
    with pytest.raises(TypeError):
        C(x)
    with pytest.raises(TypeError):
        c = C(0)
        c.x = x

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x", [-1])
def test_single_attr_value_error(x: Any, decorator: bool) -> None:
    class C:
        if decorator:
            # pylint: disable = method-hidden
            @Attr.validator
            def x(self, value: int) -> bool:
                return value >= 0
        else:
            x = Attr(int, lambda _, x: x >= 0)
        def __init__(self, x: int) -> None:
            self.x = x
    with pytest.raises(ValueError):
        C(x)
    with pytest.raises(ValueError):
        C(0).x = x

@pytest.mark.parametrize("decorator", [False, True])
@pytest.mark.parametrize("x, y", [(0, -1), (-1, 2), (3, 2)])
def test_two_attr_value_error(x: Any, y: Any, decorator: bool) -> None:
    class C:
        if decorator:
            # pylint: disable = method-hidden
            @Attr.validator
            def x(self, value: int) -> bool:
                return value >= 0
            @Attr.validator
            def y(self, value: int) -> bool:
                return value >= self.x
        else:
            x = Attr(int, lambda _, x: x >= 0)
            y = Attr(int, lambda self, y: y >= self.x)
        def __init__(self, x: int, y: int) -> None:
            self.x = x
            self.y = y
    with pytest.raises(ValueError):
        C(x, y)
    with pytest.raises(ValueError):
        C(x, x+1).y = y
