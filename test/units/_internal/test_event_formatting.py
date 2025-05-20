from __future__ import annotations

import traceback

from ansible._internal._errors import _error_factory
from ansible._internal._event_formatting import format_event_traceback


def test_traceback_formatting() -> None:
    """Verify our traceback formatting mimics the Python traceback formatting."""
    try:
        try:
            try:
                try:
                    raise Exception('one')
                except Exception as ex:
                    raise Exception('two') from ex
            except Exception:
                raise Exception('three')
        except Exception as ex:
            raise Exception('four') from ex
    except Exception as ex:
        saved_ex = ex

    event = _error_factory.ControllerEventFactory.from_exception(saved_ex, True)  # pylint: disable=used-before-assignment
    ansible_tb = format_event_traceback(event)
    python_tb = ''.join(traceback.format_exception(saved_ex))

    assert ansible_tb == python_tb
