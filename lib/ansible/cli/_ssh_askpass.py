# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import os
import sys
import typing as t
from multiprocessing.shared_memory import SharedMemory


def main() -> t.NoReturn:
    kwargs: dict[str, t.Any] = {}
    if sys.version_info[:2] >= (3, 13):
        # deprecated: description='unneeded due to track argument for SharedMemory' python_version='3.13'
        kwargs['track'] = False
    try:
        shm = SharedMemory(name=os.environ['_ANSIBLE_SSH_ASKPASS_SHM'], **kwargs)
    except FileNotFoundError:
        # We must be running after the ansible fork is shutting down
        sys.exit(1)
    sys.stdout.buffer.write(shm.buf.tobytes().rstrip(b'\x00'))
    sys.stdout.flush()
    shm.buf[:] = b'\x00' * shm.size
    shm.close()
    sys.exit(0)
