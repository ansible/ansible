"""Ansible callback plugin to enforce an execution deadline using faulthandler."""
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import datetime
import faulthandler
import os
import pathlib
import shlex
import sys

from ansible.plugins.callback import CallbackBase

DOCUMENTATION = """
    name: timeout
    type: aggregate
    short_description: Dump thread stacks when an execution deadline is reached.
    description:
      - Enforces an execution deadline by dumping all thread stacks to a file
        and terminating the process when the deadline expires.
      - Intended for use by ansible-test only. Do not enable manually.
    options:
      deadline:
        description: Execution deadline as a UTC epoch timestamp.
        env:
          - name: ANSIBLE_TEST_TIMEOUT_DEADLINE
      dump_dir:
        description: Directory for timeout dump files.
        env:
          - name: ANSIBLE_TEST_TIMEOUT_DIR
"""


class CallbackModule(CallbackBase):
    """Dump thread stacks and exit when an execution deadline is reached."""

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'timeout'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self):
        super().__init__()

        deadline_str = os.environ.get('ANSIBLE_TEST_TIMEOUT_DEADLINE')
        dump_dir = os.environ.get('ANSIBLE_TEST_TIMEOUT_DIR')

        if not deadline_str or not dump_dir:
            return

        deadline = datetime.datetime.fromtimestamp(float(deadline_str), tz=datetime.timezone.utc)
        now = datetime.datetime.now(datetime.timezone.utc)
        remaining = deadline - now

        dump_dir_path = pathlib.Path(dump_dir)
        dump_dir_path.mkdir(parents=True, exist_ok=True)

        dump_path = dump_dir_path / f'timeout-{now.isoformat()}-{os.getpid()}.txt'

        self._dump_file = dump_path.open('w')
        self._dump_file.write(f'Command: {shlex.join(sys.argv).replace("\n", " ")}\n')
        self._dump_file.flush()

        if remaining > datetime.timedelta():
            self._dump_file.write(f'Timeout: {remaining} remaining\n')
            self._dump_file.flush()
            faulthandler.dump_traceback_later(remaining.total_seconds(), file=self._dump_file, exit=True)
        else:
            self._dump_file.write(f'Timeout: deadline exceeded by {-remaining}\n')
            self._dump_file.flush()
            faulthandler.dump_traceback(file=self._dump_file)
            sys.exit(1)
