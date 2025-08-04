# Copyright (c) 2024 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Internal utility code for supporting traceback reporting."""

from __future__ import annotations

import enum
import traceback

from . import _stack


class TracebackEvent(enum.Enum):
    """The events for which tracebacks can be enabled."""

    ERROR = enum.auto()
    WARNING = enum.auto()
    DEPRECATED = enum.auto()
    DEPRECATED_VALUE = enum.auto()  # implies DEPRECATED


def traceback_for() -> list[str]:
    """Return a list of traceback event names (not enums) which are enabled."""
    return [value.name.lower() for value in TracebackEvent if is_traceback_enabled(value)]


def is_traceback_enabled(event: TracebackEvent) -> bool:
    """Return True if tracebacks are enabled for the specified event, otherwise return False."""
    return _is_traceback_enabled(event)


def maybe_capture_traceback(msg: str, event: TracebackEvent) -> str | None:
    """
    Optionally capture a traceback for the current call stack, formatted as a string, if the specified traceback event is enabled.
    Frames marked with the `_skip_stackwalk` local are omitted.
    """
    _skip_stackwalk = True

    if not is_traceback_enabled(event):
        return None

    tb_lines = []

    if frame_info := _stack.caller_frame():
        # DTFIX-FUTURE: rewrite target-side tracebacks to point at controller-side paths?
        tb_lines.append('Traceback (most recent call last):\n')
        tb_lines.extend(traceback.format_stack(frame_info.frame))
        tb_lines.append(f'Message: {msg}\n')
    else:
        tb_lines.append('(frame not found)\n')  # pragma: nocover

    return ''.join(tb_lines)


def maybe_extract_traceback(exception: BaseException, event: TracebackEvent) -> str | None:
    """Optionally extract a formatted traceback from the given exception, if the specified traceback event is enabled."""

    if not is_traceback_enabled(event):
        return None

    # deprecated: description='use the single-arg version of format_traceback' python_version='3.9'
    tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)

    return ''.join(tb_lines)


_module_tracebacks_enabled_events: frozenset[TracebackEvent] | None = None
"""Cached enabled TracebackEvent values extracted from `_ansible_tracebacks_for` module arg."""


def _is_module_traceback_enabled(event: TracebackEvent) -> bool:
    """Module utility function to lazily load traceback config and determine if traceback collection is enabled for the specified event."""
    global _module_tracebacks_enabled_events

    if _module_tracebacks_enabled_events is None:
        try:
            # Suboptimal error handling, but since import order can matter, and this is a critical error path, better to fail silently
            # than to mask the triggering error by issuing a new error/warning here.
            from ..basic import _PARSED_MODULE_ARGS

            _module_tracebacks_enabled_events = frozenset(
                TracebackEvent[value.upper()] for value in _PARSED_MODULE_ARGS.get('_ansible_tracebacks_for', [])
            )  # type: ignore[union-attr]
        except BaseException:
            return True  # if things failed early enough that we can't figure this out, assume we want a traceback for troubleshooting

    return event in _module_tracebacks_enabled_events


_is_traceback_enabled = _is_module_traceback_enabled
"""Callable to determine if tracebacks are enabled. Overridden on the controller by display. Use `is_traceback_enabled` instead of calling this directly."""
