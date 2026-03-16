from __future__ import annotations

import contextlib
import re
import typing as t

from ansible._internal import _display_utils
from ansible.module_utils._internal import _messages


@contextlib.contextmanager
def emits_warnings(
    warning_pattern: list[str] | str | None = None,
    deprecation_pattern: list[str] | str | None = None,
    ignore_boilerplate: bool = True,
    allow_unmatched_message: bool = False,
) -> t.Iterator[None]:
    """Assert that the code within the context manager body emits a warning or deprecation warning whose formatted output matches the supplied regex."""
    with _display_utils.DeferredWarningContext(variables=dict(ansible_deprecation_warnings=True)) as ctx:
        yield

    deprecations = ctx.get_deprecation_warnings()
    warnings = ctx.get_warnings()

    if ignore_boilerplate:
        warnings = [warning for warning in warnings if not warning.event.msg.startswith('Deprecation warnings can be disabled by setting')]

    _check_messages('Warning', warning_pattern, warnings, allow_unmatched_message)
    _check_messages('Deprecation', deprecation_pattern, deprecations, allow_unmatched_message)


def _check_messages(
    label: str,
    patterns: list[str] | str | None,
    entries: list[_messages.WarningSummary] | list[_messages.DeprecationSummary],
    allow_unmatched_message: bool,
) -> None:
    if patterns is None:
        return

    if isinstance(patterns, str):
        patterns = [patterns]

    unmatched = set(str(entry) for entry in entries)

    for pattern in patterns:
        matched = False

        for entry in entries:
            str_entry = str(entry)

            if re.search(pattern, str_entry):
                unmatched.discard(str_entry)
                matched = True

        assert matched, f"{label} pattern {pattern!r} did not match."

    if not allow_unmatched_message:
        assert not unmatched, f"{label} unmatched: {unmatched}"
