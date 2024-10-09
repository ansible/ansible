"""Temporary plugin to prevent stdout noise pollution from finalization of abandoned generators."""
from __future__ import annotations

import sys
import typing as t

if t.TYPE_CHECKING:
    from pylint.lint import PyLinter


def _mask_finalizer_valueerror(ur: t.Any) -> None:
    """Mask only ValueErrors from finalizing abandoned generators; delegate everything else"""
    # work around Python finalizer issue that sometimes spews this error message to stdout
    # see https://github.com/pylint-dev/pylint/issues/9138
    if ur.exc_type is ValueError and 'generator already executing' in str(ur.exc_value):
        return

    sys.__unraisablehook__(ur)


def register(linter: PyLinter) -> None:  # pylint: disable=unused-argument
    """PyLint plugin registration entrypoint"""
    sys.unraisablehook = _mask_finalizer_valueerror
