# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: masking_probe
    short_description: Serialize CallbackTaskResult data to a file to probe secret masking
    description:
        - Writes C(result.result) for each task result to a file named after its order and task name in the
          C(MASKING_PROBE_OUTPUT) directory using the same C(_dump_results) serialization as the built-in callbacks (JSON or
          YAML per C(result_format)), deliberately bypassing Display (and the masking Display performs)
          so each file reflects exactly what the callback was handed, rendered the way a real callback
          would render it.
        - Used to verify that every callback receives results with secrets already redacted,
          including mapping keys and values which the serializer would otherwise reshape
          (YAML block scalars for multi-line values).
    type: stdout
    extends_documentation_fragment:
      - result_format_callback
"""

import os

from ansible.plugins.callback import CallbackBase
from ansible.executor.task_result import CallbackTaskResult


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'masking_probe'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._out_dir = os.environ['MASKING_PROBE_OUTPUT']
        self._count = 0

    def _dump(self, result: CallbackTaskResult) -> None:
        # Intentionally bypass Display: serialize the result payload the callback was handed
        # straight to disk. Any secret still in plaintext here would leak on a real callback.
        self._count += 1

        with open(os.path.join(self._out_dir, f'{self._count}-{result.task_name}.txt'), 'w') as fd:
            fd.write(self._dump_results(self._without_timing(result.result), indent=4) + '\n')

    def _without_timing(self, result: dict) -> dict:
        # The output is compared with a stored copy, drop the command timing values which change on every run.
        result = {key: value for key, value in result.items() if key not in ('start', 'end', 'delta')}

        if isinstance(items := result.get('results'), list):
            result['results'] = [self._without_timing(item) for item in items]

        return result

    def v2_runner_on_ok(self, result: CallbackTaskResult) -> None:
        self._dump(result)

    def v2_runner_on_failed(self, result: CallbackTaskResult, ignore_errors: bool = False) -> None:
        self._dump(result)
