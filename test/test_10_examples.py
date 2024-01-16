# pylint: disable = missing-docstring

import sys
from typed_descriptors import Attr

def test_getting_started_example() -> None:
    # pylint: disable = import-outside-toplevel
    if sys.version_info[1] >= 9:

        from collections.abc import Sequence

        class MyClass:

            x = Attr(int, lambda _, x: x >= 0, readonly=True)
            y = Attr(Sequence[int], lambda self, y: len(y) <= self.x)

            def __init__(self, x: int, y: Sequence[int]):
                self.x = x
                self.y = y

        myobj = MyClass(3, [0, 2, 5]) # OK
        myobj.y = (0, 1)              # OK
        try:
            myobj.y = [0, 2, 4, 6]
            assert False, "Expected ValueError"
        except ValueError:
            pass
        try:
            myobj.x = 5
            assert False, "Expected AttributeError"
        except AttributeError:
            pass
        try:
            myobj.y = 5
            assert False, "Expected TypeError"
        except TypeError:
            pass
        try:
            myobj.y = ["hi", "bye"]
            assert False, "Expected TypeError"
        except TypeError:
            pass
