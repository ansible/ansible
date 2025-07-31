from __future__ import annotations

from ansible.module_utils import six
from ansible.module_utils.common import warnings


def deprecate(importable_name: str, module_name: str, *args) -> object:
    """Inject import-time deprecation warnings."""
    if importable_name not in args:
        raise AttributeError(f"module {module_name!r} has no attribute {importable_name!r}")

    importable = getattr(six, importable_name)

    # TODO Inspect and remove all calls to this function in 2.24
    warnings.deprecate(
        msg=f"Importing {importable_name!r} from {module_name!r} is deprecated.",
        version="2.24",
    )

    return importable
