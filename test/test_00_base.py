# pylint: disable = missing-docstring

import sys
from typing import Optional
import pytest
from typed_descriptors import Attr
from typed_descriptors.base import name_mangle

@pytest.mark.parametrize("backed_by", [None, "x", "_x", "_y", "__x", "__y"])
def test_base_set_name(backed_by: Optional[str]) -> None:
    if backed_by is None:
        backing_attr = "x"
    else:
        backing_attr = backed_by
    class C:
        x = Attr(int, lambda _, x: x >= 0, backed_by=backed_by)
        def __init__(self, x: int) -> None:
            self.x = x
    c = C(0)
    assert name_mangle(C, backing_attr) in c.__dict__

@pytest.mark.parametrize("backed_by", [None, "_x", "_y", "__x", "__y"])
def test_base_set_name_slots(backed_by: Optional[str]) -> None:
    if backed_by is None:
        backing_attr = "__x"
    else:
        backing_attr = backed_by
    class C:
        x = Attr(int, lambda _, x: x >= 0, backed_by=backed_by)
        __slots__ = (backing_attr,)
        def __init__(self, x: int) -> None:
            self.x = x
    c = C(0)
    assert hasattr(c, name_mangle(C, backing_attr))

@pytest.mark.parametrize("backed_by", [None, "x", "_x", "_y", "__x", "__y"])
def test_base_set_name_slots_dict(backed_by: Optional[str]) -> None:
    if backed_by is None:
        backing_attr = "x"
    else:
        backing_attr = backed_by
    class C:
        x = Attr(int, lambda _, x: x >= 0, backed_by=backed_by)
        __slots__ = ("__dict__",)
        def __init__(self, x: int) -> None:
            self.x = x
    c = C(0)
    assert name_mangle(C, backing_attr) in c.__dict__

name_slot_error = (
    TypeError
    if sys.version_info[1] >= 12
    else RuntimeError
)

@pytest.mark.parametrize("backed_by", [None, "x", "_x", "_y", "__x", "__y"])
def test_base_set_name_slots_error(backed_by: Optional[str]) -> None:
    with pytest.raises(name_slot_error):
        class C:
            x = Attr(int, lambda _, x: x >= 0, backed_by=backed_by)
            __slots__ = ("some_other_attr")
            # Recall that __slots__ = () is interpreted as not declaring slots
