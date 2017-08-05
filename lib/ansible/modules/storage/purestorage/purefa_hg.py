#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Simon Dodsley (simon@purestorage.com)
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: purefa_hg
version_added: "2.4"
short_description: Create, Delete and Modify hostgroups on Pure Storage FlashArray
description:
    - This module creates, deletes or modifies hostgroups on Pure Storage FlashArray.
author: Simon Dodsley (@simondodsley)
options:
  hostgroup:
    description:
      - Host Name.
    required: true
  state:
    description:
      - Creates or modifies hostgroup.
    required: false
    default: present
    choices: [ "present", "absent" ]
  host:
    description:
      - List of existing hosts to add to hostgroup.
    required: false
  volume:
    description:
      - List of existing volumes to add to hostgroup.
    required: false
extends_documentation_fragment:
    - purestorage
'''

EXAMPLES = '''
- name: Create new hostgroup
  purefa_hg:
    hostgroup: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete hostgroup - this will disconnect all hosts and volume in the hostgroup
  purefa_hg:
    hostgroup: foo
    state: absent
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create host group with hosts and volumes
  purefa_hg:
    hostgroup: bar
    host:
      - host1
      - host2
    volume:
      - vol1
      - vol2
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


HAS_PURESTORAGE = True
try:
    from purestorage import purestorage
except ImportError:
    HAS_PURESTORAGE = False


def get_hostgroup(module, array):

    hostgroup = None

    for h in array.list_hgroups():
        if h["name"] == module.params['hostgroup']:
            hostgroup = h
            break

    return hostgroup


def make_hostgroup(module, array):

    changed = True

    if not module.check_mode:
        host = array.create_hgroup(module.params['hostgroup'])
        if module.params['host']:
            array.set_hgroup(module.params['hostgroup'], hostlist=module.params['host'])
        if module.params['volume']:
            for v in module.params['volume']:
                array.connect_hgroup(module.params['hostgroup'], v)
    module.exit_json(changed=changed)


def update_hostgroup(module, array):
    changed = False
    hostgroup = module.params['hostgroup']
    module.exit_json(changed=changed)


def delete_hostgroup(module, array):
    changed = True
    if not module.check_mode:
        for vol in array.list_hgroup_connections(module.params['hostgroup']):
            array.disconnect_hgroup(module.params['hostgroup'], vol["vol"])
        host = array.get_hgroup(module.params['hostgroup'])
        array.set_hgroup(module.params['hostgroup'], remhostlist=host['hosts'])
        array.delete_hgroup(module.params['hostgroup'])
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(
        dict(
            hostgroup=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            host=dict(type='list'),
            volume=dict(type='list'),
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_PURESTORAGE:
        module.fail_json(msg='purestorage sdk is required for this module in host')

    state = module.params['state']
    array = get_system(module)
    hostgroup = get_hostgroup(module, array)

    if module.params['host']:
        try:
            for h in module.params['host']:
                array.get_host(h)
        except:
            module.fail_json(msg='Host not found')

    if module.params['volume']:
        try:
            for v in module.params['volume']:
                array.get_volume(v)
        except:
            module.fail_json(msg='Volume not found')

    if hostgroup and state == 'present':
        update_hostgroup(module, array)
    elif hostgroup and state == 'absent':
        delete_hostgroup(module, array)
    elif hostgroup is None and state == 'absent':
        module.exit_json(changed=False)
    else:
        make_hostgroup(module, array)


if __name__ == '__main__':
    main()
