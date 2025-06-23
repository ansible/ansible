# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import collections.abc as _c
import dataclasses
import functools
import typing as t

from ansible import constants
from ansible.utils import vars as _vars
from ansible.vars.clean import module_response_deepcopy, strip_internal_keys
from ansible.module_utils._internal import _messages
from ansible._internal import _collection_proxy

if t.TYPE_CHECKING:
    from ansible.inventory.host import Host
    from ansible.playbook.task import Task

_IGNORE = ('failed', 'skipped')
_PRESERVE = {'attempts', 'changed', 'retries', '_ansible_no_log', 'exception', 'warnings', 'deprecations'}
_SUB_PRESERVE = {'_ansible_delegated_vars': {'ansible_host', 'ansible_port', 'ansible_user', 'ansible_connection'}}

# stuff callbacks need
CLEAN_EXCEPTIONS = (
    '_ansible_verbose_always',  # for debug and other actions, to always expand data (pretty jsonification)
    '_ansible_item_label',  # to know actual 'item' variable
    '_ansible_no_log',  # jic we didn't clean up well enough, DON'T LOG
    '_ansible_verbose_override',  # controls display of ansible_facts, gathering would be very noise with -v otherwise
)


@t.final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _WireTaskResult:
    """A thin version of `_RawTaskResult` which can be sent over the worker queue."""

    host_name: str
    task_uuid: str
    return_data: _c.MutableMapping[str, object]
    task_fields: _c.Mapping[str, object]


class _BaseTaskResult:
    """
    This class is responsible for interpreting the resulting data
    from an executed task, and provides helper methods for determining
    the result of a given task.
    """

    def __init__(self, host: Host, task: Task, return_data: _c.MutableMapping[str, t.Any], task_fields: _c.Mapping[str, t.Any]) -> None:
        self.__host = host
        self.__task = task
        self._return_data = return_data  # FIXME: this should be immutable, but strategy result processing mutates it in some corner cases
        self.__task_fields = task_fields

    @property
    def host(self) -> Host:
        """The host associated with this result."""
        return self.__host

    @property
    def _host(self) -> Host:
        """Use the `host` property when supporting only ansible-core 2.19 or later."""
        # deprecated: description='Deprecate `_host` in favor of `host`' core_version='2.23'
        return self.__host

    @property
    def task(self) -> Task:
        """The task associated with this result."""
        return self.__task

    @property
    def _task(self) -> Task:
        """Use the `task` property when supporting only ansible-core 2.19 or later."""
        # deprecated: description='Deprecate `_task` in favor of `task`' core_version='2.23'
        return self.__task

    @property
    def task_fields(self) -> _c.Mapping[str, t.Any]:
        """The task fields associated with this result."""
        return self.__task_fields

    @property
    def _task_fields(self) -> _c.Mapping[str, t.Any]:
        """Use the `task_fields` property when supporting only ansible-core 2.19 or later."""
        # deprecated: description='Deprecate `_task_fields` in favor of `task`' core_version='2.23'
        return self.__task_fields

    @property
    def exception(self) -> _messages.ErrorSummary | None:
        """The error from this task result, if any."""
        return self._return_data.get('exception')

    @property
    def warnings(self) -> _c.Sequence[_messages.WarningSummary]:
        """The warnings for this task, if any."""
        return _collection_proxy.SequenceProxy(self._return_data.get('warnings') or [])

    @property
    def deprecations(self) -> _c.Sequence[_messages.DeprecationSummary]:
        """The deprecation warnings for this task, if any."""
        return _collection_proxy.SequenceProxy(self._return_data.get('deprecations') or [])

    @property
    def _loop_results(self) -> list[_c.MutableMapping[str, t.Any]]:
        """Return a list of loop results. If no loop results are present, an empty list is returned."""
        results = self._return_data.get('results')

        if not isinstance(results, list):
            return []

        return results

    @property
    def task_name(self) -> str:
        return str(self.task_fields.get('name', '')) or self.task.get_name()

    def is_changed(self) -> bool:
        return self._check_key('changed')

    def is_skipped(self) -> bool:
        if self._loop_results:
            # Loop tasks are only considered skipped if all items were skipped.
            # some squashed results (eg, dnf) are not dicts and can't be skipped individually
            if all(isinstance(loop_res, dict) and loop_res.get('skipped', False) for loop_res in self._loop_results):
                return True

        # regular tasks and squashed non-dict results
        return bool(self._return_data.get('skipped', False))

    def is_failed(self) -> bool:
        if 'failed_when_result' in self._return_data or any(isinstance(loop_res, dict) and 'failed_when_result' in loop_res for loop_res in self._loop_results):
            return self._check_key('failed_when_result')

        return self._check_key('failed')

    def is_unreachable(self) -> bool:
        return self._check_key('unreachable')

    def needs_debugger(self, globally_enabled: bool = False) -> bool:
        _debugger = self.task_fields.get('debugger')
        _ignore_errors = constants.TASK_DEBUGGER_IGNORE_ERRORS and self.task_fields.get('ignore_errors')

        ret = False

        if globally_enabled and ((self.is_failed() and not _ignore_errors) or self.is_unreachable()):
            ret = True

        if _debugger in ('always',):
            ret = True
        elif _debugger in ('never',):
            ret = False
        elif _debugger in ('on_failed',) and self.is_failed() and not _ignore_errors:
            ret = True
        elif _debugger in ('on_unreachable',) and self.is_unreachable():
            ret = True
        elif _debugger in ('on_skipped',) and self.is_skipped():
            ret = True

        return ret

    def _check_key(self, key: str) -> bool:
        """Fetch a specific named boolean value from the result; if missing, a logical OR of the value from nested loop results; False for non-loop results."""
        if (value := self._return_data.get(key, ...)) is not ...:
            return bool(value)

        return any(isinstance(result, dict) and result.get(key) for result in self._loop_results)


@t.final
class _RawTaskResult(_BaseTaskResult):
    def as_wire_task_result(self) -> _WireTaskResult:
        """Return a `_WireTaskResult` from this instance."""
        return _WireTaskResult(
            host_name=self.host.name,
            task_uuid=self.task._uuid,
            return_data=self._return_data,
            task_fields=self.task_fields,
        )

    def as_callback_task_result(self) -> CallbackTaskResult:
        """Return a `CallbackTaskResult` from this instance."""
        ignore: tuple[str, ...]

        # statuses are already reflected on the event type
        if self.task and self.task.action in constants._ACTION_DEBUG:
            # debug is verbose by default to display vars, no need to add invocation
            ignore = _IGNORE + ('invocation',)
        else:
            ignore = _IGNORE

        subset: dict[str, dict[str, object]] = {}

        # preserve subset for later
        for sub, sub_keys in _SUB_PRESERVE.items():
            sub_data = self._return_data.get(sub)

            if isinstance(sub_data, dict):
                subset[sub] = {key: value for key, value in sub_data.items() if key in sub_keys}

        # DTFIX-FUTURE: is checking no_log here redundant now that we use _ansible_no_log everywhere?
        if isinstance(self.task.no_log, bool) and self.task.no_log or self._return_data.get('_ansible_no_log'):
            censored_result = censor_result(self._return_data)

            if self._loop_results:
                # maintain shape for loop results so callback behavior recognizes a loop was performed
                censored_result.update(results=[
                    censor_result(loop_res) if isinstance(loop_res, dict) and loop_res.get('_ansible_no_log') else loop_res for loop_res in self._loop_results
                ])

            return_data = censored_result
        elif self._return_data:
            return_data = {k: v for k, v in module_response_deepcopy(self._return_data).items() if k not in ignore}

            # remove almost ALL internal keys, keep ones relevant to callback
            strip_internal_keys(return_data, exceptions=CLEAN_EXCEPTIONS)
        else:
            return_data = {}

        # keep subset
        return_data.update(subset)

        return CallbackTaskResult(self.host, self.task, return_data, self.task_fields)


@t.final
class CallbackTaskResult(_BaseTaskResult):
    """Public contract of TaskResult """

    @property
    def _result(self) -> _c.MutableMapping[str, t.Any]:
        """Use the `result` property when supporting only ansible-core 2.19 or later."""
        # deprecated: description='Deprecate `_result` in favor of `result`' core_version='2.23'
        return self.result

    @functools.cached_property
    def result(self) -> _c.MutableMapping[str, t.Any]:
        """
        Returns a cached copy of the task result dictionary for consumption by callbacks.
        Internal custom types are transformed to native Python types to facilitate access and serialization.
        """
        return t.cast(_c.MutableMapping[str, t.Any], _vars.transform_to_native_types(self._return_data))


TaskResult = CallbackTaskResult
"""Compatibility name for the pre-2.19 callback-shaped TaskResult passed to callbacks."""


def censor_result(result: _c.Mapping[str, t.Any]) -> dict[str, t.Any]:
    censored_result = {key: value for key in _PRESERVE if (value := result.get(key, ...)) is not ...}
    censored_result.update(censored="the output has been hidden due to the fact that 'no_log: true' was specified for this result")

    return censored_result
