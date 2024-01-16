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
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
    final,
    overload,
)
from typing_validation import can_validate

if sys.version_info[1] >= 12:
    from typing import Self
else:
    from typing_extensions import Self


T = TypeVar("T")
""" Invariant type variable for generic values. """


class DescriptorBase(Generic[T]):
    """
    Base class for descriptors backed by a protected or private attribute:

    - if the optional kwarg ``attr_name`` is specified in the constructor,
      the descriptor uses an attribute with that given name
    - otherwise, the descriptor uses a private attribute obtained from the
      descriptor name by prepending one or two underscores (depending on
      whether the descriptor name itself starts with underscore or not, resp.).

    If the attribute name starts with two underscores but does not end with
    two underscores, name-mangling is automatically performed.
    If the descriptor owner defines ``__slots__`` and ``'__dict__'`` is not
    listed in its ``__slots__``, then the backing attribute name must appear
    in the ``__slots__``.
    """

    __name: str
    __attr_name: str
    __given_attr_name: Optional[str]
    __owner: Type[Any]
    __type: Union[Type[T], Any]

    __slots__ = (
        "__name",
        "__attr_name",
        "__given_attr_name",
        "__owner",
        "__type",
    )

    @overload
    def __init__(
        self,
        ty: Type[T],
        /,
        *,
        attr_name: Optional[str] = None,
        lax: Literal[False] = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self, ty: Any, /, *, attr_name: Optional[str] = None, lax: Literal[True]
    ) -> None:
        ...

    def __init__(
        self,
        ty: Type[T],
        /,
        *,
        attr_name: Optional[str] = None,
        lax: bool = False,
    ) -> None:
        """
        Creates a new descriptor with the given type and optional validator.

        :param ty: the type of the descriptor
        :param attr_name: the name of the backing attribute for the
                          descriptor, or :obj:`None` to use a default name
        :param lax: if set to :obj:`True`, suppresses static typechecking
                    of the ``ty`` argument, allowing more general types to
                    be specified for runtime typechecks.

        :raises TypeError: if the type is not a valid type

        .. note ::

            If ``lax=True`` is set, the static typechecker can no longer
            infer ``T`` from the ``ty`` argument and a static type for the
            descriptor will have to be set by hand.

        :meta public:
        """
        if not can_validate(ty):
            raise TypeError(f"Cannot validate type {ty!r}.")
        self.__type = ty
        self.__given_attr_name = attr_name

    @final
    @property
    def name(self) -> str:
        """
        The name of the attribute.
        """
        return self.__name

    @final
    @property
    def type(self) -> Union[Type[T], Any]:
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
    @property
    def given_attr_name(self) -> Optional[str]:
        """
        The name of the backing attribute for the descriptor
        as specified in the descriptor constructor, or :obj:`None`
        if the backing attribute name is to be computed from the
        descriptor name.

        """
        return self.__given_attr_name

    @final
    @property
    def attr_name(self) -> str:
        """
        The name of the backing attribute for the descriptor,
        which can be accessed via ``getatttr(intance, attr_name)``.

        If the backing attribute is private, name-mangling has been applied.
        """
        return self.__attr_name

    @final
    def __set_name__(self, owner: Type[Any], name: str) -> None:
        """
        Hook called when the descriptor is assigned to a class attribute.
        Sets the name for the descriptor.
        """
        name_mangling_prefix = f"_{owner.__name__}"
        # 1. If 'name' has been mangled, remove the mangling prefix:
        if name.startswith(name_mangling_prefix):
            name = name[len(name_mangling_prefix) :]
        # 2. Get the backing attribute name (not yet name-mangled):
        given_attr_name = self.__given_attr_name
        if given_attr_name is None:
            attr_name_prefix = "_" if name.startswith("_") else "__"
            given_attr_name = f"{attr_name_prefix}{name}"
        elif given_attr_name == name:
            raise ValueError(
                f"Name of backing attribute for descriptor {self.name!r} "
                "cannot be the same as the descriptor name."
            )
        # 3. Name-mangle the backing attribute name, if private and not dunder:
        if given_attr_name.startswith("__") and not given_attr_name.endswith(
            "__"
        ):
            attr_name = f"{name_mangling_prefix}{given_attr_name}"
        else:
            attr_name = given_attr_name
        # 4. If slots are used without __dict__, ensure attr_name in slots:
        if hasattr(owner, "__slots__") and "__dict__" not in owner.__slots__:
            if given_attr_name not in owner.__slots__:
                attr_qual = (
                    "Private"
                    if given_attr_name.startswith("__")
                    else "Protected"
                )
                raise AttributeError(
                    f"{attr_qual} attribute {given_attr_name!r} must be "
                    f"defined in __slots__. Found {owner.__slots__ = }"
                )
        # 5. Set owner, name (not name-mangled) and attr_name (name-mangled):
        self.__owner = owner
        self.__name = name
        self.__attr_name = attr_name

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
