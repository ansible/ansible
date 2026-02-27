from __future__ import annotations

import dataclasses
import typing as t

from ansible._internal._errors import _error_utils
from ansible.errors import AnsibleRuntimeError
from ansible.module_utils._internal import _messages

if t.TYPE_CHECKING:
    from ansible._internal import _task


class AnsibleCapturedError(AnsibleRuntimeError):
    """An exception representing error detail captured in another context where the error detail must be serialized to be preserved."""

    context: str

    def __init__(
        self,
        *,
        obj: t.Any = None,
        event: _messages.Event,
    ) -> None:
        super().__init__(
            obj=obj,
        )

        self._event = event


class AnsibleResultCapturedError(AnsibleCapturedError, _error_utils.ContributesToTaskResult):
    """
    An exception representing error detail captured in a foreign context where an action/module result dictionary is involved.

    This exception provides a result dictionary via the ContributesToTaskResult mixin.
    """

    def __init__(self, event: _messages.Event, utr: _task.UnifiedTaskResult) -> None:
        self.context = utr._captured_error_context
        self._default_message = utr._captured_error_message

        super().__init__(event=event)

        self._utr = utr

    def as_task_result(self, utr: _task.UnifiedTaskResult) -> _task.UnifiedTaskResult:
        return self._utr  # RPFIX-5: explain this better - Drop the provided UTR on the floor and use the stored one instead.


@dataclasses.dataclass(**_messages._dataclass_kwargs)
class CapturedErrorSummary(_messages.ErrorSummary):
    # RPFIX-5: clean this up (naming, docstring, etc.)
    error_message: str
    error_context: str
    is_module: bool
