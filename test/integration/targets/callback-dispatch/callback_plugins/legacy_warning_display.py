from __future__ import annotations

import collections.abc as c
import functools

from unittest.mock import MagicMock

from ansible.executor.task_result import CallbackTaskResult
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    # DTFIX5: validate VaultedValue redaction behavior

    CALLBACK_NEEDS_ENABLED = True
    seen_tr = []  # track taskresult instances to ensure every call sees a unique instance

    expects_task_result = {
        'v2_runner_on_failed', 'v2_runner_on_ok', 'v2_runner_on_skipped', 'v2_runner_on_unreachable', 'v2_runner_on_async_poll', 'v2_runner_on_async_ok',
        'v2_runner_on_async_failed,', 'v2_on_file_diff', 'v2_runner_item_on_ok',
        'v2_runner_item_on_failed', 'v2_runner_item_on_skipped', 'v2_runner_retry',
    }

    expects_no_task_result = {
        'v2_playbook_on_start', 'v2_playbook_on_notify', 'v2_playbook_on_no_hosts_matched', 'v2_playbook_on_no_hosts_remaining', 'v2_playbook_on_task_start',
        'v2_playbook_on_handler_task_start', 'v2_playbook_on_vars_prompt', 'v2_playbook_on_play_start',
        'v2_playbook_on_include', 'v2_runner_on_start',
    }

    # we're abusing runtime assertions to signify failure in this integration test component; ensure they're not disabled by opimizations
    try:
        assert False
    except AssertionError:
        pass
    else:
        raise BaseException("this test does not function when running Python with optimization")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._display = MagicMock()

    @staticmethod
    def get_first_task_result(args: c.Sequence) -> CallbackTaskResult | None:
        """Find the first CallbackTaskResult in posargs, since the signatures are dynamic and we didn't want to use inspect signature binding."""
        return next((arg for arg in args if isinstance(arg, CallbackTaskResult)), None)

    def v2_on_any(self, *args, **kwargs) -> None:
        """Standard behavioral test for the v2_on_any callback method."""
        print(f'hello from v2_on_any {args=} {kwargs=}')
        if result := self.get_first_task_result(args):
            assert isinstance(result, CallbackTaskResult)

            assert result is self._current_task_result

            assert result not in self.seen_tr

            self.seen_tr.append(result)
        else:
            assert self._current_task_result is None

    def v2_method_expects_task_result(self, *args, method_name: str, **_kwargs) -> None:
        """Standard behavioral tests for callback methods accepting a task result; wired dynamically."""
        print(f'hello from {method_name}')
        result = self.get_first_task_result(args)

        assert result is self._current_task_result

        assert isinstance(result, CallbackTaskResult)

        assert result not in self.seen_tr

        self.seen_tr.append(result)

        has_exception = bool(result.exception)
        has_warnings = bool(result.warnings)
        has_deprecations = bool(result.deprecations)

        self._display.reset_mock()

        self._handle_exception(result.result)  # pops exception from transformed dict

        if has_exception:
            assert 'exception' not in result.result
            self._display._error.assert_called()

        self._display.reset_mock()

        self._handle_warnings(result.result)  # pops warnings/deprecations from transformed dict

        if has_warnings:
            assert 'warnings' not in result.result
            self._display._warning.assert_called()

        if has_deprecations:
            assert 'deprecations' not in result.result
            self._display._deprecated.assert_called()

    def v2_method_expects_no_task_result(self, *args, method_name: str, **_kwargs) -> None:
        """Standard behavioral tests for non-task result callback methods; wired dynamically."""
        print(f'hello from {method_name}')

        assert self.get_first_task_result(args) is None

        assert self._current_task_result is None

    def v2_playbook_on_stats(self, *args, **kwargs) -> None:
        print('hello from v2_playbook_on_stats')
        assert self.get_first_task_result(args) is None

        print('legacy warning display callback test PASS')

    def __getattribute__(self, item: str) -> object:
        if item in CallbackModule.expects_task_result:
            return functools.partial(CallbackModule.v2_method_expects_task_result, self, method_name=item)
        elif item in CallbackModule.expects_no_task_result:
            return functools.partial(CallbackModule.v2_method_expects_no_task_result, self, method_name=item)
        else:
            return object.__getattribute__(self, item)
