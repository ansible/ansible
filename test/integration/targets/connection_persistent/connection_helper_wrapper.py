# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import os
import pathlib
import sys
import time

from ansible.cli import scripts


counter_path = pathlib.Path(os.environ['ANSIBLE_TEST_CONNECTION_HELPER_COUNTER'])
with counter_path.open('a', encoding='utf-8') as counter:
    counter.write(f'{os.getpid()}\n')

if barrier_size := int(os.environ.get('ANSIBLE_TEST_CONNECTION_HELPER_BARRIER_SIZE', '0')):
    deadline = time.monotonic() + 10
    while len(counter_path.read_text(encoding='utf-8').splitlines()) < barrier_size:
        if time.monotonic() >= deadline:
            raise RuntimeError(f'timed out waiting for {barrier_size} connection helpers')
        time.sleep(0.01)

helper_path = os.environ.get('ANSIBLE_TEST_CONNECTION_HELPER_TARGET') or os.environ.get('ANSIBLE_TEST_REAL_CONNECTION_PATH')
if not helper_path:
    helper_path = str(pathlib.Path(scripts.__file__).parent / 'ansible_connection_cli_stub.py')

os.execv(sys.executable, [sys.executable, helper_path, *sys.argv[1:]])
