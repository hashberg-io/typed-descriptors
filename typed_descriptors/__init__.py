"""
    Descriptor classes with static and runtime validation features.
"""

# typed-descriptors: Descriptor classes for typed attributes and properties.
# Copyright (C) 2023 Hashberg Ltd

from __future__ import annotations
from .attr import Attr
from .prop import Prop, cached_property

__version__ = "1.2.0"

__all__ = ("Attr", "Prop", "cached_property")
