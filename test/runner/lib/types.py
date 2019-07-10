"""Import wrapper for type hints when available."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from typing import (
        Any,
        Dict,
        FrozenSet,
        Iterable,
        List,
        Optional,
        Set,
        Tuple,
        Type,
        TypeVar,
    )
except ImportError:
    pass
