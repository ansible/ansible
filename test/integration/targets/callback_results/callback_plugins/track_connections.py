# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: track_connections
    short_description: Track connection plugins used for hosts
    description:
        - Track connection plugins used for hosts
    type: aggregate
"""

import functools
import inspect
import json

from collections import defaultdict

from ansible.plugins.callback import CallbackBase
from ansible.executor.task_result import CallbackTaskResult


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'track_connections'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._conntrack = defaultdict(lambda : defaultdict(list))

        # dynamically implement all v2 callback methods that accept `result`
        for name, sig in ((cb, inspect.signature(getattr(self, cb))) for cb in dir(self) if cb.startswith('v2_')):
            if 'result' in sig.parameters:
                setattr(self, name, functools.partial(self._track, event_name=name))

    def _track(self, result: CallbackTaskResult, *_args, event_name: str, **_kwargs):
        host = result.host.get_name()
        task = result.task

        self._conntrack[host][task.connection].append(f'{event_name}: {task.name}')

    def v2_playbook_on_stats(self, stats):
        expected = {
            "testhost": {
                "ansible.builtin.local": [
                    "v2_runner_on_ok: execute a successful non-loop task with the local connection",
                    "v2_runner_on_failed: execute a failing non-loop task with the local connection",
                    "v2_runner_item_on_ok: execute a successful looped task with the local connection",
                    "v2_runner_on_ok: execute a successful looped task with the local connection",
                    "v2_runner_item_on_failed: execute a failing looped task with the local connection",
                    "v2_runner_on_failed: execute a failing looped task with the local connection",
                    "v2_runner_on_async_ok: execute a successful async task with the local connection",
                    "v2_runner_on_ok: execute a successful async task with the local connection",
                    "v2_runner_on_async_failed: execute a failing async task with the local connection",
                    "v2_runner_on_failed: execute a failing async task with the local connection"
                ],
            }
        }

        if self._conntrack == expected:
            self._display.display('FOUND EXPECTED EVENTS')
            return

        # pragma: nocover
        self._display.display(f'ACTUAL\n{json.dumps(self._conntrack, indent=4)}')
        self._display.display(f'EXPECTED\n{json.dumps(expected, indent=4)}')
