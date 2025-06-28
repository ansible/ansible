# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import json
import multiprocessing.resource_tracker
import os
import re
import sys
import typing as t

from multiprocessing.shared_memory import SharedMemory


def main() -> t.Never:
    if len(sys.argv) > 1:
        exit_code = 0 if handle_prompt(sys.argv[1]) else 1
    else:
        exit_code = 1

    sys.exit(exit_code)


def handle_prompt(prompt: str) -> bool:
    if re.search(r'(The authenticity of host |differs from the key for the IP address)', prompt):
        sys.stdout.write('no')
        sys.stdout.flush()
        return True

    # deprecated: description='Python 3.13 and later support track' python_version='3.12'
    can_track = sys.version_info[:2] >= (3, 13)
    kwargs = dict(track=False) if can_track else {}

    # This SharedMemory instance is intentionally not closed or unlinked.
    # Closing will occur naturally in the SharedMemory finalizer.
    # Unlinking is the responsibility of the process which created it.
    shm = SharedMemory(name=os.environ['_ANSIBLE_SSH_ASKPASS_SHM'], **kwargs)

    if not can_track:
        # When track=False is not available, we must unregister explicitly, since it otherwise only occurs during unlink.
        # This avoids resource tracker noise on stderr during process exit.
        multiprocessing.resource_tracker.unregister(shm._name, 'shared_memory')

    cfg = json.loads(shm.buf.tobytes().rstrip(b'\x00'))

    if cfg['prompt'] not in prompt:
        return False

    # Report the password provided by the SharedMemory instance.
    # The contents are left untouched after consumption to allow subsequent attempts to succeed.
    # This can occur when multiple password prompting methods are enabled, such as password and keyboard-interactive, which is the default on macOS.
    sys.stdout.write(cfg['password'])
    sys.stdout.flush()
    return True
