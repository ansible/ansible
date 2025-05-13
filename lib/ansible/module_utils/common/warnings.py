# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations as _annotations

import typing as _t

from ansible.module_utils._internal import _traceback, _deprecator
from ansible.module_utils.common import messages as _messages
from ansible.module_utils import _internal


def warn(warning: str) -> None:
    """Record a warning to be returned with the module result."""
    # DTFIX-RELEASE: shim to controller display warning like `deprecate`
    _global_warnings[_messages.WarningSummary(
        details=(
            _messages.Detail(msg=warning),
        ),
        formatted_traceback=_traceback.maybe_capture_traceback(_traceback.TracebackEvent.WARNING),
    )] = None


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

    _global_deprecations[_messages.DeprecationSummary(
        details=(
            _messages.Detail(msg=msg, help_text=help_text),
        ),
        formatted_traceback=_traceback.maybe_capture_traceback(_traceback.TracebackEvent.DEPRECATED),
        version=version,
        date=date,
        deprecator=deprecator,
    )] = None


def get_warning_messages() -> tuple[str, ...]:
    """Return a tuple of warning messages accumulated over this run."""
    # DTFIX-RELEASE: add future deprecation comment
    return tuple(item._format() for item in _global_warnings)


_DEPRECATION_MESSAGE_KEYS = frozenset({'msg', 'date', 'version', 'collection_name'})


def get_deprecation_messages() -> tuple[dict[str, _t.Any], ...]:
    """Return a tuple of deprecation warning messages accumulated over this run."""
    # DTFIX-RELEASE: add future deprecation comment
    return tuple({key: value for key, value in item._as_simple_dict().items() if key in _DEPRECATION_MESSAGE_KEYS} for item in _global_deprecations)


def get_warnings() -> list[_messages.WarningSummary]:
    """Return a list of warning messages accumulated over this run."""
    return list(_global_warnings)


def get_deprecations() -> list[_messages.DeprecationSummary]:
    """Return a list of deprecations accumulated over this run."""
    return list(_global_deprecations)


_global_warnings: dict[_messages.WarningSummary, object] = {}
"""Global, ordered, de-deplicated storage of acculumated warnings for the current module run."""

_global_deprecations: dict[_messages.DeprecationSummary, object] = {}
"""Global, ordered, de-deplicated storage of acculumated deprecations for the current module run."""
