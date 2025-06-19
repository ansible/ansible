"""Runtime projections to provide template/var-visible views of objects that are not natively allowed in Ansible's type system."""

from __future__ import annotations

import dataclasses
import typing as t

from ansible.module_utils._internal import _traceback, _event_utils, _messages
from ansible.parsing.vault import EncryptedString, VaultHelper
from ansible.utils.display import Display

from ._jinja_common import VaultExceptionMarker
from .._errors import _captured, _error_factory
from .. import _event_formatting

display = Display()


def plugin_info(value: _messages.PluginInfo) -> dict[str, str]:
    """Render PluginInfo as a dictionary."""
    return dataclasses.asdict(value)


def plugin_type(value: _messages.PluginType) -> str:
    """Render PluginType as a string."""
    return value.value


def error_summary(value: _messages.ErrorSummary) -> str:
    """Render ErrorSummary as a formatted traceback for backward-compatibility with pre-2.19 TaskResult.exception."""
    if _traceback._is_traceback_enabled(_traceback.TracebackEvent.ERROR):
        return _event_formatting.format_event_traceback(value.event)

    return '(traceback unavailable)'


def warning_summary(value: _messages.WarningSummary) -> str:
    """Render WarningSummary as a simple message string for backward-compatibility with pre-2.19 TaskResult.warnings."""
    return _event_utils.format_event_brief_message(value.event)


def deprecation_summary(value: _messages.DeprecationSummary) -> dict[str, t.Any]:
    """Render DeprecationSummary as dict values for backward-compatibility with pre-2.19 TaskResult.deprecations."""
    transformed = _event_utils.deprecation_as_dict(value)
    transformed.update(deprecator=value.deprecator)

    return transformed


def encrypted_string(value: EncryptedString) -> str | VaultExceptionMarker:
    """Decrypt an encrypted string and return its value, or a VaultExceptionMarker if decryption fails."""
    try:
        return value._decrypt()
    except Exception as ex:
        return VaultExceptionMarker(
            ciphertext=VaultHelper.get_ciphertext(value, with_tags=True),
            event=_error_factory.ControllerEventFactory.from_exception(ex, _traceback.is_traceback_enabled(_traceback.TracebackEvent.ERROR)),
        )


_type_transform_mapping: dict[type, t.Callable[[t.Any], t.Any]] = {
    _captured.CapturedErrorSummary: error_summary,
    _messages.PluginInfo: plugin_info,
    _messages.PluginType: plugin_type,
    _messages.ErrorSummary: error_summary,
    _messages.WarningSummary: warning_summary,
    _messages.DeprecationSummary: deprecation_summary,
    EncryptedString: encrypted_string,
}
"""This mapping is consulted by `Templar.template` to provide custom views of some objects."""
