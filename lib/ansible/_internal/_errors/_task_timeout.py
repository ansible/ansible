from __future__ import annotations

from ansible._internal import _task
from ansible._internal._errors._alarm_timeout import AnsibleTimeoutError
from ansible._internal._errors._error_utils import ContributesToTaskResult
from ansible.module_utils.datatag import deprecate_value


class TaskTimeoutError(AnsibleTimeoutError, ContributesToTaskResult):
    """
    A task-specific timeout.

    This exception provides a result dictionary via the ContributesToTaskResult mixin.
    """

    def as_task_result(self, utr: _task.UnifiedTaskResult) -> _task.UnifiedTaskResult:
        help_text = "Configure `DISPLAY_TRACEBACK` to see a traceback on timeout errors."

        frame = deprecate_value(
            value=help_text,
            msg="The `timedout.frame` task result key is deprecated.",
            help_text=help_text,
            version="2.23",
        )

        utr.result_data.update(timedout=dict(frame=frame, period=self.timeout))

        return utr
