# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
    name: track_connections
    short_description: Track connection plugins used for hosts
    description:
        - Track connection plugins used for hosts
    type: aggregate
'''

import json
from collections import defaultdict

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'track_connections'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._conntrack = defaultdict(lambda : defaultdict(int))

    def _track(self, result, *args, **kwargs):
        host = result._host.get_name()
        task = result._task

        self._conntrack[host][task.connection] += 1

    v2_runner_on_ok = v2_runner_on_failed = _track
    v2_runner_on_async_poll = v2_runner_on_async_ok = v2_runner_on_async_failed = _track
    v2_runner_item_on_ok = v2_runner_item_on_failed = _track

    def v2_playbook_on_stats(self, stats):
        self._display.display(json.dumps(self._conntrack, indent=4))
