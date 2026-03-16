# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import typing as t

from ansible.module_utils.common.text.converters import to_bytes
from ansible.module_utils._internal._ansiballz import _respawn

_ANSIBLE_PARENT_PATH = pathlib.Path(__file__).parents[3]


def has_respawned():
    return hasattr(sys.modules['__main__'], '_respawned')


def respawn_module(interpreter_path) -> t.NoReturn:
    """
    Respawn the currently-running Ansible Python module under the specified Python interpreter.

    Ansible modules that require libraries that are typically available only under well-known interpreters
    (eg, ``apt``, ``dnf``) can use bespoke logic to determine the libraries they need are not
    available, then call `respawn_module` to re-execute the current module under a different interpreter
    and exit the current process when the new subprocess has completed. The respawned process inherits only
    stdout/stderr from the current process.

    Only a single respawn is allowed. ``respawn_module`` will fail on nested respawns. Modules are encouraged
    to call `has_respawned()` to defensively guide behavior before calling ``respawn_module``, and to ensure
    that the target interpreter exists, as ``respawn_module`` will not fail gracefully.

    :arg interpreter_path: path to a Python interpreter to respawn the current module
    """

    if has_respawned():
        raise Exception('module has already been respawned')

    # FUTURE: we need a safe way to log that a respawn has occurred for forensic/debug purposes
    payload = _respawn.create_payload()
    stdin_read, stdin_write = os.pipe()
    os.write(stdin_write, to_bytes(payload))
    os.close(stdin_write)
    rc = subprocess.call([interpreter_path, '--'], stdin=stdin_read)
    sys.exit(rc)  # pylint: disable=ansible-bad-function


def probe_interpreters_for_module(interpreter_paths, module_name):
    """
    Probes a supplied list of Python interpreters, returning the first one capable of
    importing the named module. This is useful when attempting to locate a "system
    Python" where OS-packaged utility modules are located.

    :arg interpreter_paths: iterable of paths to Python interpreters. The paths will be probed
    in order, and the first path that exists and can successfully import the named module will
    be returned (or ``None`` if probing fails for all supplied paths).
    :arg module_name: fully-qualified Python module name to probe for (for example, ``selinux``)
    """
    PYTHONPATH = os.getenv('PYTHONPATH', '')

    env = os.environ.copy()
    env.update({
        'PYTHONPATH': f'{_ANSIBLE_PARENT_PATH}:{PYTHONPATH}'.rstrip(': ')
    })

    for interpreter_path in interpreter_paths:
        if not os.path.exists(interpreter_path):
            continue
        try:
            rc = subprocess.call(
                [
                    interpreter_path,
                    '-c',
                    f'import {module_name}, ansible.module_utils.basic',
                ],
                env=env,
            )
            if rc == 0:
                return interpreter_path
        except Exception:
            continue

    return None
