from __future__ import annotations

import os
import typing as t

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    call_count: t.ClassVar[int] = 0

    def v2_runner_on_ok(self, *args, **kwargs) -> None:
        print(f"hello from ALWAYS ENABLED v2_runner_on_ok {args=} {kwargs=}")

        CallbackModule.call_count += 1

    def v2_playbook_on_stats(self, stats):
        print('hello from ALWAYS ENABLED v2_playbook_on_stats')

        if os.environ.get('_ASSERT_OOPS'):
            assert CallbackModule.call_count < 2, "always enabled callback should not "
            print("no double callbacks test PASS")
