"""PyYAML compatibility."""
from __future__ import annotations

import typing as t

from functools import (
    partial,
)

try:
    import yaml as _yaml

    YAML_IMPORT_ERROR = None
except ImportError as ex:
    yaml_load = None  # pylint: disable=invalid-name
    YAML_IMPORT_ERROR = ex
else:
    try:
        _SafeLoader: t.Union[t.Type[_yaml.CSafeLoader], t.Type[_yaml.SafeLoader]] = _yaml.CSafeLoader
    except AttributeError:
        _SafeLoader = _yaml.SafeLoader

    yaml_load = partial(_yaml.load, Loader=_SafeLoader)
