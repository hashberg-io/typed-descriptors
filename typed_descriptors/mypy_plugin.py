"""
A Mypy plugin to enhance static type inference of descriptors from
the :mod`typed_descriptors` library.
"""

from __future__ import annotations
from collections.abc import Callable
import typing
from mypy.plugin import FunctionContext, Plugin
from mypy.types import CallableType, Instance, get_proper_type, Type

def typed_descriptor_hook(ctx: FunctionContext) -> Type:
    """
    Extracts the descriptor type and assigns it to the generic type parameter,
    presuming that the generic type parameter appears at index 0.
    """
    assert ctx.arg_types and ctx.arg_types[0]
    _descriptor_t = get_proper_type(ctx.arg_types[0][0])
    ret_t = get_proper_type(ctx.default_return_type)
    if isinstance(_descriptor_t, CallableType):
        descriptor_t = _descriptor_t.ret_type
        if isinstance(ret_t, Instance):
            args = list(ret_t.args)
            args[0] = descriptor_t
            return ret_t.copy_modified(args=tuple(args))
        return ret_t
    return ret_t

_function_hooks = {
    "typed_descriptors.attr.Attr": typed_descriptor_hook,
    "typed_descriptors.prop.Prop": typed_descriptor_hook,
}

class TypedDescriptorsPlugin(Plugin):
    """
    Mypy plugin which expands type inference for typed descriptor,
    in the absence of TypeForm.
    """

    def get_function_hook(
        self, fullname: str
    ) -> Callable[[FunctionContext], Type] | None:
        hook = _function_hooks.get(fullname)
        if hook is not None:
            return hook
        return super().get_function_hook(fullname)

def plugin(version: str) -> typing.Type[TypedDescriptorsPlugin]:
    """
    Entry point for the Mypy plugin.
    """
    # ignore version argument if the plugin works with all mypy versions.
    return TypedDescriptorsPlugin
