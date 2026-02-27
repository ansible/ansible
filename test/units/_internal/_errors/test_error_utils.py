from __future__ import annotations

import typing as t

import pytest

from ansible._internal import _task
from ansible._internal._errors import _error_utils
from ansible.module_utils._internal import _messages
from ansible.playbook.task import Task
from units.mock.error_helper import raise_exceptions


class _TestContributesError(Exception, _error_utils.ContributesToTaskResult):
    def as_task_result(self, utr: _task.UnifiedTaskResult) -> _task.UnifiedTaskResult:
        utr.result_data.update(some_flag=True)

        return utr


class _TestContributesUnreachable(Exception, _error_utils.ContributesToTaskResult):
    @property
    def omit_failed_key(self) -> bool:
        return True

    def as_task_result(self, utr: _task.UnifiedTaskResult) -> _task.UnifiedTaskResult:
        utr.unreachable = True

        return utr


class _TestContributesMsg(Exception, _error_utils.ContributesToTaskResult):
    def as_task_result(self, utr: _task.UnifiedTaskResult) -> _task.UnifiedTaskResult:
        utr.msg = "contributed msg"

        return utr


@pytest.mark.parametrize("exceptions,expected", (
    (
        (Exception("e0"), _TestContributesError("e1"), ValueError("e2")),
        dict(changed=False, failed=True, some_flag=True, msg="e0: e1: e2"),
    ),
    (
        (Exception("e0"), ValueError("e1"), _TestContributesError("e2")),
        dict(changed=False, failed=True, some_flag=True, msg="e0: e1: e2"),
    ),
    (
        (Exception("e0"), _TestContributesUnreachable("e1")),
        dict(changed=False, failed=False, unreachable=True, msg="e0: e1"),
    ),
    (
        (Exception("e0"), _TestContributesMsg()),
        dict(changed=False, failed=True, msg="contributed msg"),
    ),
))
def test_exception_result_contribution(exceptions: t.Sequence[BaseException], expected: dict[str, t.Any]) -> None:
    """Validate result dict augmentation by exceptions conforming to the ContributeToTaskResult protocol."""

    with pytest.raises(Exception) as error:
        raise_exceptions(exceptions)

    with _task.TaskContext(task=Task(), task_vars={}):
        utr = _task.UnifiedTaskResult.create_from_action_exception(error.value, accept_result_contribution=True)

    result = utr.as_result_dict()

    summary = result.pop('exception')

    assert isinstance(summary, _messages.ErrorSummary)
    assert result == expected
