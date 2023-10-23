"""Temporary plugin to prevent stdout noise pollution from finalization of abandoned generators under Python 3.12"""
from __future__ import annotations

import sys
import typing as t

if t.TYPE_CHECKING:
    from pylint.lint import PyLinter


def _mask_finalizer_valueerror(ur: t.Any) -> None:
    """Mask only ValueErrors from finalizing abandoned generators; delegate everything else"""
    # work around Py3.12 finalizer changes that sometimes spews this error message to stdout
    # see https://github.com/pylint-dev/pylint/issues/9138
    if ur.exc_type is ValueError and 'generator already executing' in str(ur.exc_value):
        return

    sys.__unraisablehook__(ur)


def register(linter: PyLinter) -> None:  # pylint: disable=unused-argument
    """PyLint plugin registration entrypoint"""
    if sys.version_info >= (3, 12):
        sys.unraisablehook = _mask_finalizer_valueerror
