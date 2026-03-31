from __future__ import annotations

from ansible._internal._errors._task_timeout import TaskTimeoutError
from ansible._internal._task import UnifiedTaskResult
from ansible.module_utils._internal._datatag._tags import Deprecated


def test_task_timeout_result_contribution() -> None:
    """Validate the result contribution shape."""
    try:
        raise TaskTimeoutError(99)
    except TaskTimeoutError as tte:
        utr = UnifiedTaskResult(is_module=False)
        contrib = tte.as_task_result(utr).as_result_dict()

        assert isinstance(contrib, dict)

        timedout = contrib.get('timedout')

        assert isinstance(timedout, dict)

        frame = timedout.get('frame')

        assert isinstance(frame, str)
        assert Deprecated.is_tagged_on(frame)

        period = timedout.get('period')

        assert period == 99
