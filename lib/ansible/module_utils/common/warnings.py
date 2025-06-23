# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations as _annotations

import typing as _t

from ansible.module_utils._internal import _traceback, _deprecator, _event_utils, _messages, _errors
from ansible.module_utils import _internal


def warn(
    warning: str,
    *,
    help_text: str | None = None,
    obj: object | None = None,
) -> None:
    """Record a warning to be returned with the module result."""
    _skip_stackwalk = True

    if _internal.is_controller:
        _display = _internal.import_controller_module('ansible.utils.display').Display()
        _display.warning(
            msg=warning,
            help_text=help_text,
            obj=obj,
        )

        return

    warning = _messages.WarningSummary(
        event=_messages.Event(
            msg=warning,
            help_text=help_text,
            formatted_traceback=_traceback.maybe_capture_traceback(warning, _traceback.TracebackEvent.WARNING),
        ),
    )

    _global_warnings[warning] = None


def error_as_warning(
    msg: str | None,
    exception: BaseException,
    *,
    help_text: str | None = None,
    obj: object = None,
) -> None:
    """Display an exception as a warning."""
    _skip_stackwalk = True

    if _internal.is_controller:
        _display = _internal.import_controller_module('ansible.utils.display').Display()
        _display.error_as_warning(
            msg=msg,
            exception=exception,
            help_text=help_text,
            obj=obj,
        )

        return

    event = _errors.EventFactory.from_exception(exception, _traceback.is_traceback_enabled(_traceback.TracebackEvent.WARNING))

    warning = _messages.WarningSummary(
        event=_messages.Event(
            msg=msg,
            help_text=help_text,
            formatted_traceback=_traceback.maybe_capture_traceback(msg, _traceback.TracebackEvent.WARNING),
            chain=_messages.EventChain(
                msg_reason=_errors.MSG_REASON_DIRECT_CAUSE,
                traceback_reason=_errors.TRACEBACK_REASON_EXCEPTION_DIRECT_WARNING,
                event=event,
            ),
        ),
    )

    _global_warnings[warning] = None


def deprecate(
    msg: str,
    version: str | None = None,
    date: str | None = None,
    collection_name: str | None = None,
    *,
    deprecator: _messages.PluginInfo | None = None,
    help_text: str | None = None,
    obj: object | None = None,
) -> None:
    """
    Record a deprecation warning.
    The `obj` argument is only useful in a controller context; it is ignored for target-side callers.
    Most callers do not need to provide `collection_name` or `deprecator` -- but provide only one if needed.
    Specify `version` or `date`, but not both.
    If `date` is a string, it must be in the form `YYYY-MM-DD`.
    """
    _skip_stackwalk = True

    deprecator = _deprecator.get_best_deprecator(deprecator=deprecator, collection_name=collection_name)

    if _internal.is_controller:
        _display = _internal.import_controller_module('ansible.utils.display').Display()
        _display.deprecated(
            msg=msg,
            version=version,
            date=date,
            help_text=help_text,
            obj=obj,
            # skip passing collection_name; get_best_deprecator already accounted for it when present
            deprecator=deprecator,
        )

        return

    warning = _messages.DeprecationSummary(
        event=_messages.Event(
            msg=msg,
            help_text=help_text,
            formatted_traceback=_traceback.maybe_capture_traceback(msg, _traceback.TracebackEvent.DEPRECATED),
        ),
        version=version,
        date=date,
        deprecator=deprecator,
    )

    _global_deprecations[warning] = None


def get_warning_messages() -> tuple[str, ...]:
    """Return a tuple of warning messages accumulated over this run."""
    # DTFIX7: add future deprecation comment
    return tuple(_event_utils.format_event_brief_message(item.event) for item in _global_warnings)


def get_deprecation_messages() -> tuple[dict[str, _t.Any], ...]:
    """Return a tuple of deprecation warning messages accumulated over this run."""
    # DTFIX7: add future deprecation comment
    return tuple(_event_utils.deprecation_as_dict(item) for item in _global_deprecations)


def get_warnings() -> list[_messages.WarningSummary]:
    """Return a list of warning messages accumulated over this run."""
    return list(_global_warnings)


def get_deprecations() -> list[_messages.DeprecationSummary]:
    """Return a list of deprecations accumulated over this run."""
    return list(_global_deprecations)


_global_warnings: dict[_messages.WarningSummary, object] = {}
"""Global, ordered, de-duplicated storage of accumulated warnings for the current module run."""

_global_deprecations: dict[_messages.DeprecationSummary, object] = {}
"""Global, ordered, de-duplicated storage of accumulated deprecations for the current module run."""
