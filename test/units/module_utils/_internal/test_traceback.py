from __future__ import annotations

import pytest
import pytest_mock

from ansible.module_utils._internal import _traceback


@pytest.mark.parametrize("patched_parsed_args, event, expected", (
    (dict(_ansible_tracebacks_for=["error", "warning"]), _traceback.TracebackEvent.ERROR, True),  # included value
    (dict(_ansible_tracebacks_for=["error", "warning"]), _traceback.TracebackEvent.WARNING, True),  # included value
    (dict(_ansible_tracebacks_for=["error", "warning"]), _traceback.TracebackEvent.DEPRECATED, False),  # excluded value
    ({}, _traceback.TracebackEvent.ERROR, False),  # unspecified defaults to no tracebacks
    (dict(_ansible_tracebacks_for="bogus,values"), _traceback.TracebackEvent.ERROR, True),  # parse failure defaults to always enabled
    (None, _traceback.TracebackEvent.ERROR, True),  # fetch failure defaults to always enabled
), ids=str)
def test_default_module_traceback_config(
        patched_parsed_args: dict | None,
        event: _traceback.TracebackEvent,
        expected: bool,
        mocker: pytest_mock.MockerFixture
) -> None:
    """Validate MU traceback config behavior (including unconfigured/broken config fallbacks)."""
    from ansible.module_utils import basic

    mocker.patch.object(basic, '_PARSED_MODULE_ARGS', patched_parsed_args)

    # this should just be an importlib.reload() on _traceback, but that redeclares the enum type and breaks the world
    mocker.patch.object(_traceback, '_module_tracebacks_enabled_events', None)

    assert _traceback._is_module_traceback_enabled(event=event) is expected
