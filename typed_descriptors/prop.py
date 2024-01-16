"""
    Descriptor class for cached properties.
"""

# Copyright (C) 2023 Hashberg Ltd

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

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


class Prop(DescriptorBase[T]):
    """
    A descriptor class for cached properties, supporting:

    - static type checking for the property value
    - lazy caching (value only cached at first read)

    See :class:`DescriptorBase` for details on how the property value is
    cached in each instance.
    """

    __value_fun: ValueFunction[T]

    __slots__ = ("__value_fun",)

    @overload
    def __init__(
        self,
        ty: Type[T],
        /,
        value: ValueFunction[T],
        *,
        attr_name: Optional[str] = None,
        lax: Literal[False] = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        ty: Any,
        /,
        value: ValueFunction[T],
        *,
        attr_name: Optional[str] = None,
        lax: Literal[True],
    ) -> None:
        ...

    def __init__(
        self,
        ty: Type[T],
        /,
        value: ValueFunction[T],
        *,
        attr_name: Optional[str] = None,
        lax: bool = False,
    ) -> None:
        """
        Creates a new property with the given type and value function.

        :param ty: the type of the property
        :param value: function computing the property value
        :param attr_name: the name of the backing attribute for the property
                          cache, or :obj:`None` to use a default name
        :param lax: if set to :obj:`True`, suppresses static typechecking
                    of the ``ty`` argument, allowing more general types to
                    be specified for runtime typechecks.

        :raises TypeError: if the type is not a valid type
        :raises TypeError: if the value function is not callable

        .. note ::

            If ``lax=True`` is set, the static typechecker can no longer
            infer ``T`` from the ``ty`` argument. It will infer ``T`` from
            the ``validator`` argument, if it is given and it is statically
            typed; otherwise, a static type for the descriptor will have to
            be set by hand.

        :meta public:
        """
        super().__init__(ty, attr_name=attr_name)
        if value is not None and not callable(value):
            raise TypeError(f"Expected callable 'value', got {value!r}.")
        self.__value_fun = value

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
        return hasattr(instance, self.attr_name)

    @final
    def cache_on(self, instance: Any) -> None:
        """
        Caches the property value on the given instance.
        Can be used to force property computation at a desired time,
        overriding the default lazy behaviour.

        :raises AttributeError: if the property is already cached.
        """
        validate(instance, self.owner)
        if hasattr(instance, self.attr_name):
            raise AttributeError(f"Property {self} is already cached.")
        value = self.value_fun(instance)
        validate(value, self.type)
        setattr(instance, self.attr_name, value)

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
        the property on the given instance.

        If the descriptor is accessed on the owner class, i.e. if
        ``instance`` is :obj:`None`, returns the :class:`Prop` object.

        :meta public:
        """
        if instance is None:
            return self
        try:
            return cast(T, getattr(instance, self.attr_name))
        except AttributeError:
            value = self.value_fun(instance)
            validate(value, self.type)
            setattr(instance, self.attr_name, value)
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
        if not hasattr(instance, self.attr_name):
            raise AttributeError(f"Property {self} is not cached.")
        delattr(instance, self.attr_name)

    def __str__(self) -> str:
        """
        Representation of this property, inclusive of the following info:

        - the :attr:`owner` name
        - the property :attr:`name`

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
        Representation of this property, inclusive of the following info:

        - the :class:`Prop` subclass
        - the :attr:`owner` name
        - the property :attr:`name`
        - the property :attr:`type`

        An example:

        .. code-block ::

            <Prop Color.rgb: tuple[int, int, int]>

        """
        descr_cls = type(self).__name__
        owner = self.owner.__name__
        name = self.attr_name
        ty = (
            self.type.__name__
            if isinstance(self.type, type)
            else str(self.type)
        )
        return f"<{descr_cls} {owner}.{name}: {ty}>"
