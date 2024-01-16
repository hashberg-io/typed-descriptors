# pylint: disable = missing-docstring

import sys
from typing import Optional
import pytest
from typed_descriptors import Attr

@pytest.mark.parametrize("attr_name", [None, "_x", "_y", "__x", "__y"])
def test_base_set_name(attr_name: Optional[str]) -> None:
    class C:
        x = Attr(int, lambda _, x: x >= 0, attr_name=attr_name)
        def __init__(self, x: int) -> None:
            self.x = x
    C(0)

@pytest.mark.parametrize("attr_name", [None, "_x", "_y", "__x", "__y"])
def test_base_set_name_slots(attr_name: Optional[str]) -> None:
    if attr_name is not None:
        slot_name = attr_name
    else:
        slot_name = "__x"
    class C:
        x = Attr(int, lambda _, x: x >= 0, attr_name=attr_name)
        __slots__ = (slot_name,)
        def __init__(self, x: int) -> None:
            self.x = x
    C(0)

name_slot_error = (
    AttributeError
    if sys.version_info[1] >= 12
    else RuntimeError
)

@pytest.mark.parametrize("attr_name", [None, "_x", "_y", "__x", "__y"])
def test_base_set_name_slots_error(attr_name: Optional[str]) -> None:
    with pytest.raises(name_slot_error):
        class C:
            x = Attr(int, lambda _, x: x >= 0, attr_name=attr_name)
            __slots__ = ()
    class D:
        x = Attr(int, lambda _, x: x >= 0, attr_name=attr_name)
        __slots__ = ("__dict__",)
        def __init__(self, x: int) -> None:
            self.x = x
    D(0)

@pytest.mark.parametrize("attr_name", [None, "x", "y", "_y", "__x", "__y"])
def test_base_set_name_slots_protected(attr_name: Optional[str]) -> None:
    if attr_name is not None:
        slot_name = attr_name
    else:
        slot_name = "__x"
    class C:
        _x = Attr(int, lambda _, x: x >= 0, attr_name=attr_name)
        __slots__ = (slot_name,)
        def __init__(self, x: int) -> None:
            self._x = x
    C(0)


@pytest.mark.parametrize("attr_name", [None, "x", "y", "_x" "_y", "__y", "___x"])
def test_base_set_name_slots_private(attr_name: Optional[str]) -> None:
    if attr_name is not None:
        slot_name = attr_name
    else:
        slot_name = "___x"
    class C:
        __x = Attr(int, lambda _, x: x >= 0, attr_name=attr_name)
        __slots__ = (slot_name,)
        def __init__(self, x: int) -> None:
            self.__x = x
    C(0)
