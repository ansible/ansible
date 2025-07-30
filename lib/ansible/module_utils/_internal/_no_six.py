from __future__ import annotations

import inspect

from ansible.module_utils import six
from ansible.module_utils.common import warnings


def deprecate(importable_name: str, *args) -> object:
    """Inject import-time deprecation warnings."""
    parent__name__ = inspect.stack()[1].frame.f_globals['__name__']

    if importable_name not in args:
        raise AttributeError(f"module {parent__name__!r} has no attribute {importable_name!r}")

    importable = getattr(six, importable_name)

    # TODO Inspect and remove all calls to this function in 2.24
    warnings.deprecate(
        msg=f"Importing {importable_name!r} from {parent__name__!r} is deprecated.",
        version="2.24",
    )

    return importable
