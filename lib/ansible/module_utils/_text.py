# Copyright (c), Toshio Kuratomi <tkuratomi@ansible.com> 2016
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

from ansible.module_utils.common import warnings as _warnings


def __getattr__(importable_name):
    """Inject import-time deprecation warnings."""
    help_text = ""
    if importable_name == "codecs":
        import codecs
        importable = codecs
    elif importable_name in {"binary_type", "text_type", "PY3"}:
        from ansible.module_utils import six
        importable = getattr(six, importable_name)
    elif importable_name in {"to_bytes", "to_native", "to_text"}:
        from ansible.module_utils.common.text import converters
        importable = getattr(converters, importable_name)
        help_text = "Use ansible.module_utils.common.text.converters instead."
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {importable_name!r}")

    _warnings.deprecate(
        msg=f"Importing {importable_name!r} from {__name__!r} is deprecated.",
        version="2.24",
        help_text=help_text,
    )
    return importable
