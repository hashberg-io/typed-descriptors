# pylint: disable = missing-docstring

import sys
from typing import Union
import pytest
from typed_descriptors import Attr

if sys.version_info[1] >= 9:
    from collections.abc import Sequence
else:
    from typing import Sequence

def test_getting_started_example() -> None:
    # pylint: disable = import-outside-toplevel

        class MyClass:

            x = Attr(int, lambda _, x: x >= 0, readonly=True)
            y = Attr(Sequence[int], lambda self, y: len(y) <= self.x)

            def __init__(self, x: int, y: Sequence[int]):
                self.x = x
                self.y = y

        myobj = MyClass(3, [0, 2, 5]) # OK
        myobj.y = (0, 1)              # OK
        with pytest.raises(ValueError):
            myobj.y = [0, 2, 4, 6]
        with pytest.raises(AttributeError):
            myobj.x = 5
        with pytest.raises(TypeError):
            myobj.y = 5
        with pytest.raises(TypeError):
            myobj.y = ["hi", "bye"]

def test_attr_validator_example_1() -> None:
    class MyClass:
        @Attr.validator
        def x(self, value: Sequence[str]) -> bool:
            ''' Validator function for attribute 'C.x'. '''
            return 1 <= len(value) <= 3

    myobj = MyClass()
    myobj.x = ["a", "b", "c"]
    assert myobj.x == ["a", "b", "c"]
    assert "x" in myobj.__dict__
    assert myobj.__dict__["x"] == ["a", "b", "c"]
    with pytest.raises(TypeError):
        myobj.x = 10
    with pytest.raises(ValueError):
        myobj.x = ["a", "b", "c", "d"]

def test_attr_validator_example_2() -> None:
    class MyClass:
        @Attr.validator(readonly=True)
        def x(self, value: Union[int, str]) -> bool:
            ''' Validator function for readonly attribute 'C.x'. '''
            if isinstance(value, int):
                return value > 0
            return len(value) > 0

        @Attr.validator(backed_by='_w')
        def w(self, value: Sequence[int]) -> bool:
            ''' Validator function for mutable attribute 'C.w'. '''
            return len(value) in range(3)

        __slots__ = ("__x", "_w")
        #    default ^^^^^  ^^^^ custom
        #        backing attributes

    myobj = MyClass()
    myobj.x = "hello"
    assert myobj.x == "hello"
    assert hasattr(myobj, "_MyClass__x")
    assert getattr(myobj, "_MyClass__x") == "hello"
    with pytest.raises(AttributeError):
        myobj.x = "hello"
    with pytest.raises(AttributeError):
        myobj.x = 1.5
    with pytest.raises(AttributeError):
        myobj.x = ""
