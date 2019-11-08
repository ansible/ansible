#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_vg
version_added: '2.9'
short_description: Manage volume groups on Pure Storage FlashArrays
description:
- Create, delete or modify volume groups on Pure Storage FlashArrays.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  vgroup:
    description:
    - The name of the volume group.
    type: str
    required: true
  state:
    description:
    - Define whether the volume group should exist or not.
    type: str
    default: present
    choices: [ absent, present ]
  eradicate:
    description:
    - Define whether to eradicate the volume group on delete and leave in trash.
    type : bool
    default: 'no'
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create new volume group
  purefa_vg:
    vgroup: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Destroy volume group
  purefa_vg:
    vgroup: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: absent

- name: Recover deleted volume group
  purefa_vg:
    vgroup: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Destroy and Eradicate volume group
  purefa_vg:
    vgroup: foo
    eradicate: true
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: absent
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


VGROUP_API_VERSION = '1.13'


def get_pending_vgroup(module, array):
    """ Get Deleted Volume Group"""
    vgroup = None
    for vgrp in array.list_vgroups(pending=True):
        if vgrp["name"] == module.params['vgroup'] and vgrp['time_remaining']:
            vgroup = vgrp
            break

    return vgroup


def get_vgroup(module, array):
    """ Get Volume Group"""
    vgroup = None
    for vgrp in array.list_vgroups():
        if vgrp["name"] == module.params['vgroup']:
            vgroup = vgrp
            break

    return vgroup


def make_vgroup(module, array):
    """ Create Volume Group"""
    changed = True
    if not module.check_mode:
        try:
            array.create_vgroup(module.params['vgroup'])
        except Exception:
            module.fail_json(msg='creation of volume group {0} failed.'.format(module.params['vgroup']))

    module.exit_json(changed=changed)


def recover_vgroup(module, array):
    """ Recover Volume Group"""
    changed = True
    if not module.check_mode:
        try:
            array.recover_vgroup(module.params['vgroup'])
        except Exception:
            module.fail_json(msg='Recovery of volume group {0} failed.'.format(module.params['vgroup']))

    module.exit_json(changed=changed)


def eradicate_vgroup(module, array):
    """ Eradicate Volume Group"""
    changed = True
    if not module.check_mode:
        try:
            array.eradicate_vgroup(module.params['vgroup'])
        except Exception:
            module.fail_json(msg='Eradicating vgroup {0} failed.'.format(module.params['vgroup']))
    module.exit_json(changed=changed)


def delete_vgroup(module, array):
    """ Delete Volume Group"""
    changed = True
    if not module.check_mode:
        try:
            array.destroy_vgroup(module.params['vgroup'])
        except Exception:
            module.fail_json(msg='Deleting vgroup {0} failed.'.format(module.params['vgroup']))
    if module.params['eradicate']:
        eradicate_vgroup(module, array)

    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        vgroup=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        eradicate=dict(type='bool', default=False),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True)

    state = module.params['state']
    array = get_system(module)
    api_version = array._list_available_rest_versions()
    if VGROUP_API_VERSION not in api_version:
        module.fail_json(msg='API version does not support volume groups.')

    vgroup = get_vgroup(module, array)
    xvgroup = get_pending_vgroup(module, array)

    if xvgroup and state == 'present':
        recover_vgroup(module, array)
    elif vgroup and state == 'absent':
        delete_vgroup(module, array)
    elif xvgroup and state == 'absent' and module.params['eradicate']:
        eradicate_vgroup(module, array)
    elif not vgroup and not xvgroup and state == 'present':
        make_vgroup(module, array)
    elif vgroup is None and state == 'absent':
        module.exit_json(changed=False)

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
