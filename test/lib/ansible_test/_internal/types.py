"""Import wrapper for type hints when available."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from typing import (
        Any,
        AnyStr,
        Callable,
        Dict,
        FrozenSet,
        Iterable,
        List,
        Optional,
        Set,
        Text,
        Tuple,
        Type,
        TypeVar,
        Union,
    )
except ImportError:
    pass
