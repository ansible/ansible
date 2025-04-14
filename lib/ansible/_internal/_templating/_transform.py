"""Runtime projections to provide template/var-visible views of objects that are not natively allowed in Ansible's type system."""

from __future__ import annotations

import dataclasses
import typing as t

from ansible.module_utils._internal import _traceback
from ansible.module_utils.common.messages import PluginInfo, ErrorSummary, WarningSummary, DeprecationSummary
from ansible.parsing.vault import EncryptedString, VaultHelper
from ansible.utils.display import Display

from ._jinja_common import VaultExceptionMarker
from .._errors import _captured, _utils

display = Display()


def plugin_info(value: PluginInfo) -> dict[str, str]:
    """Render PluginInfo as a dictionary."""
    return dataclasses.asdict(value)


def error_summary(value: ErrorSummary) -> str:
    """Render ErrorSummary as a formatted traceback for backward-compatibility with pre-2.19 TaskResult.exception."""
    return value.formatted_traceback or '(traceback unavailable)'


def warning_summary(value: WarningSummary) -> str:
    """Render WarningSummary as a simple message string for backward-compatibility with pre-2.19 TaskResult.warnings."""
    return value._format()


def deprecation_summary(value: DeprecationSummary) -> dict[str, t.Any]:
    """Render DeprecationSummary as dict values for backward-compatibility with pre-2.19 TaskResult.deprecations."""
    # DTFIX-RELEASE: reconsider which deprecation fields should be exposed here, taking into account that collection_name is to be deprecated
    result = value._as_simple_dict()
    result.pop('details')

    return result


def encrypted_string(value: EncryptedString) -> str | VaultExceptionMarker:
    """Decrypt an encrypted string and return its value, or a VaultExceptionMarker if decryption fails."""
    try:
        return value._decrypt()
    except Exception as ex:
        return VaultExceptionMarker(
            ciphertext=VaultHelper.get_ciphertext(value, with_tags=True),
            reason=_utils.get_chained_message(ex),
            traceback=_traceback.maybe_extract_traceback(ex, _traceback.TracebackEvent.ERROR),
        )


_type_transform_mapping: dict[type, t.Callable[[t.Any], t.Any]] = {
    _captured.CapturedErrorSummary: error_summary,
    PluginInfo: plugin_info,
    ErrorSummary: error_summary,
    WarningSummary: warning_summary,
    DeprecationSummary: deprecation_summary,
    EncryptedString: encrypted_string,
}
"""This mapping is consulted by `Templar.template` to provide custom views of some objects."""
