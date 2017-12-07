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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: "vyos_system"
version_added: "2.3"
author: "Nathaniel Case (@qalthos)"
short_description: Run `set system` commands on VyOS devices
description:
  - Runs one or more commands on remote devices running VyOS.
    This module can also be introspected to validate key parameters before
    returning successfully.
extends_documentation_fragment: vyos
notes:
  - Tested against VYOS 1.1.7
options:
  hostname:
    description:
      - Configure the device hostname parameter. This option takes an ASCII string value.
  domain_name:
    description:
      - The new domain name to apply to the device.
  name_server:
    description:
      - A list of name servers to use with the device. Mutually exclusive with
        I(domain_search)
    required: false
    default: null
  domain_search:
    description:
      - A list of domain names to search. Mutually exclusive with
        I(name_server)
  state:
    description:
      - Whether to apply (C(present)) or remove (C(absent)) the settings.
    default: present
    choices: ['present', 'absent']
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - set system hostname vyos01
    - set system domain-name foo.example.com
"""

EXAMPLES = """
- name: configure hostname and domain-name
  vyos_system:
    hostname: vyos01
    domain_name: test.example.com

- name: remove all configuration
  vyos_system:
    state: absent

- name: configure name servers
  vyos_system:
    name_server:
      - 8.8.8.8
      - 8.8.4.4

- name: configure domain search suffixes
  vyos_system:
    domain_search:
      - sub1.example.com
      - sub2.example.com
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.vyos.vyos import get_config, load_config
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec


def spec_key_to_device_key(key):
    device_key = key.replace('_', '-')

    # domain-search is longer than just it's key
    if device_key == 'domain-search':
        device_key += ' domain'

    return device_key


def config_to_dict(module):
    data = get_config(module)

    config = {'domain_search': [], 'name_server': []}

    for line in data.split('\n'):
        if line.startswith('set system host-name'):
            config['host_name'] = line[22:-1]
        elif line.startswith('set system domain-name'):
            config['domain_name'] = line[24:-1]
        elif line.startswith('set system domain-search domain'):
            config['domain_search'].append(line[33:-1])
        elif line.startswith('set system name-server'):
            config['name_server'].append(line[24:-1])

    return config


def spec_to_commands(want, have):
    commands = []

    state = want.pop('state')

    # state='absent' by itself has special meaning
    if state == 'absent' and all(v is None for v in want.values()):
        # Clear everything
        for key in have:
            commands.append('delete system %s' % spec_key_to_device_key(key))

    for key in want:
        if want[key] is None:
            continue

        current = have.get(key)
        proposed = want[key]
        device_key = spec_key_to_device_key(key)

        # These keys are lists which may need to  be reconciled with the device
        if key in ['domain_search', 'name_server']:
            if not proposed:
                # Empty list was passed, delete all values
                commands.append("delete system %s" % device_key)
            for config in proposed:
                if state == 'absent' and config in current:
                    commands.append("delete system %s '%s'" % (device_key, config))
                elif state == 'present' and config not in current:
                    commands.append("set system %s '%s'" % (device_key, config))
        else:
            if state == 'absent' and current and proposed:
                commands.append('delete system %s' % device_key)
            elif state == 'present' and proposed and proposed != current:
                commands.append("set system %s '%s'" % (device_key, proposed))

    return commands


def map_param_to_obj(module):
    return {
        'host_name': module.params['host_name'],
        'domain_name': module.params['domain_name'],
        'domain_search': module.params['domain_search'],
        'name_server': module.params['name_server'],
        'state': module.params['state']
    }


def main():
    argument_spec = dict(
        host_name=dict(type='str'),
        domain_name=dict(type='str'),
        domain_search=dict(type='list'),
        name_server=dict(type='list', aliases=['name_servers']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    argument_spec.update(vyos_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[('domain_name', 'domain_search')],
    )

    warnings = list()

    result = {'changed': False, 'warnings': warnings}

    want = map_param_to_obj(module)
    have = config_to_dict(module)

    commands = spec_to_commands(want, have)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        response = load_config(module, commands, commit=commit)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
