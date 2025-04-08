# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import json
import os
import re
import sys
import typing as t
from multiprocessing.shared_memory import SharedMemory

HOST_KEY_RE = re.compile(
    r'(The authenticity of host |differs from the key for the IP address)',
)


def main() -> t.Never:
    try:
        if HOST_KEY_RE.search(sys.argv[1]):
            sys.stdout.buffer.write(b'no')
            sys.stdout.flush()
            sys.exit(0)
    except IndexError:
        pass

    kwargs: dict[str, bool] = {}
    if sys.version_info[:2] >= (3, 13):
        # deprecated: description='unneeded due to track argument for SharedMemory' python_version='3.12'
        kwargs['track'] = False
    try:
        shm = SharedMemory(name=os.environ['_ANSIBLE_SSH_ASKPASS_SHM'], **kwargs)
    except FileNotFoundError:
        # We must be running after the ansible fork is shutting down
        sys.exit(1)
    cfg = json.loads(shm.buf.tobytes().rstrip(b'\x00'))

    try:
        if cfg['prompt'] not in sys.argv[1]:
            sys.exit(1)
    except IndexError:
        sys.exit(1)

    sys.stdout.buffer.write(cfg['password'].encode('utf-8'))
    sys.stdout.flush()
    shm.buf[:] = b'\x00' * shm.size
    shm.close()
    sys.exit(0)
