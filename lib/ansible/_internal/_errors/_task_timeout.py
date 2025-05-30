from __future__ import annotations

from collections import abc as _c

from ansible._internal._errors._alarm_timeout import AnsibleTimeoutError
from ansible._internal._errors._error_utils import ContributesToTaskResult
from ansible.module_utils.datatag import deprecate_value


class TaskTimeoutError(AnsibleTimeoutError, ContributesToTaskResult):
    """
    A task-specific timeout.

    This exception provides a result dictionary via the ContributesToTaskResult mixin.
    """

    @property
    def result_contribution(self) -> _c.Mapping[str, object]:
        help_text = "Configure `DISPLAY_TRACEBACK` to see a traceback on timeout errors."

        frame = deprecate_value(
            value=help_text,
            msg="The `timedout.frame` task result key is deprecated.",
            help_text=help_text,
            version="2.23",
        )

        return dict(timedout=dict(frame=frame, period=self.timeout))
