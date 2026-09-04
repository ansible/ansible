#!/usr/bin/python
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import os
import sys

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.respawn import respawn_module, has_respawned
from ansible.module_utils.secrets import register_secret, mask_secrets


def main():
    module = AnsibleModule(argument_spec=dict(
        incoming=dict(type='str', required=True),
        register_as_secret=dict(type='str', required=True),
    ))

    if not has_respawned():
        new_interpreter = os.path.join(module.tmpdir, 'anotherpython')
        os.symlink(sys.executable, new_interpreter)
        respawn_module(interpreter_path=new_interpreter)

        raise Exception('FAIL, should never reach this line after respawn_module')

    incoming = module.params['incoming']

    register_as_secret = module.params['register_as_secret']
    register_secret(register_as_secret)

    module.exit_json(
        changed=False,
        respawned=has_respawned(),
        incoming=incoming,
        incoming_masked=mask_secrets(incoming),
        register_as_secret=register_as_secret,
        register_as_secret_masked=mask_secrets(register_as_secret),
    )


if __name__ == '__main__':
    main()
