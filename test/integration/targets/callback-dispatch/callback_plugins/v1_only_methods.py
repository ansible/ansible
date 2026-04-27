from __future__ import annotations

import functools

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """Test callback that implements exclusively deprecated v1 callback methods."""
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.called_v1_method_names: set[str] = set()

    def callback_impl(self, *args, name: str, **kwargs) -> None:
        print(f"hi from callback {name!r} with {args=!r} {kwargs=!r}")
        self.called_v1_method_names.add(name)

    for v1_method in CallbackBase._v2_v1_method_map.values():
        if not v1_method:
            continue

        locals()[v1_method.__name__] = functools.partialmethod(callback_impl, name=v1_method.__name__)

    def playbook_on_stats(self, stats, *args, **kwargs):
        if missed_v1_method_calls := (
                {'on_any',
                 'runner_on_ok',
                 'playbook_on_task_start',
                 'runner_on_async_ok',
                 } - self.called_v1_method_names):
            assert False, f"The following v1 callback methods were not invoked as expected: {', '.join(missed_v1_method_calls)}"

        print("v1 callback test PASS")
