# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import datetime
import typing as t

from .._internal import _traceback
from ..common.messages import Detail, WarningSummary, DeprecationSummary


def warn(warning: str) -> None:
    """Record a warning to be returned with the module result."""
    _global_warnings[WarningSummary(
        details=(
            Detail(msg=warning),
        ),
        formatted_traceback=_traceback.maybe_capture_traceback(_traceback.TracebackEvent.WARNING),
    )] = None


def deprecate(msg: str, version: str | None = None, date: str | datetime.date | None = None, collection_name: str | None = None) -> None:
    """Record a deprecation warning to be returned with the module result."""
    if isinstance(date, datetime.date):
        date = str(date)

    _global_deprecations[DeprecationSummary(
        details=(
            Detail(msg=msg),
        ),
        formatted_traceback=_traceback.maybe_capture_traceback(_traceback.TracebackEvent.DEPRECATED),
        version=version,
        date=date,
        collection_name=collection_name,
    )] = None


def get_warning_messages() -> tuple[str, ...]:
    """Return a tuple of warning messages accumulated over this run."""
    # DTFIX-MERGE: add future deprecation comment
    return tuple(item.format() for item in _global_warnings)


def get_deprecation_messages() -> tuple[dict[str, t.Any], ...]:
    """Return a tuple of deprecation warning messages accumulated over this run."""
    # DTFIX-MERGE: add future deprecation comment
    return tuple(item._as_simple_dict() for item in _global_deprecations)


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
