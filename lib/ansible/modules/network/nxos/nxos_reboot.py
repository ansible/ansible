#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nxos_reboot
extends_documentation_fragment: nxos
version_added: 2.2
short_description: Reboot a network device.
description:
    - Reboot a network device.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - The module will fail due to timeout issues, but the reboot will be
      performed anyway.
options:
    confirm:
        description:
            - Safeguard boolean. Set to true if you're sure you want to reboot.
        required: false
        default: false
'''

EXAMPLES = '''
- nxos_reboot:
    confirm: true
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
'''

RETURN = '''
rebooted:
    description: Whether the device was instructed to reboot.
    returned: success
    type: boolean
    sample: true
'''

from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def reboot(module):
    cmds = [
        {'command': 'terminal-dont-ask'},
        {'command': 'reload', 'output': 'text'}
    ]
    run_commands(module, cmds)

def main():
    argument_spec = {}
    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    if not module.check_mode:
        reboot(module)
    changed = True

    results = {
        'changed': True,
        'warnings': warnings
    }

    module.exit_json(**results)


if __name__ == '__main__':
    main()

