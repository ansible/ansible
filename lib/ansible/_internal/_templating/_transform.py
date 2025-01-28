"""Runtime projections to provide template/var-visible views of objects that are not natively allowed in Ansible's type system."""

from __future__ import annotations

import typing as t

from ansible.errors import get_chained_message
from ansible.module_utils._internal import _traceback
from ansible.module_utils.common.messages import ErrorSummary, WarningSummary, DeprecationSummary
from ansible.parsing.vault import EncryptedString, VaultHelper
from ansible.utils.display import Display

from ._jinja_common import VaultExceptionMarker
from .. import _errors

display = Display()


def error_summary(value: ErrorSummary) -> str:
    """Render ErrorSummary as a formatted traceback for backward-compatibility with pre-2.19 TaskResult.exception."""
    return value.formatted_traceback or '(traceback unavailable)'


def warning_summary(value: WarningSummary) -> str:
    """Render WarningSummary as a simple message string for backward-compatibility with pre-2.19 TaskResult.warnings."""
    return value.format()


def deprecation_summary(value: DeprecationSummary) -> dict[str, t.Any]:
    """Render DeprecationSummary as dict values for backward-compatibility with pre-2.19 TaskResult.deprecations."""
    return value._as_simple_dict()


def encrypted_string(value: EncryptedString) -> str | VaultExceptionMarker:
    """Decrypt an encrypted string and return its value, or a VaultExceptionMarker if decryption fails."""
    try:
        return value._decrypt()
    except Exception as ex:
        return VaultExceptionMarker(
            ciphertext=VaultHelper.get_ciphertext(value, with_tags=True),
            reason=get_chained_message(ex),
            traceback=_traceback.maybe_extract_traceback(ex, _traceback.TracebackEvent.ERROR),
        )


_type_transform_mapping: dict[type, t.Callable[[t.Any], t.Any]] = {
    _errors.CapturedErrorSummary: error_summary,
    ErrorSummary: error_summary,
    WarningSummary: warning_summary,
    DeprecationSummary: deprecation_summary,
    EncryptedString: encrypted_string,
}
"""This mapping is consulted by `Templar.template` to provide custom views of some objects."""
