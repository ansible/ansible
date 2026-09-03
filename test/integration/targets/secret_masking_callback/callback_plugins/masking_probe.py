# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: masking_probe
    short_description: Serialize raw CallbackTaskResult data to a file to probe secret masking
    description:
        - Writes C(result.result) for each task result straight to a file as JSON, deliberately
          bypassing Display (and the masking Display performs) so the file reflects exactly what
          the callback was handed.
        - Used to verify that a callback which does not opt in via C(ANSIBLE_SUPPORTS_MASKING)
          receives results with secrets already redacted, so serializing them directly cannot leak.
    type: stdout
"""

import json
import os

from ansible.plugins.callback import CallbackBase
from ansible.executor.task_result import CallbackTaskResult


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'masking_probe'

    # Toggled by the test harness. When unset (the default for every real callback that has not
    # been updated for masking) TQM masks result.result on our behalf before we ever see it.
    # When set, we opt in and receive raw data - which the harness uses as a negative control to
    # prove the secret really is present and that the default path is what redacts it.
    ANSIBLE_SUPPORTS_MASKING = os.environ.get('MASKING_PROBE_SUPPORTS_MASKING') == '1'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._out_path = os.environ['MASKING_PROBE_OUTPUT']

    def _dump(self, result: CallbackTaskResult) -> None:
        # Intentionally bypass Display: serialize the result payload the callback was handed
        # straight to disk. Any secret still in plaintext here would leak on a real callback.
        with open(self._out_path, 'a') as fd:
            fd.write(json.dumps(result.result, default=str) + '\n')

    def v2_runner_on_ok(self, result: CallbackTaskResult) -> None:
        self._dump(result)

    def v2_runner_on_failed(self, result: CallbackTaskResult, ignore_errors: bool = False) -> None:
        self._dump(result)
