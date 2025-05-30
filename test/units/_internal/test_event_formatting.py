from __future__ import annotations

import traceback

from ansible._internal._errors import _error_factory
from ansible._internal._event_formatting import format_event_traceback
from units.mock.error_helper import raise_exceptions

import pytest


def test_traceback_formatting() -> None:
    """Verify our traceback formatting mimics the Python traceback formatting."""
    with pytest.raises(Exception) as error:
        raise_exceptions((
            Exception('a'),
            Exception('b'),
            Exception('c'),
            Exception('d'),
        ))

    event = _error_factory.ControllerEventFactory.from_exception(error.value, True)
    ansible_tb = format_event_traceback(event)
    python_tb = ''.join(traceback.format_exception(error.value))

    assert ansible_tb == python_tb
