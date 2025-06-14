"""
Utilities to support unit testing of Ansible Python modules.
Not supported for use cases other than testing.
"""

from __future__ import annotations as _annotations

import contextlib as _contextlib
import json as _json
import typing as _t

from unittest import mock as _mock

from ansible.module_utils.common import json as _common_json
from ansible.module_utils._internal import _messages
from . import basic as _basic


@_contextlib.contextmanager
def patch_module_args(args: dict[str, _t.Any] | None = None) -> _t.Iterator[None]:
    """Expose the given module args to `AnsibleModule` instances created within this context."""
    if not isinstance(args, (dict, type(None))):
        raise TypeError("The `args` arg must be a dict or None.")

    args = dict(ANSIBLE_MODULE_ARGS=args or {})
    profile = 'legacy'  # this should be configurable in the future, once the profile feature is more fully baked

    encoder = _common_json.get_module_encoder(profile, _common_json.Direction.CONTROLLER_TO_MODULE)
    args = _json.dumps(args, cls=encoder).encode()

    with _mock.patch.object(_basic, '_ANSIBLE_ARGS', args), _mock.patch.object(_basic, '_ANSIBLE_PROFILE', profile):
        yield


def extract_warnings_messages(results: dict[str, _t.Any]) -> list[str]:
    """Given the results dictionary of a module, extracts the warning messages as a list of strings."""
    result = []
    if isinstance(results.get("warnings"), list):
        for warning in results["warnings"]:
            if isinstance(warning, _messages.WarningSummary):
                result.append(warning.event.msg)
    return result


class DeprecationMessage(_t.TypedDict):
    msg: str
    version: _t.Optional[str]
    date: _t.Optional[str]


def extract_deprecation_records(results: dict[str, _t.Any]) -> list[DeprecationMessage]:
    """Given the results dictionary of a module, extracts the deprecation messages as a list of DeprecationMessage dicts."""
    result: list[DeprecationMessage] = []
    if isinstance(results.get("deprecations"), list):
        for deprecation in results["deprecations"]:
            if isinstance(deprecation, _messages.DeprecationSummary):
                result.append({
                    "msg": deprecation.event.msg,
                    "version": deprecation.version,
                    "date": deprecation.date,
                })
    return result
