"""
    Descriptor class for attributes.
"""

# Part of typed-descriptors
# Copyright (C) 2023 Hashberg Ltd

from __future__ import annotations
import sys
from typing import (
    Any,
    Literal,
    Optional,
    Protocol,
    Type,
    TypeVar,
    cast,
    final,
    overload,
)
from typing_validation import validate
from .base import DescriptorBase, T

if sys.version_info[1] >= 12:
    from typing import Self
else:
    from typing_extensions import Self

T_contra = TypeVar("T_contra", contravariant=True)
""" Contravariant type variable for generic values. """


class ValidatorFunction(Protocol[T_contra]):
    """
    Structural type for the validator function of a :class:`Attr`.
    """

    def __call__(self, instance: Any, value: T_contra, /) -> bool:
        """
        Validates the given value for assignment to a :class:`Attr`,
        in the context of the given instance.

        Called passing the current ``instance`` and the ``value`` that is
        to be assigned to the descriptor.
        At the time when the validator function for a descriptor is invoked,
        the given ``value`` has already passed its runtime typecheck.
        Validator functions can use ``instance`` to perform validation
        involving other descriptors for the same class.
        """


class Attr(DescriptorBase[T]):
    """
    A descriptor class for attributes, supporting:

    - static type checking for the attribute value
    - runtime type checking of values assigned to the attribute
    - optional runtime validation of values assigned to the attribute
    - optional read-only restrictions on the attribute (set once)

    See :class:`DescriptorBase` for details on how the attribute value is
    stored in each instance.
    """

    __readonly: bool
    __validator: Optional[ValidatorFunction[T]]

    __slots__ = ("__readonly", "__validator")

    @overload
    def __init__(
        self,
        ty: Type[T],
        /,
        validator: Optional[ValidatorFunction[T]] = None,
        *,
        readonly: bool = False,
        attr_name: Optional[str] = None,
        lax: Literal[False] = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        ty: Any,
        /,
        validator: Optional[ValidatorFunction[T]] = None,
        *,
        readonly: bool = False,
        attr_name: Optional[str] = None,
        lax: Literal[True],
    ) -> None:
        ...

    def __init__(
        self,
        ty: Type[T],
        /,
        validator: Optional[ValidatorFunction[T]] = None,
        *,
        readonly: bool = False,
        attr_name: Optional[str] = None,
        lax: bool = False,
    ) -> None:
        """
        Creates a new attribute with the given type and optional validator.

        :param ty: the type of the attribute
        :param validator: an optional validator function for the attribute
        :param readonly: whether the attribute is read-only
        :param attr_name: the name of the backing attribute for the
                          attribute, or :obj:`None` to use a default name
        :param lax: if set to :obj:`True`, suppresses static typechecking
                    of the ``ty`` argument, allowing more general types to
                    be specified for runtime typechecks.

        :raises TypeError: if the type is not a valid type
        :raises TypeError: if the validator is not callable

        .. note ::

            If ``lax=True`` is set, the static typechecker can no longer
            infer ``T`` from the ``ty`` argument. It will infer ``T`` from
            the ``validator`` argument, if it is given and it is statically
            typed; otherwise, a static type for the descriptor will have to
            be set by hand.

        :meta public:
        """
        super().__init__(ty, attr_name=attr_name)
        if validator is not None and not callable(validator):
            raise TypeError(
                f"Expected callable 'validator', got {validator!r}."
            )
        self.__validator = validator
        self.__readonly = bool(readonly)

    @final
    @property
    def readonly(self) -> bool:
        """
        Whether the attribute is readonly.
        """
        return self.__readonly

    @final
    @property
    def validator(self) -> Optional[ValidatorFunction[T]]:
        """
        The custom validator function for the attribute,
        or :obj:`None` if no validator was specified.

        There are two ways in which the validator can trigger an error:

        - By returning :obj:`False`: a :obj:`ValueError` is raised
        - By raising any exception as part of its body: the exception is
          caught as part of a `try...except` block, and a :obj:`ValueError`
          is raised from it (preserving the original error information).

        In the second case, the validator should return :obj:`True` at the
        end, to signal that validation was successful.
        """
        return self.__validator

    @final
    def is_defined_on(self, instance: Any) -> bool:
        """
        Wether the attribute is defined on the given instance.
        """
        validate(instance, self.owner)
        return hasattr(instance, self.attr_name)

    @overload
    def __get__(self, instance: None, _: Type[Any]) -> Self:
        ...

    @overload
    def __get__(self, instance: Any, _: Type[Any]) -> T:
        ...

    @final
    def __get__(self, instance: Any, _: Type[Any]) -> T | Self:
        """
        If the descriptor is accessed on an instance, returns the value of
        the attribute on the given instance.

        If the descriptor is accessed on the owner class, i.e. if
        ``instance`` is :obj:`None`, returns the :class:`Attr` object.

        :raises AttributeError: if the attribute is not defined,
                                see :meth:`is_defined_on`.

        :meta public:
        """
        if instance is None:
            return self
        try:
            return cast(T, getattr(instance, self.attr_name))
        except AttributeError:
            raise AttributeError(f"Attribute {self} is not set.") from None

    @final
    def __set__(self, instance: Any, value: T) -> None:
        """
        Sets the value of the descriptor on the given instance.

        :raises TypeError: if the value has the wrong type
        :raises ValueError: if a custom validator is specified and the
                            value is invalid
        :raises AttributeError: if the attribute is readonly and it already
                                has a value assigned to it

        :meta public:
        """
        validate(value, self.type)
        validator = self.validator
        if validator is not None:
            try:
                res = validator(instance, value)
                if not res:
                    raise ValueError(
                        f"Invalid value for attribute {self}: {value!r}"
                    )
            except ValueError as e:
                raise ValueError(
                    f"Invalid value for attribute {self}: {value!r}"
                ) from e
        if self.readonly:
            if hasattr(instance, self.attr_name):
                raise AttributeError(
                    f"Attribute {self} is readonly: it can only be set once."
                )
        setattr(instance, self.attr_name, value)

    @final
    def __delete__(self, instance: Any) -> None:
        """
        Deletes the value of the descriptor on the given instance.

        :raises AttributeError: if the attribute is readonly
        :raises AttributeError: if the attribute is not defined,
                                see :meth:`is_defined_on`.

        :meta public:
        """
        if self.readonly:
            raise AttributeError(
                f"Attribute {self.name!r} is readonly: it cannot be deleted."
            )
        if not hasattr(instance, self.attr_name):
            raise AttributeError(f"Attribute {self} is not set.")
        delattr(instance, self.attr_name)

    def __str__(self) -> str:
        """
        Representation of this attribute, inclusive of the following info:

        - the :attr:`owner` name
        - the attribute :attr:`name`

        An example:

        .. code-block ::

            Color.hue
        """
        type_name = type(self).__name__
        owner_name = self.owner.__name__
        attr_name = self.attr_name
        return f"{type_name} {owner_name}.{attr_name}"

    def __repr__(self) -> str:
        """
        Representation of this attribute, inclusive of the following info:

        - the :class:`Attr` subclass
        - the :attr:`owner` name
        - the attribute :attr:`name`
        - the attribute :attr:`type`
        - optional ``readonly`` qualifier

        Two examples:

        .. code-block ::

            <Attr Color.hue: str>
            <readonly Attr Color.saturation: int>

        """
        descr_cls = type(self).__name__
        owner = self.owner.__name__
        name = self.attr_name
        ty = (
            self.type.__name__
            if isinstance(self.type, type)
            else str(self.type)
        )
        qualifier = "readonly " if self.readonly else ""
        return f"<{qualifier}{descr_cls} {owner}.{name}: {ty}>"
