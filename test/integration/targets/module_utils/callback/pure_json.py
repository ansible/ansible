# (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: pure_json
    type: stdout
    short_description: only outputs the module results as json
"""

import json

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'pure_json'

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._display.display(json.dumps(result.result))

    def v2_runner_on_ok(self, result):
        self._display.display(json.dumps(result.result))

    def v2_runner_on_skipped(self, result):
        self._display.display(json.dumps(result.result))
