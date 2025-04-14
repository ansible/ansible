# Copyright (c) 2024 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Internal error handling logic for targets. Not for use on the controller."""

from __future__ import annotations

from . import _traceback
from ..common.messages import Detail, ErrorSummary


def create_error_summary(exception: BaseException) -> ErrorSummary:
    """Return an `ErrorDetail` created from the given exception."""
    return ErrorSummary(
        details=_create_error_details(exception),
        formatted_traceback=_traceback.maybe_extract_traceback(exception, _traceback.TracebackEvent.ERROR),
    )


def _create_error_details(exception: BaseException) -> tuple[Detail, ...]:
    """Return an `ErrorMessage` tuple created from the given exception."""
    target_exception: BaseException | None = exception
    error_details: list[Detail] = []

    while target_exception:
        error_details.append(Detail(msg=str(target_exception).strip()))

        target_exception = target_exception.__cause__

    return tuple(error_details)
