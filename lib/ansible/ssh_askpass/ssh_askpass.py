#!/usr/bin/env python3
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright: Contributors to the Ansible project

import os
import sys
from multiprocessing.shared_memory import SharedMemory

if __name__ == '__main__':
    kwargs = {}
    if sys.version_info[:2] >= (3, 13):
        kwargs['track'] = False
    try:
        shm = SharedMemory(name=os.environ['_ANSIBLE_SSH_ASKPASS_SHM'], **kwargs)
    except FileNotFoundError:
        # We must be running after the ansible fork is shutting down
        sys.exit(1)
    sys.stdout.buffer.write(shm.buf.tobytes().rstrip(b'\x00'))
    shm.buf[:] = b'\x00' * shm.size
    shm.close()
