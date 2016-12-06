#!/usr/bin/python
# -*- coding: utf-8 -*-
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = """
---
module: "vyos_system"
version_added: "2.3"
author: "Nathaniel Case (@qalthos)"
"""

RETURN = """
"""

EXAMPLES = """
"""

#from ansible.module_utils.local import LocalAnsibleModule
from ansible.module_utils.basic import AnsibleModule as LocalAnsibleModule
from ansible.module_utils.vyos2 import run_commands, get_config


def config_to_dict(module):
    data = get_config(module)

    config = {'domain-search': [], 'name-server': []}

    for line in data:
        if line.startswith('set system hostname'):
            config['hostname'] = line[20:]
        elif line.startswith('set system domain-name'):
            config['domain-name'] = line[23:]
        elif line.startswith('set system domain-search'):
            config['domain-search'].append(line[25:])
        elif line.startswith('set system name-servers'):
            config['name-server'].append(line[24:])

    return config


def spec_to_commands(want, have):
    commands = []

    state = want['state']

    for key in want:
        # These keys do not map to commnads directly
        if key in ('state', 'purge'):
            continue

        device_key = key.replace('_', '-')
        current = have.get(key)
        if state == 'absent' and current:
            commands.append('delete system %s' % device_key)
        elif state == 'present' and current != want[key]:
            if key in ['domain-search', 'name-servers']:
                for config in want[key]:
                    commands.append('set system %s %s' % (device_key, config))
            else:
                commands.append('set system %s %s' % (device_key, want[key]))

    return commands


def main():
    argument_spec = dict(
        hostname=dict(type='str'),
        domain_name=dict(type='str'),
        domain_search=dict(type='list'),
        name_servers=dict(type='list'),
        state=dict(type='str', default='present', choices=['present', 'absent'])
    )

    module = LocalAnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    result = {'changed': False}
    want = module.params
    have = config_to_dict(module)

    commands = spec_to_commands(want, have)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
