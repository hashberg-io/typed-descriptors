"""
    Abstract base class for descriptors backed by protected/private attributes.
"""

# Part of typed-descriptors
# Copyright (C) 2023 Hashberg Ltd

from __future__ import annotations
from abc import abstractmethod
import sys
from typing import (
    Any,
    Generic,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    final,
    overload,
)
from typing_validation import can_validate, validate

if sys.version_info[1] >= 12:
    from typing import Self
else:
    from typing_extensions import Self


def name_mangle(owner: type, attr_name: str) -> str:
    """
    If the given attribute name is private and not dunder,
    return its name-mangled version for the given owner class.
    """
    if not attr_name.startswith("__"):
        return attr_name
    if attr_name.endswith("__"):
        return attr_name
    return f"_{owner.__name__}{attr_name}"


def name_unmangle(owner: type, attr_name: str) -> str:
    """
    If the given attribute name is name-mangled for the given owner class,
    removes the name-mangling prefix.
    """
    name_mangling_prefix = f"_{owner.__name__}"
    if attr_name.startswith(name_mangling_prefix + "__"):
        return attr_name[len(name_mangling_prefix) :]
    return attr_name


T = TypeVar("T")
""" Invariant type variable for generic values. """


class DescriptorBase(Generic[T]):
    """
    Base class for descriptors backed by an attribute whose name and access mode
    is determined by the following logic.

    Naming logic for backing attribute:

    1. If the ``backed_by`` argument is specified in the constructor, the string
       passed to it is used as name for the backing attribute.
    2. Else, if either the owner class has no ``__slots__`` or ``__dict__``
       is included in its ``__slots__``, the backing attribute name coincides
       with the descriptor name.
    3. Else, the backing attribute name is obtained by prepending one or
       two underscores to the descriptor name (one if the descriptor name starts
       with underscore, two if it doesn't).

    Access logic for backing attribute:

    1. If the owner class has no ``__slots__``, the backing attribute is
       accessed via ``__dict__`` if its name coincides with the descriptor name,
       and via ``___attr`` functions otherwise.
    2. Else, if the the ``backed_by`` argument is specified in the constructor
       and it appears in the owner class's ``__slots__``, the backing attribute
       is accessed via ``___attr`` functions.
    3. Else, if ``__dict__`` appears in the owner class's ``__slots__``, the
       backing attribute is accessed via ``__dict__`` if its name coincides with
       the descriptor name, and via ``___attr`` functions otherwise.
    4. Else, the backing attribute is accessed via ``___attr`` functions.

    Above, the nomenclature "``___attr`` functions" refers to :func:`getattr`,
    :func:`setattr`, :func:`delattr` and :func:`hasattr`.

    If the backing attribute name starts with two underscores but does not end
    with two underscores, name-mangling is automatically performed.

    If the owner class has ``__slots__`` and ``__dict__`` is not included in its
    ``__slots__``, a :obj:`TypeError` is raised at the time when the descriptor
    is assigned if the backing attribute name does not appear in ``__slots__``.
    """

    # Attributes set by constructor:
    __type: Union[Type[T], Any]

    # Attributes set by __set_name__:
    __name: str
    __owner: Type[Any]
    __backed_by: str
    __use_dict: bool

    # Attribute set by constructor and deleted by __set_name__:
    __temp_backed_by: Optional[str]

    __slots__ = (
        "__type",
        "__name",
        "__owner",
        "__backed_by",
        "__use_dict",
        "__temp_backed_by",
    )

    @overload
    def __init__(
        self,
        type: Type[T],
        /,
        *,
        backed_by: Optional[str] = None,
    ) -> None:
        # pylint: disable = redefined-builtin
        ...

    @overload
    def __init__(
        self,
        type: Any,
        /,
        *,
        backed_by: Optional[str] = None,
    ) -> None:
        # pylint: disable = redefined-builtin
        ...

    def __init__(
        self,
        type: Type[T] | Any,  # will be TypeForm[T] one day
        /,
        *,
        backed_by: Optional[str] = None,
    ) -> None:
        """
        Creates a new descriptor with the given type and optional validator.

        :param type: the type of the descriptor.
        :param backed_by: the name of the backing attribute for the
                          descriptor, or :obj:`None` to use a default name.

        :raises TypeError: if the type cannot be validated by the
                           :mod:`typing_validation` library.

        :meta public:
        """
        # pylint: disable = redefined-builtin
        if not can_validate(type):
            raise TypeError(f"Cannot validate type {type!r}.")
        validate(backed_by, Optional[str])
        self.__type = type
        self.__temp_backed_by = backed_by

    @final
    @property
    def name(self) -> str:
        """
        The name of the attribute.
        """
        return self.__name

    @final
    @property
    def type(self) -> Union[Type[T], Any]:  # will be TypeForm[T] one day
        """
        The type of the attribute.
        """
        return self.__type

    @final
    @property
    def owner(self) -> Type[Any]:
        """
        The class that owns the attribute.
        """
        return self.__owner

    @final
    def _get_on(self, instance: Any) -> T:
        """
        Gets the value of the backing attribute on the given instance.
        """
        if self.__use_dict:
            try:
                return cast(T, instance.__dict__[self.__backed_by])
            except KeyError:
                raise AttributeError(
                    f"{self.__owner.__name__!r} object has no "
                    f"attribute {self.__backed_by!r}."
                ) from None
        return cast(T, getattr(instance, self.__backed_by))

    @final
    def _set_on(self, instance: Any, value: T) -> None:
        """
        Sets the value of the backing attribute on the given instance.
        """
        if self.__use_dict:
            instance.__dict__[self.__backed_by] = value
        else:
            setattr(instance, self.__backed_by, value)

    @final
    def _del_on(self, instance: Any) -> None:
        """
        Deletes the value of the backing attribute on the given instance.
        """
        if self.__use_dict:
            try:
                del instance.__dict__[self.__backed_by]
            except KeyError:
                raise AttributeError(
                    f"{self.__owner.__name__!r} object has no "
                    f"attribute {self.__backed_by!r}."
                ) from None
        else:
            delattr(instance, self.__backed_by)

    @final
    def _is_set_on(self, instance: Any) -> bool:
        """
        Checkes whether the value of the backing attribute is set on the
        given instance.
        """
        if self.__use_dict:
            return self.__backed_by in instance.__dict__
        return hasattr(instance, self.__backed_by)

    @final
    @property
    def is_assigned(self) -> bool:
        """
        Whether the descriptor has been assigned its owner and name.
        """
        return hasattr(self, "_DescriptorBase__owner")

    @final
    def __set_name__(self, owner: Type[Any], name: str) -> None:
        """
        Hook called when the descriptor is assigned to a class attribute.
        Responsible for:

        - Setting the owner and name of the descriptor
        - Setting the name of the backing attribute (incl. name-mangling)
        - Determining how to access the backing attribute.

        See :class:`DescriptorBase` class documentation for the logic behind
        the backing attribute's name and access mode.

        :raises TypeError: if the descriptor is assigned more than once
        :raises TypeError: if the owner class has ``__slots__`` and the
                           descriptor ``name`` appears in ``__slots__``
        :raises TypeError: if the owner class has ``__slots__``, ``__dict__`` is
                           not in ``__slots__``, and the backing attribute name
                           is not in ``__slots__``.

        :meta public:
        """
        # 1. Ensure descriptor is not assigned twice:
        if self.is_assigned:
            raise TypeError(
                "Cannot set owner/name for the same descriptor twice."
            )
        # 2. If descriptor name is mangled, unmangle it:
        name = name_unmangle(owner, name)
        # 3. Compute backing attribute name and whether to use __dict__:
        __slots__ = owner.__slots__ if hasattr(owner, "__slots__") else None
        temp_backed_by = self.__temp_backed_by
        if __slots__ is None:
            if temp_backed_by is None:
                temp_backed_by = name
            use_dict = temp_backed_by == name
        elif temp_backed_by in __slots__:
            assert temp_backed_by is not None
            use_dict = False
        elif "__dict__" in __slots__:
            if temp_backed_by is None:
                temp_backed_by = name
            use_dict = temp_backed_by == name
        else:  # __slots__ is used and __dict__ is not available
            use_dict = False
            if temp_backed_by is None:
                if name.startswith("_"):
                    temp_backed_by = f"_{name}"
                else:
                    temp_backed_by = f"__{name}"
            if temp_backed_by not in __slots__:
                raise TypeError(
                    "When __slots__ are used and __dict__ is not available, "
                    f"the name of the backing attribtue {temp_backed_by!r} "
                    "must appear in __slots__."
                )
        backed_by = name_mangle(owner, temp_backed_by)
        # 4. Set owner, name (not name-mangled) and backed_by (name-mangled):
        self.__owner = owner
        self.__name = name
        self.__backed_by = backed_by
        self.__use_dict = use_dict
        del self.__temp_backed_by

    @abstractmethod
    @overload
    def __get__(self, instance: None, _: Type[Any]) -> Self:
        ...

    @abstractmethod
    @overload
    def __get__(self, instance: Any, _: Type[Any]) -> T:
        ...

    @abstractmethod
    def __get__(self, instance: Any, _: Type[Any]) -> T | Self:
        """
        If the descriptor is accessed on an instance, returns the value of
        the descriptor on the given instance.

        If the descriptor is accessed on the owner class, i.e. if
        ``instance`` is :obj:`None`, returns the descriptor object.

        :meta public:
        """
