# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import subprocess
import sys

from ansible.module_utils.common.text.converters import to_bytes, to_native


def has_respawned():
    return hasattr(sys.modules['__main__'], '_respawned')


def respawn_module(interpreter_path):
    """
    Respawn the currently-running Ansible Python module under the specified Python interpreter.

    Ansible modules that require libraries that are typically available only under well-known interpreters
    (eg, ``yum``, ``apt``, ``dnf``) can use bespoke logic to determine the libraries they need are not
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

    payload = _create_payload()
    stdin_read, stdin_write = os.pipe()
    os.write(stdin_write, to_bytes(payload))
    os.close(stdin_write)
    rc = subprocess.call([interpreter_path, '--'], stdin=stdin_read)
    sys.exit(rc)  # pylint: disable=ansible-bad-function


def _create_payload():
    from ansible.module_utils import basic
    smuggled_args = getattr(basic, '_ANSIBLE_ARGS')
    if not smuggled_args:
        raise Exception('unable to access ansible.module_utils.basic._ANSIBLE_ARGS (not launched by AnsiballZ?)')
    module_fqn = sys.modules['__main__']._module_fqn
    modlib_path = sys.modules['__main__']._modlib_path
    respawn_code_template = '''
import runpy
import json
import sys

module_fqn = '{module_fqn}'
modlib_path = '{modlib_path}'
smuggled_args = b"""{smuggled_args}""".strip()


if __name__ == '__main__':
    sys.path.insert(0, modlib_path)

    from ansible.module_utils import basic
    basic._ANSIBLE_ARGS = smuggled_args

    runpy.run_module(module_fqn, init_globals=dict(_respawned=True), run_name='__main__', alter_sys=True)
    '''

    respawn_code = respawn_code_template.format(module_fqn=module_fqn, modlib_path=modlib_path, smuggled_args=to_native(smuggled_args))

    return respawn_code
