# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import collections.abc as _c
import os
import subprocess
import sys
import typing as t

from ansible.module_utils.common.text.converters import to_bytes
from ansible.module_utils._internal._ansiballz import _respawn


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
    rc = subprocess.run(
        [interpreter_path, '--'],
        input=to_bytes(payload),
        check=False,
    ).returncode
    sys.exit(rc)  # pylint: disable=ansible-bad-function


def _create_probe_payload(module_names: list[str]) -> str:
    """Create a probe payload that tests if modules can be imported."""
    wrapper_code = sys.modules['__main__']._ansiballz_wrapper_source
    zip_bytes = sys.modules['__main__']._ansiballz_zip_data

    payload = f'''{wrapper_code}

if __name__ == '__main__':
    zip_data = {zip_bytes!r}
    import sys
    sys.exit(probe_imports(zip_data, {module_names!r}))
'''

    return payload


def probe_interpreters_for_module(
    interpreter_paths: _c.Sequence[str],
    module_name: str | None = None,
    *,
    module_names: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> str | None:
    """
    Probes a supplied list of Python interpreters, returning the first one capable of
    importing the named modules. This is useful when attempting to locate a "system
    Python" where OS-packaged utility modules are located.

    FIXME environment description (do we want the utility method and/or stored location?)
    FIXME: describe module_name includes basic
    """
    if module_name is not None:
        if module_names:
            raise ValueError("The module_name and module_names arguments are mutually exclusive.")

        module_names = [module_name, 'ansible.module_utils.basic']  # compatibility behavior

    if not module_names:
        raise ValueError("No module names were specified.")

    # Check if any module requires ansible imports
    needs_ansiballz = any(
        name.startswith('ansible.') or name.startswith('ansible_collections.')
        for name in module_names
    )

    if needs_ansiballz:
        payload = _create_probe_payload(module_names)
        for interpreter_path in interpreter_paths:
            if not os.path.exists(interpreter_path):
                continue
            try:
                rc = subprocess.run(
                    [interpreter_path, '-'],
                    input=to_bytes(payload),
                    env=env,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                ).returncode
                if rc == 0:
                    return interpreter_path
            except Exception:
                continue
    else:
        modules_string = ", ".join(module_names)
        for interpreter_path in interpreter_paths:
            if not os.path.exists(interpreter_path):
                continue
            try:
                rc = subprocess.run(
                    [interpreter_path, '-c', f'import {modules_string}'],
                    env=env,
                    check=False,
                ).returncode
                if rc == 0:
                    return interpreter_path
            except Exception:
                continue

    return None
