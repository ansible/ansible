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
- If a protection group exists and you try to add non-valid types, eg. a host
  to a volume protection group the module will ignore the invalid types.
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
  target:
    description:
    - List of remote arrays for replication protection group to connect to.
    - Note that all replicated protection groups are asynchronous.
    - Target arrays must already be connected to the source array.
    - Maximum number of targets per Portection Group is 4, assuming your
      configuration suppors this.
    version_added: '2.8'
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create new local protection group
  purefa_pg:
    pgroup: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create new replicated protection group
  purefa_pg:
    pgroup: foo
    target:
      - arrayb
      - arrayc
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

- name: Create replicated protection group for volumes
  purefa_pg:
    pgroup: bar
    volume:
      - vol1
      - vol2
    target: arrayb
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def get_arrays(array):
    """ Get Connected Arrays"""
    arrays = []
    array_details = array.list_array_connections()
    for arraycnt in range(0, len(array_details)):
        arrays.append(array_details[arraycnt]['array_name'])

    return arrays


def get_pgroup(module, array):
    """ Get Protection Group"""
    pgroup = None

    for pgrp in array.list_pgroups():
        if pgrp["name"] == module.params['pgroup']:
            pgroup = pgrp
            break

    return pgroup


def get_pgroup_sched(module, array):
    """ Get Protection Group Schedule"""
    pgroup = None

    for pgrp in array.list_pgroups(schedule=True):
        if pgrp["name"] == module.params['pgroup']:
            pgroup = pgrp
            break

    return pgroup


def make_pgroup(module, array):
    """ Create Protection Group"""
    changed = False
    if module.params['target']:
        connected_arrays = get_arrays(array)
        if connected_arrays == []:
            module.fail_json(msg='No target arrays not connected to source array.')
        if set(module.params['target'][0:4]).issubset(connected_arrays):
            try:
                array.create_pgroup(module.params['pgroup'], targetlist=[module.params['target'][0:4]])
            except Exception:
                module.fail_json(msg='Creation of replicated pgroup {0} failed.'.format(module.params['pgroup']))
        else:
            module.fail_json(msg='Target arrays {0} not connected to source array.'.format(module.params['target']))
    else:
        try:
            array.create_pgroup(module.params['pgroup'])
        except Exception:
            module.fail_json(msg='Creation of pgroup {0} failed.'.format(module.params['pgroup']))
    try:
        if module.params['target']:
            array.set_pgroup(module.params['pgroup'], replicate_enabled=module.params['enabled'])
        else:
            array.set_pgroup(module.params['pgroup'], snap_enabled=module.params['enabled'])
    except Exception:
        module.fail_json(msg='Enabling pgroup {0} failed.'.format(module.params['pgroup']))
    if module.params['volume']:
        try:
            array.set_pgroup(module.params['pgroup'], vollist=module.params['volume'])
        except Exception:
            module.fail_json(msg='Adding volumes to pgroup {0} failed.'.format(module.params['pgroup']))
    if module.params['host']:
        try:
            array.set_pgroup(module.params['pgroup'], hostlist=module.params['host'])
        except Exception:
            module.fail_json(msg='Adding hosts to pgroup {0} failed.'.format(module.params['pgroup']))
    if module.params['hostgroup']:
        try:
            array.set_pgroup(module.params['pgroup'], hgrouplist=module.params['hostgroup'])
        except Exception:
            module.fail_json(msg='Adding hostgroups to pgroup {0} failed.'.format(module.params['pgroup']))
    changed = True
    module.exit_json(changed=changed)


def update_pgroup(module, array):
    """ Update Protection Group"""
    changed = False
    if module.params['target']:
        connected_arrays = get_arrays(array)
        if connected_arrays == []:
            module.fail_json(msg='No target arrays not connected to source array.')
        if not all(x in connected_arrays for x in module.params['target'][0:4]):
            try:
                array.set_pgroup(module.params['pgroup'], targetlist=[module.params['target'][0:4]])
                changed = True
            except Exception:
                module.fail_json(msg='Changing targets for pgroup {0} failed.'.format(module.params['pgroup']))

    if module.params['target'] and module.params['enabled'] != get_pgroup_sched(module, array)['replicate_enabled']:
        try:
            array.set_pgroup(module.params['pgroup'], replicate_enabled=module.params['enabled'])
            changed = True
        except Exception:
            module.fail_json(msg='Changing enabled status of pgroup {0} failed.'.format(module.params['pgroup']))
    elif not module.params['target'] and module.params['enabled'] != get_pgroup_sched(module, array)['snap_enabled']:
        try:
            array.set_pgroup(module.params['pgroup'], snap_enabled=module.params['enabled'])
            changed = True
        except Exception:
            module.fail_json(msg='Changing enabled status of pgroup {0} failed.'.format(module.params['pgroup']))

    if module.params['volume'] and get_pgroup(module, array)['hosts'] is None and get_pgroup(module, array)['hgroups'] is None:
        if get_pgroup(module, array)['volumes'] is None:
            try:
                array.set_pgroup(module.params['pgroup'], vollist=module.params['volume'])
                changed = True
            except Exception:
                module.fail_json(msg='Adding volumes to pgroup {0} failed.'.format(module.params['pgroup']))
        else:
            if not all(x in get_pgroup(module, array)['volumes'] for x in module.params['volume']):
                try:
                    array.set_pgroup(module.params['pgroup'], vollist=module.params['volume'])
                    changed = True
                except Exception:
                    module.fail_json(msg='Changing volumes in pgroup {0} failed.'.format(module.params['pgroup']))

    if module.params['host'] and get_pgroup(module, array)['volumes'] is None and get_pgroup(module, array)['hgroups'] is None:
        if not get_pgroup(module, array)['hosts'] is None:
            try:
                array.set_pgroup(module.params['pgroup'], hostlist=module.params['host'])
                changed = True
            except Exception:
                module.fail_json(msg='Adding hosts to pgroup {0} failed.'.format(module.params['pgroup']))
        else:
            if not all(x in get_pgroup(module, array)['hosts'] for x in module.params['host']):
                try:
                    array.set_pgroup(module.params['pgroup'], hostlist=module.params['host'])
                    changed = True
                except Exception:
                    module.fail_json(msg='Changing hosts in pgroup {0} failed.'.format(module.params['pgroup']))

    if module.params['hostgroup'] and get_pgroup(module, array)['hosts'] is None and get_pgroup(module, array)['volumes'] is None:
        if not get_pgroup(module, array)['hgroups'] is None:
            try:
                array.set_pgroup(module.params['pgroup'], hgrouplist=module.params['hostgroup'])
                changed = True
            except Exception:
                module.fail_json(msg='Adding hostgroups to pgroup {0} failed.'.format(module.params['pgroup']))
        else:
            if not all(x in get_pgroup(module, array)['hgroups'] for x in module.params['hostgroup']):
                try:
                    array.set_pgroup(module.params['pgroup'], hgrouplist=module.params['hostgroup'])
                    changed = True
                except Exception:
                    module.fail_json(msg='Changing hostgroups in pgroup {0} failed.'.format(module.params['pgroup']))

    module.exit_json(changed=changed)


def delete_pgroup(module, array):
    """ Delete Protection Group"""
    changed = True
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
        target=dict(type='list'),
        eradicate=dict(type='bool', default=False),
        enabled=dict(type='bool', default=True),
    ))

    mutually_exclusive = [['volume', 'host', 'hostgroup']]
    module = AnsibleModule(argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=False)

    state = module.params['state']
    array = get_system(module)
    pgroup = get_pgroup(module, array)

    if module.params['host']:
        try:
            for hst in module.params['host']:
                array.get_host(hst)
        except Exception:
            module.fail_json(msg='Host {} not found'.format(hst))

    if module.params['hostgroup']:
        try:
            for hstg in module.params['hostgroup']:
                array.get_hgroup(hstg)
        except Exception:
            module.fail_json(msg='Hostgroup {} not found'.format(hstg))

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
