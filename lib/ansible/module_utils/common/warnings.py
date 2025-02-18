# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import datetime
import typing as t

from .._internal import _traceback, _plugin_exec_context
from ..common.messages import Detail, WarningSummary, DeprecationSummary

_UNSET = t.cast(t.Any, ...)


def warn(warning: str) -> None:
    """Record a warning to be returned with the module result."""
    _global_warnings[WarningSummary(
        details=(
            Detail(msg=warning),
        ),
        formatted_traceback=_traceback.maybe_capture_traceback(_traceback.TracebackEvent.WARNING),
    )] = None


def deprecate(msg: str, version: str | None = None, date: str | datetime.date | None = None, collection_name: str | None = _UNSET) -> None:
    """Record a deprecation warning to be returned with the module result."""
    if isinstance(date, datetime.date):
        date = str(date)

    # deprecated: description='enable the deprecation message for collection_name' core_version='2.23'
    # if collection_name is not _UNSET:
    #     deprecate('The `collection_name` argument to `deprecate` is deprecated.', version='2.25')

    _global_deprecations[DeprecationSummary(
        details=(
            Detail(msg=msg),
        ),
        formatted_traceback=_traceback.maybe_capture_traceback(_traceback.TracebackEvent.DEPRECATED),
        version=version,
        date=date,
        plugin=_plugin_exec_context.PluginExecContext.get_current_plugin_info(),
    )] = None


def get_warning_messages() -> tuple[str, ...]:
    """Return a tuple of warning messages accumulated over this run."""
    # DTFIX-RELEASE: add future deprecation comment
    return tuple(item.format() for item in _global_warnings)


def get_deprecation_messages() -> tuple[dict[str, t.Any], ...]:
    """Return a tuple of deprecation warning messages accumulated over this run."""
    # DTFIX-RELEASE: add future deprecation comment
    messages = [item._as_simple_dict() for item in _global_deprecations]

    for message in messages:
        message.pop('plugin', None)  # don't expose new data via legacy API

    return tuple(messages)


def get_warnings() -> list[WarningSummary]:
    """Return a list of warning messages accumulated over this run."""
    return list(_global_warnings)


def get_deprecations() -> list[DeprecationSummary]:
    """Return a list of deprecations accumulated over this run."""
    return list(_global_deprecations)


_global_warnings: dict[WarningSummary, object] = {}
"""Global, ordered, de-deplicated storage of acculumated warnings for the current module run."""

_global_deprecations: dict[DeprecationSummary, object] = {}
"""Global, ordered, de-deplicated storage of acculumated deprecations for the current module run."""
