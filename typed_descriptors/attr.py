"""
    Descriptor class for attributes.
"""

# Part of typed-descriptors
# Copyright (C) 2023 Hashberg Ltd

from __future__ import annotations
from inspect import signature
from typing import (
    Any,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    final,
    get_type_hints,
    overload,
)
from typing_extensions import Self
from typing_validation import validate
from .base import DescriptorBase, T


_T = TypeVar("_T")
""" Invariant type variable for generic values, privately used. """

T_contra = TypeVar("T_contra", contravariant=True)
""" Contravariant type variable for generic values. """


class SupportsBool(Protocol):
    """
    Structural types for things which can be converted to :obj:`bool`.
    """

    def __bool__(self) -> bool: ...


class ValidatorFunction(Protocol[T_contra]):
    """
    Structural type for the validator function of a :class:`Attr`.
    """

    def __call__(
        self, instance: Any, value: T_contra, /
    ) -> Union[SupportsBool, None]:
        """
        Validates the given value for assignment to a :class:`Attr`,
        in the context of the given instance.

        Called passing the current ``instance`` and the ``value`` that is
        to be assigned to the descriptor.
        At the time when the validator function for a descriptor is invoked,
        the given ``value`` has already passed its runtime typecheck.
        Validator functions can use ``instance`` to perform validation
        involving other descriptors for the same class.

        There are two ways in which a validator function can trigger an error
        as part of the validation logic for an :class:`Attr`:

        - By returning :obj:`False`: a :obj:`ValueError` will be raised.
        - By raising any exception as part of its body: the exception is
          caught as part of a `try...except` block, and a :obj:`ValueError`
          is raised from it (preserving the original error information).

        In the second case, the validator should return :obj:`True` at the
        end, to signal that validation was successful.

        """
        ...


def validate_validator_fun(validator_fun: ValidatorFunction[T], /) -> None:
    """
    Runtime validation for validator functions.

    :raises TypeError: if the argument is not a validator function
    """
    if not callable(validator_fun):
        raise TypeError("Validator function must be callable.")
    if len(signature(validator_fun).parameters) != 2:
        raise TypeError("Validator function must take exactly two arguments.")


def validator_fun_value_type(validator_fun: ValidatorFunction[T], /) -> Any:
    """
    Returns the type annotation for the ``value`` argument of a validator
    function. Used by :meth:`Attr.validator` to infer the :class:`Attr`
    type from the validator function type hints.

    :raises TypeError: if the argument is not a validator function
    :raises ValueError: if the function doesn't have an explicit annotation
                        for its ``value`` argument type or its return type.
    """
    validate_validator_fun(validator_fun)
    validator_fun_types = get_type_hints(validator_fun)
    validator_fun_sig = signature(validator_fun)
    validator_fun_params = tuple(validator_fun_sig.parameters.keys())
    value_argname = validator_fun_params[1]
    if value_argname not in validator_fun_types:
        raise ValueError(
            "Validator function must explicitly annotate the type for its "
            f"second argument {value_argname!r}."
        )
    return validator_fun_types[value_argname]


class ValidatedAttrFactory(Protocol):
    """
    Structural type for functions which create :class:`Attr` instances
    from validator functions.
    """

    def __call__(self, validator_fun: ValidatorFunction[T], /) -> Attr[T]:
        """
        Returns a validated :class:`Attr` from a validator function.
        """
        ...


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

    @staticmethod
    @overload
    def validator(
        validator_fun: ValidatorFunction[T],
        /,
        *,
        readonly: bool = False,
        backed_by: Optional[str] = None,
    ) -> Attr[T]: ...

    @staticmethod
    @overload
    def validator(
        validator_fun: None = None,
        /,
        *,
        readonly: bool = False,
        backed_by: Optional[str] = None,
    ) -> ValidatedAttrFactory: ...

    @staticmethod
    def validator(
        validator_fun: Optional[ValidatorFunction[T]] = None,
        /,
        *,
        readonly: bool = False,
        backed_by: Optional[str] = None,
    ) -> ValidatedAttrFactory | Attr[T]:
        """
        Decorator used to create an :class:`Attr` from a validator function,
        optionally specifying a readonly modifier and a backing attribute.

        It can be used directly, for mutable attributes with default backing
        attribute name:

            .. code-block ::

                class MyClass:

                    @Attr.validator
                    def x(self, value: Sequence[str]) -> bool:
                        ''' Validator function for attribute 'C.x'. '''
                        return 1 <= len(value) <= 3

        It can be used by supplying ``readonly`` and ``backed_by`` values,
        for more general attributes:

            .. code-block ::

                class MyClass:

                    @Attr.validator(readonly=True)
                    def x(self, value: int|str) -> bool:
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

        """
        if validator_fun is not None:
            ty = validator_fun_value_type(validator_fun)
            return Attr(
                ty,
                validator=validator_fun,
                readonly=readonly,
                backed_by=backed_by,
            )

        def _validated_attr(validator_fun: ValidatorFunction[_T]) -> Attr[_T]:
            return Attr.validator(
                validator_fun, readonly=readonly, backed_by=backed_by
            )

        return _validated_attr

    __readonly: bool
    __validator_fun: Optional[ValidatorFunction[T]]

    @overload
    def __init__(
        self,
        type: Type[T],
        /,
        validator: Optional[ValidatorFunction[T]] = None,
        *,
        readonly: bool = False,
        backed_by: Optional[str] = None,
    ) -> None:
        # pylint: disable = redefined-builtin
        ...

    @overload
    def __init__(
        self,
        type: Any,
        /,
        validator: Optional[ValidatorFunction[T]] = None,
        *,
        readonly: bool = False,
        backed_by: Optional[str] = None,
    ) -> None:
        # pylint: disable = redefined-builtin
        ...

    def __init__(
        self,
        type: Type[T] | Any,
        /,
        validator: Optional[ValidatorFunction[T]] = None,
        *,
        readonly: bool = False,
        backed_by: Optional[str] = None,
    ) -> None:
        """
        Creates a new attribute with the given type and optional validator.

        :param ty: the type of the attribute
        :param validator: an optional validator function for the attribute
        :param readonly: whether the attribute is read-only
        :param backed_by: the name of the backing attribute for the
                          attribute, or :obj:`None` to use a default name

        :raises TypeError: if the type is not a valid type
        :raises TypeError: if the validator is not callable

        :meta public:
        """
        # pylint: disable = redefined-builtin
        super().__init__(type, backed_by=backed_by)
        if validator is not None:
            validate_validator_fun(validator)
            self.__doc__ = validator.__doc__
        self.__validator_fun = validator
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
    def validator_fun(self) -> Optional[ValidatorFunction[T]]:
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
        return self.__validator_fun

    @final
    def is_defined_on(self, instance: Any) -> bool:
        """
        Wether the attribute is defined on the given instance.
        """
        validate(instance, self.owner)
        return self._is_set_on(instance)

    @overload
    def __get__(self, instance: None, _: Type[Any]) -> Self: ...

    @overload
    def __get__(self, instance: Any, _: Type[Any]) -> T: ...

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
            return self._get_on(instance)
            # return cast(T, getattr(instance, self.attr_name))
        except AttributeError:
            raise AttributeError(f"Attribute {self} is not set.") from None

    @final
    def __set__(self, instance: Any, value: T) -> None:
        """
        Sets the value of the descriptor on the given instance.

        :raises AttributeError: if the attribute is readonly and it already
                                has a value assigned to it
        :raises TypeError: if the value has the wrong type
        :raises ValueError: if a custom validator is specified and the
                            value is invalid

        :meta public:
        """
        if self.readonly:
            if self._is_set_on(instance):
                raise AttributeError(
                    f"Attribute {self} is readonly: it can only be set once."
                )
        validate(value, self.type)
        validator = self.__validator_fun
        if validator is not None:
            try:
                res = validator(instance, value)
                if res is not None and not res:
                    raise ValueError(
                        f"Invalid value for attribute {self}: {value!r}"
                    )
            except ValueError as e:
                raise ValueError(
                    f"Invalid value for attribute {self}: {value!r}"
                ) from e
        self._set_on(instance, value)

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
        if not self._is_set_on(instance):
            raise AttributeError(f"Attribute {self} is not set.")
        self._del_on(instance)

    def __str__(self) -> str:
        """
        Representation of this attribute, inclusive of the following info:

        - the :attr:`owner` name
        - the attribute :attr:`name`

        An example:

        .. code-block ::

            Color.hue
        """
        owner_name = self.owner.__name__
        name = self.name
        return f"{owner_name}.{name}"

    def __repr__(self) -> str:
        """
        Representation of this attribute, inclusive of the following info:

        - the :attr:`owner` name
        - the attribute :attr:`name`
        - the attribute :attr:`type`
        - optional ``readonly`` qualifier

        Two examples:

        .. code-block ::

            <Attr Color.hue: str>
            <readonly Attr Color.saturation: int>

        """
        owner = self.owner.__name__
        name = self.name
        ty = (
            self.type.__name__
            if isinstance(self.type, type)
            else str(self.type)
        )
        qualifier = "readonly " if self.readonly else ""
        return f"<{qualifier}Attr {owner}.{name}: {ty}>"
