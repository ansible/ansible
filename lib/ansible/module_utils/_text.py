# Copyright (c), Toshio Kuratomi <tkuratomi@ansible.com> 2016
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

from ansible.module_utils.common import warnings as _warnings


_mini_six = {
    "binary_type": bytes,
    "text_type": str,
    "PY3": True,
}


def __getattr__(importable_name: str) -> object:
    """Inject import-time deprecation warnings."""
    help_text: str | None = None
    importable: object
    if importable_name == "codecs":
        import codecs
        importable = codecs
    elif importable_name in {"to_bytes", "to_native", "to_text"}:
        from ansible.module_utils.common.text import converters
        importable = getattr(converters, importable_name)
        help_text = "Use ansible.module_utils.common.text.converters instead."
    elif (importable := _mini_six.get(importable_name, ...)) is ...:
        raise AttributeError(f"module {__name__!r} has no attribute {importable_name!r}")

    _warnings.deprecate(
        msg=f"Importing {importable_name!r} from {__name__!r} is deprecated.",
        version="2.24",
        help_text=help_text,
    )
    return importable
