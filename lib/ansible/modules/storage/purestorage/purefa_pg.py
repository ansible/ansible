#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_pg
version_added: '2.4'
short_description: Manage protection groups on Pure Storage FlashArrays
description:
- Create, delete or modify protection groups on Pure Storage FlashArrays.
author:
- Simon Dodsley (@sdodsley)
options:
  pgroup:
    description:
    - The name of the protection group.
    required: true
  state:
    description:
    - Define whether the protection group should exist or not.
    default: present
    choices: [ absent, present ]
  volume:
    description:
    - List of existing volumes to add to protection group.
  host:
    description:
    - List of existing hosts to add to protection group.
  hostgroup:
    description:
    - List of existing hostgroups to add to protection group.
  eradicate:
    description:
    - Define whether to eradicate the protection group on delete and leave in trash.
    type : bool
    default: 'no'
  enabled:
    description:
    - Define whether to enabled snapshots for the protection group.
    type : bool
    default: 'yes'
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create new protection group
  purefa_pg:
    pgroup: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create new protection group with snapshots disabled
  purefa_pg:
    pgroup: foo
    enabled: false
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete protection group
  purefa_pg:
    pgroup: foo
    eradicate: true
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: absent

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

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


try:
    from purestorage import purestorage
    HAS_PURESTORAGE = True
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
        array.set_pgroup(module.params['pgroup'], snap_enabled=module.params['enabled'])
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
        if module.params['eradicate']:
            array.eradicate_pgroup(module.params['pgroup'])
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        pgroup=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        volume=dict(type='list'),
        host=dict(type='list'),
        hostgroup=dict(type='list'),
        eradicate=dict(type='bool', default=False),
        enabled=dict(type='bool', default=True),
    ))

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
