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
module: purefa_pg
version_added: "2.4"
short_description: Create, Delete and Modify Protection Groups on Pure Storage FlashArray
description:
    - This module creates, deletes or modifies protection groups on Pure Storage FlashArray.
author: Simon Dodsley (@simondodsley)
options:
  pgroup:
    description:
      - Host Name
    required: true
  state:
    description:
      - Creates or modifies protection group.
    required: false
    default: present
    choices: [ "present", "absent" ]
  volume:
    description:
      - List of existing volumes to add to protection group.
    required: false
  host:
    description:
      - List of existing hosts to add to protection group.
    required: false
  hostgroup:
    description:
      - List of existing hostgroups to add to protection group.
    required: false
  eradicate:
    description:
      - Define whether to eradicate the protection group on delete and leave in trash.
    required: false
    type : bool
    default: false
extends_documentation_fragment:
    - purestorage
'''

EXAMPLES = '''
- name: Create new protection group
  purefa_pg:
    pgroup: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete protection group
  purefa_pg:
    pgroup: foo
    state: absent
    eradicate: true
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create protection group for hostgroups
  purefa_pg:
    pgroup: bar
    hostgroup:
      - hg1
      - hg2
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create protection group for hosts
  purefa_pg:
    pgroup: bar
    host:
      - host1
      - host2
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create protection group for volumes
  purefa_pg:
    pgroup: bar
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


def get_pgroup(module, array):

    pgroup = None

    for h in array.list_pgroups():
        if h["name"] == module.params['pgroup']:
            pgroup = h
            break

    return pgroup


def make_pgroup(module, array):

    changed = True

    if not module.check_mode:
        host = array.create_pgroup(module.params['pgroup'])
        if module.params['volume']:
            array.set_pgroup(module.params['pgroup'], vollist=module.params['volume'])
        if module.params['host']:
            array.set_pgroup(module.params['pgroup'], hostlist=module.params['host'])
        if module.params['hostgroup']:
            array.set_pgroup(module.params['pgroup'], hgrouplist=module.params['hostgroup'])
    module.exit_json(changed=changed)


def update_pgroup(module, array):
    changed = False
    pgroup = module.params['pgroup']
    module.exit_json(changed=changed)


def delete_pgroup(module, array):
    changed = True
    if not module.check_mode:
        array.destroy_pgroup(module.params['pgroup'])
        if module.params['eradicate'] == 'true':
            array.eradicate_pgroup(module.params['pgroup'])
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(
        dict(
            pgroup=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            volume=dict(type='list'),
            host=dict(type='list'),
            hostgroup=dict(type='list'),
            eradicate=dict(default='false', type='bool'),
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_PURESTORAGE:
        module.fail_json(msg='purestorage sdk is required for this module in host')

    state = module.params['state']
    array = get_system(module)
    pgroup = get_pgroup(module, array)

    if module.params['host']:
        try:
            for h in module.params['host']:
                array.get_host(h)
        except:
            module.fail_json(msg='Host {} not found'.format(h))

    if module.params['hostgroup']:
        try:
            for hg in module.params['hostgroup']:
                array.get_hgroup(hg)
        except:
            module.fail_json(msg='Hostgroup {} not found'.format(hg))

    if pgroup and state == 'present':
        update_pgroup(module, array)
    elif pgroup and state == 'absent':
        delete_pgroup(module, array)
    elif pgroup is None and state == 'absent':
        module.exit_json(changed=False)
    else:
        make_pgroup(module, array)


if __name__ == '__main__':
    main()
