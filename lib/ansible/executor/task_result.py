# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import collections.abc as _c
import functools
import typing as t

from ansible._internal import _collection_proxy
from ansible.module_utils._internal import _messages
from ansible.utils.display import Display

if t.TYPE_CHECKING:
    from ansible._internal import _task
    from ansible.inventory.host import Host
    from ansible.playbook.task import Task


class CallbackTaskResult:
    def __init__(
        self,
        host: Host,
        task: Task,
        utr: _task.UnifiedTaskResult,
    ) -> None:
        self.__host = host
        self.__task = task
        self.__utr = utr

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
        Display().deprecated(
            msg="The `CallbackTaskResult.task_fields` mapping is deprecated.",
            help_text="Use `CallbackTaskResult.task` instead.",
            version="2.24",
        )

        return self.__task.dump_attrs()

    @property
    def _task_fields(self) -> _c.Mapping[str, t.Any]:
        """Use the `task_fields` property when supporting only ansible-core 2.19 or later."""
        # deprecated: description='Deprecate `_task_fields` in favor of `task`' core_version='2.23'
        # Display().deprecated(
        #     msg="The `CallbackTaskResult._task_fields` mapping is deprecated.",
        #     help_text="Use `CallbackTaskResult.task` instead.",
        #     version="2.26",
        # )

        return self.__task.dump_attrs()

    @property
    def exception(self) -> _messages.ErrorSummary | None:
        """The error from this task result, if any."""
        return self.__utr.exception

    @property
    def warnings(self) -> _c.Sequence[_messages.WarningSummary]:
        """The warnings for this task, if any."""
        return _collection_proxy.SequenceProxy(self.__utr.warnings or [])

    @property
    def deprecations(self) -> _c.Sequence[_messages.DeprecationSummary]:
        """The deprecation warnings for this task, if any."""
        return _collection_proxy.SequenceProxy(self.__utr.deprecations or [])

    @property
    def task_name(self) -> str:
        return self.task.get_name()

    def is_changed(self) -> bool:
        return self.__utr.changed

    def is_skipped(self) -> bool:
        return bool(self.__utr.skipped)

    def is_failed(self) -> bool:
        return self.__utr.failed

    def is_unreachable(self) -> bool:
        return bool(self.__utr.unreachable)

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
        # RPFIX-5: consolidate the no_log logic earlier so we don't have to check both?
        return self.__utr.as_result_dict(for_callback=True, censor_callback_result=self.task.no_log or self.__utr.no_log)


TaskResult = CallbackTaskResult
"""Compatibility name for the pre-2.19 callback-shaped TaskResult passed to callbacks."""
