"""Import wrapper for type hints when available."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

TYPE_CHECKING = False

try:
    from typing import (
        Any,
        AnyStr,
        BinaryIO,
        Callable,
        Dict,
        FrozenSet,
        Generator,
        IO,
        Iterable,
        Iterator,
        List,
        Optional,
        Pattern,
        Set,
        Text,
        TextIO,
        Tuple,
        Type,
        TYPE_CHECKING,
        TypeVar,
        Union,
    )
except ImportError:
    pass
