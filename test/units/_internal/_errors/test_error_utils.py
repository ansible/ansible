from __future__ import annotations

import collections.abc as c
import typing as t

import pytest

from ansible._internal._errors import _error_utils
from ansible.module_utils._internal import _messages
from units.mock.error_helper import raise_exceptions


class _TestContributesError(Exception, _error_utils.ContributesToTaskResult):
    @property
    def result_contribution(self) -> c.Mapping[str, object]:
        return dict(some_flag=True)


class _TestContributesUnreachable(Exception, _error_utils.ContributesToTaskResult):
    @property
    def omit_failed_key(self) -> bool:
        return True

    @property
    def result_contribution(self) -> c.Mapping[str, object]:
        return dict(unreachable=True)


class _TestContributesMsg(Exception, _error_utils.ContributesToTaskResult):
    @property
    def result_contribution(self) -> c.Mapping[str, object]:
        return dict(msg="contributed msg")


@pytest.mark.parametrize("exceptions,expected", (
    (
        (Exception("e0"), _TestContributesError("e1"), ValueError("e2")),
        dict(failed=True, some_flag=True, msg="e0: e1: e2"),
    ),
    (
        (Exception("e0"), ValueError("e1"), _TestContributesError("e2")),
        dict(failed=True, some_flag=True, msg="e0: e1: e2"),
    ),
    (
        (Exception("e0"), _TestContributesUnreachable("e1")),
        dict(unreachable=True, msg="e0: e1"),
    ),
    (
        (Exception("e0"), _TestContributesMsg()),
        dict(failed=True, msg="contributed msg"),
    ),
))
def test_exception_result_contribution(exceptions: t.Sequence[BaseException], expected: dict[str, t.Any]) -> None:
    """Validate result dict augmentation by exceptions conforming to the ContributeToTaskResult protocol."""

    with pytest.raises(Exception) as error:
        raise_exceptions(exceptions)

    result = _error_utils.result_dict_from_exception(error.value, accept_result_contribution=True)

    summary = result.pop('exception')

    assert isinstance(summary, _messages.ErrorSummary)
    assert result == expected
