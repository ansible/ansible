#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Gregory Shulov (gregory.shulov@gmail.com)
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: infini_host
version_added: 2.3
short_description: Create, Delete and Modify Hosts on Infinibox
description:
    - This module creates, deletes or modifies hosts on Infinibox.
author: Gregory Shulov (@GR360RY)
options:
  name:
    description:
      - Host Name
    required: true
  state:
    description:
      - Creates/Modifies Host when present or removes when absent
    required: false
    default: present
    choices: [ "present", "absent" ]
  wwns:
    description:
      - List of wwns of the host
    required: false
  volume:
    description:
      - Volume name to map to the host
    required: false
extends_documentation_fragment:
    - infinibox
'''

EXAMPLES = '''
- name: Create new new host
  infini_host:
    name: foo.example.com
    user: admin
    password: secret
    system: ibox001

- name: Make sure host bar is available with wwn ports
  infini_host:
    name: bar.example.com
    wwns:
      - "00:00:00:00:00:00:00"
      - "11:11:11:11:11:11:11"
    system: ibox01
    user: admin
    password: secret

- name: Map host foo.example.com to volume bar
  infini_host:
    name: foo.example.com
    volume: bar
    system: ibox01
    user: admin
    password: secret
'''

RETURN = '''
'''

HAS_INFINISDK = True
try:
    from infinisdk import InfiniBox, core
except ImportError:
    HAS_INFINISDK = False

from ansible.module_utils.infinibox import *
from collections import Counter


@api_wrapper
def get_host(module, system):

    host  = None

    for h in system.hosts.to_list():
        if h.get_name() == module.params['name']:
            host = h
            break

    return host


@api_wrapper
def create_host(module, system):

    changed = True

    if not module.check_mode:
        host = system.hosts.create(name=module.params['name'])
        if module.params['wwns']:
            for p in module.params['wwns']:
                host.add_fc_port(p)
        if module.params['volume']:
            host.map_volume(system.volumes.get(name=module.params['volume']))
    module.exit_json(changed=changed)


@api_wrapper
def update_host(module, host):
    changed = False
    name = module.params['name']
    module.exit_json(changed=changed)


@api_wrapper
def delete_host(module, host):
    changed = True
    if not module.check_mode:
        host.delete()
    module.exit_json(changed=changed)


def main():
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            name   = dict(required=True),
            state  = dict(default='present', choices=['present', 'absent']),
            wwns   = dict(type='list'),
            volume = dict()
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        module.fail_json(msg='infinisdk is required for this module')

    state  = module.params['state']
    system = get_system(module)
    host   = get_host(module, system)

    if module.params['volume']:
        try:
            system.volumes.get(name=module.params['volume'])
        except:
            module.fail_json(msg='Volume {} not found'.format(module.params['volume']))

    if host and state == 'present':
        update_host(module, host)
    elif host and state == 'absent':
        delete_host(module, host)
    elif host is None and state == 'absent':
        module.exit_json(changed=False)
    else:
        create_host(module, system)


# Import Ansible Utilities
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
