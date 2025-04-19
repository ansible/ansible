"""Public API for data tagging."""
from __future__ import annotations as _annotations

import datetime as _datetime
import typing as _t

from ._internal import _plugin_exec_context, _datatag
from ._internal._datatag import _tags

_T = _t.TypeVar('_T')


def deprecate_value(
    value: _T,
    msg: str,
    *,
    help_text: str | None = None,
    removal_date: str | _datetime.date | None = None,
    removal_version: str | None = None,
) -> _T:
    """
    Return `value` tagged with the given deprecation details.
    The types `None` and `bool` cannot be deprecated and are returned unmodified.
    Raises a `TypeError` if `value` is not a supported type.
    If `removal_date` is a string, it must be in the form `YYYY-MM-DD`.
    This function is only supported in contexts where an Ansible plugin/module is executing.
    """
    if isinstance(removal_date, str):
        # The `fromisoformat` method accepts other ISO 8601 formats than `YYYY-MM-DD` starting with Python 3.11.
        # That should be considered undocumented behavior of `deprecate_value` rather than an intentional feature.
        removal_date = _datetime.date.fromisoformat(removal_date)

    deprecated = _tags.Deprecated(
        msg=msg,
        help_text=help_text,
        removal_date=removal_date,
        removal_version=removal_version,
        plugin=_plugin_exec_context.PluginExecContext.get_current_plugin_info(),
    )

    return deprecated.tag(value)


def native_type_name(value: object | type, /) -> str:
    """Return the type name of `value`, substituting the native Python type name for internal tagged types."""
    return _datatag.AnsibleTagHelper.base_type(value).__name__
