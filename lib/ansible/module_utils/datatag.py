"""Public API for data tagging."""
from __future__ import annotations as _annotations

import typing as _t

from ._internal import _datatag, _deprecator, _traceback, _messages
from ._internal._datatag import _tags

_T = _t.TypeVar('_T')


deprecator_from_collection_name = _deprecator.deprecator_from_collection_name


def deprecate_value(
    value: _T,
    msg: str,
    *,
    version: str | None = None,
    date: str | None = None,
    collection_name: str | None = None,
    deprecator: _messages.PluginInfo | None = None,
    help_text: str | None = None,
) -> _T:
    """
    Return `value` tagged with the given deprecation details.
    The types `None` and `bool` cannot be deprecated and are returned unmodified.
    Raises a `TypeError` if `value` is not a supported type.
    Most callers do not need to provide `collection_name` or `deprecator` -- but provide only one if needed.
    Specify `version` or `date`, but not both.
    If `date` is provided, it should be in the form `YYYY-MM-DD`.
    """
    _skip_stackwalk = True

    deprecated = _tags.Deprecated(
        msg=msg,
        help_text=help_text,
        date=date,
        version=version,
        deprecator=_deprecator.get_best_deprecator(deprecator=deprecator, collection_name=collection_name),
        formatted_traceback=_traceback.maybe_capture_traceback(msg, _traceback.TracebackEvent.DEPRECATED_VALUE),
    )

    return deprecated.tag(value)


def native_type_name(value: object | type, /) -> str:
    """Return the type name of `value`, substituting the native Python type name for internal tagged types."""
    return _datatag.AnsibleTagHelper.base_type(value).__name__
