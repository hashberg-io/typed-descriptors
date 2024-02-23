"""
    Descriptor class for cached properties.
"""

# Part of typed-descriptors
# Copyright (C) 2023 Hashberg Ltd

from __future__ import annotations
from inspect import signature
import sys
from typing import (
    Any,
    Optional,
    Protocol,
    Type,
    TypeVar,
    final,
    get_type_hints,
    overload,
)
from typing_extensions import Self
from typing_validation import validate
from .base import DescriptorBase, T


_T = TypeVar("_T")
""" Invariant type variable for generic values, privately used. """

T_co = TypeVar("T_co", covariant=True)
""" Covariant type variable for generic values. """


class ValueFunction(Protocol[T_co]):
    """
    Structural type for the value function of a :class:`Prop`.
    """

    def __call__(self, instance: Any, /) -> T_co:
        """
        Computes and returns the value for a :class:`Prop`,
        in the context of the given instance.
        """
        ...


def validate_value_fun(value_fun: ValueFunction[T], /) -> None:
    """
    Runtime validation for value functions.

    :raises TypeError: if the argument is not a value function
    :raises ValueError: if the function doesn't have an explicit annotation
                        for its return type.
    """
    if not callable(value_fun):
        raise TypeError("Value function must be callable.")
    if len(signature(value_fun).parameters) != 1:
        raise TypeError("Value function must take exactly one argument.")


def value_fun_return_type(value_fun: ValueFunction[T], /) -> Any:
    """
    Returns the return type annotation of a value function.
    Used by :func:`Prop` to infer the property type from the value function
    return type annotation.

    :raises TypeError: if the argument is not a value function
    :raises ValueError: if the function doesn't have an explicit annotation
                        for its return type.
    """
    validate_value_fun(value_fun)
    value_fun_types = get_type_hints(value_fun)
    if "return" not in value_fun_types:
        raise ValueError(
            "Value function must explicitly annotate its return type."
        )
    return value_fun_types["return"]


class PropFactory(Protocol):
    """
    Structural type for functions which create :class:`Prop` instances
    from value functions.
    """

    def __call__(self, value_fun: ValueFunction[T], /) -> Prop[T]:
        """
        Returns a validated :class:`Prop` from a value function.
        """
        ...


class Prop(DescriptorBase[T]):
    """
    A descriptor class for cached properties, supporting:

    - static type checking for the property value
    - lazy caching (value only cached at first read)

    See :class:`~typed_descriptors.base.DescriptorBase` for details on how the property value is
    cached in each instance.
    """

    @staticmethod
    @overload
    def value(
        value_fun: ValueFunction[T], /, *, backed_by: Optional[str] = None
    ) -> Prop[T]: ...

    @staticmethod
    @overload
    def value(
        value_fun: None = None, /, *, backed_by: Optional[str] = None
    ) -> PropFactory: ...

    @staticmethod
    def value(
        value_fun: Optional[ValueFunction[T]] = None,
        /,
        *,
        backed_by: Optional[str] = None,
    ) -> PropFactory | Prop[T]:
        """
        An alias for :func:`cached_property`.

        It offers a way to declare :class:`Prop` which is stylisticallly
        aligned to the :meth:`Attr.validator<typed_descriptors.attr.Attr.validator>`
        decorator for attributes.
        """
        return cached_property(value_fun, backed_by=backed_by)

    __value_fun: ValueFunction[T]

    @overload
    def __init__(
        self,
        type: Type[T],
        value: ValueFunction[T],
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
        value: ValueFunction[T],
        /,
        *,
        backed_by: Optional[str] = None,
    ) -> None:
        # pylint: disable = redefined-builtin
        ...

    def __init__(
        self,
        type: Type[T] | Any,
        value: ValueFunction[T],
        /,
        *,
        backed_by: Optional[str] = None,
    ) -> None:
        """
        Creates a new property with the given type and value function.

        :param value: function computing the property value
        :param type: the type of the property
        :param attr_name: the name of the backing attribute for the property
                          cache, or :obj:`None` to use a default name

        :raises TypeError: if the type is not a valid type
        :raises TypeError: if the value function is not callable

        :meta public:
        """
        # pylint: disable = redefined-builtin
        validate_value_fun(value)
        super().__init__(type, backed_by=backed_by)
        if not callable(value):
            raise TypeError(f"Expected callable 'value', got {value!r}.")
        self.__value_fun = value
        self.__doc__ = value.__doc__

    @final
    @property
    def value_fun(self) -> ValueFunction[T]:
        """
        The function called to produce a value for this property on a given
        instance.
        It is called by the getter when the property doesn't have a cached
        value, and the value returned is automatically cached.
        """
        return self.__value_fun

    @final
    def is_cached_on(self, instance: Any) -> bool:
        """
        Whether the property is cached on the given instance.
        """
        validate(instance, self.owner)
        return self._is_set_on(instance)

    @final
    def cache_on(self, instance: Any) -> None:
        """
        Caches the property value on the given instance.
        Can be used to force property computation at a desired time,
        overriding the default lazy behaviour.

        :raises AttributeError: if the property is already cached.
        """
        validate(instance, self.owner)
        if self._is_set_on(instance):
            raise AttributeError(f"Property {self} is already cached.")
        value = self.value_fun(instance)
        validate(value, self.type)
        self._set_on(instance, value)

    @overload
    def __get__(self, instance: None, _: Type[Any]) -> Self: ...

    @overload
    def __get__(self, instance: Any, _: Type[Any]) -> T: ...

    @final
    def __get__(self, instance: Any, _: Type[Any]) -> T | Self:
        """
        If the descriptor is accessed on an instance, returns the value of
        the property on the given instance.

        If the descriptor is accessed on the owner class, i.e. if
        ``instance`` is :obj:`None`, returns the :class:`Prop` object.

        :meta public:
        """
        if instance is None:
            return self
        try:
            return self._get_on(instance)
        except AttributeError:
            value = self.value_fun(instance)
            validate(value, self.type)
            self._set_on(instance, value)
            return value

    __set__ = None
    """
        Property values cannot be set.

        :meta public:
    """

    @final
    def __delete__(self, instance: Any) -> None:
        """
        Deletes the property cache on the given instance.

        :raises AttributeError: if the property is not cached,
                                see :meth:`is_cached_on`.

        :meta public:
        """
        if not self._is_set_on(instance):
            raise AttributeError(f"Property {self} is not cached.")
        self._del_on(instance)

    def __str__(self) -> str:
        """
        Representation of this property, inclusive of the following info:

        - the :attr:`owner` name
        - the property :attr:`name`

        An example:

        .. code-block ::

            Color.hue
        """
        owner_name = self.owner.__name__
        name = self.name
        return f"{owner_name}.{name}"

    def __repr__(self) -> str:
        """
        Representation of this property, inclusive of the following info:

        - the :attr:`owner` name
        - the property :attr:`name`
        - the property :attr:`type`

        An example:

        .. code-block ::

            <Prop Color.rgb: tuple[int, int, int]>

        """
        owner = self.owner.__name__
        name = self.name
        ty = (
            self.type.__name__
            if isinstance(self.type, type)
            else str(self.type)
        )
        return f"<Prop {owner}.{name}: {ty}>"


@overload
def cached_property(
    value_fun: ValueFunction[T], /, *, backed_by: Optional[str] = None
) -> Prop[T]: ...


@overload
def cached_property(
    value_fun: None = None, /, *, backed_by: Optional[str] = None
) -> PropFactory: ...


def cached_property(
    value_fun: Optional[ValueFunction[T]] = None,
    /,
    *,
    backed_by: Optional[str] = None,
) -> PropFactory | Prop[T]:
    """
    Decorator used to create a cached property from a value function,
    optionally specifying a backing attribute.
    See :class:`Prop` and :class:`DescriptorBase` for more information.

    It can be used directly, for properties with default backing attribute name:

    .. code-block ::

        class C:

            @cached_property
            def x(self) -> Sequence[str]:
                ''' Value function for property 'C.x'. '''
                return 10

    It can be used by supplying a custom backing attribute name to the
    ``backed_by`` argument:

    .. code-block ::

        class C:

            @cached_property(backed_by="_x")
            def x(self) -> Sequence[str]:
                ''' Value function for property 'C.x'. '''
                return 10

            __slots__ = ("_x", )

    .. note ::

        The decorator is analogous to the built-in :func:`functools.cached_property`,
        from which it takes its name, and it uses the same caching logic when
        ``__dict__`` is available on owner class's instances and no custom
        attribute name is used.
        Contrary to its built-in counterpart, however, this decorator can be
        used with a slotted attribute as backing attribute.

    """
    if value_fun is not None:
        prop_type = value_fun_return_type(value_fun)
        return Prop(prop_type, value_fun, backed_by=backed_by)

    def _cached_property(value_fun: ValueFunction[_T]) -> Prop[_T]:
        return cached_property(value_fun, backed_by=backed_by)

    return _cached_property
