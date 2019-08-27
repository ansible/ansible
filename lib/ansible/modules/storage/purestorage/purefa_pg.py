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
module: purefa_pg
version_added: '2.4'
short_description: Manage protection groups on Pure Storage FlashArrays
description:
- Create, delete or modify protection groups on Pure Storage FlashArrays.
- If a protection group exists and you try to add non-valid types, eg. a host
  to a volume protection group the module will ignore the invalid types.
- Protection Groups on Offload targets are supported.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  pgroup:
    description:
    - The name of the protection group.
    type: str
    required: true
  state:
    description:
    - Define whether the protection group should exist or not.
    type: str
    default: present
    choices: [ absent, present ]
  volume:
    description:
    - List of existing volumes to add to protection group.
    type: list
  host:
    description:
    - List of existing hosts to add to protection group.
    type: list
  hostgroup:
    description:
    - List of existing hostgroups to add to protection group.
    type: list
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
    - List of remote arrays or offload target for replication protection group
      to connect to.
    - Note that all replicated protection groups are asynchronous.
    - Target arrays or offload targets must already be connected to the source array.
    - Maximum number of targets per Portection Group is 4, assuming your
      configuration suppors this.
    type: list
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

- name: Create new replicated protection group to offload target and remote array
  purefa_pg:
    pgroup: foo
    target:
      - offload
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

- name: Eradicate protection group foo on offload target where source array is arrayA
  purefa_pg:
    pgroup: "arrayA:foo"
    target: offload
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


OFFLOAD_API_VERSION = '1.16'


def get_targets(array):
    """Get Offload Targets"""
    targets = []
    try:
        target_details = array.list_offload()
    except Exception:
        return None

    for targetcnt in range(0, len(target_details)):
        if target_details[targetcnt]['status'] == "connected":
            targets.append(target_details[targetcnt]['name'])
    return targets


def get_arrays(array):
    """ Get Connected Arrays"""
    arrays = []
    array_details = array.list_array_connections()
    for arraycnt in range(0, len(array_details)):
        if array_details[arraycnt]['connected']:
            arrays.append(array_details[arraycnt]['array_name'])

    return arrays


def get_pending_pgroup(module, array):
    """ Get Protection Group"""
    pgroup = None
    if ":" in module.params['pgroup']:
        for pgrp in array.list_pgroups(pending=True, on="*"):
            if pgrp["name"] == module.params['pgroup'] and pgrp['time_remaining']:
                pgroup = pgrp
                break
    else:
        for pgrp in array.list_pgroups(pending=True):
            if pgrp["name"] == module.params['pgroup'] and pgrp['time_remaining']:
                pgroup = pgrp
                break

    return pgroup


def get_pgroup(module, array):
    """ Get Protection Group"""
    pgroup = None
    if ":" in module.params['pgroup']:
        for pgrp in array.list_pgroups(on="*"):
            if pgrp["name"] == module.params['pgroup']:
                pgroup = pgrp
                break
    else:
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


def check_pg_on_offload(module, array):
    """ Check if PG already exists on offload target """
    array_name = array.get()['array_name']
    remote_pg = array_name + ":" + module.params['pgroup']
    targets = get_targets(array)
    for target in targets:
        remote_pgs = array.list_pgroups(pending=True, on=target)
        for rpg in range(0, len(remote_pgs)):
            if remote_pg == remote_pgs[rpg]['name']:
                return target
    return None


def make_pgroup(module, array):
    """ Create Protection Group"""
    changed = False
    if module.params['target']:
        api_version = array._list_available_rest_versions()
        connected_targets = []
        connected_arrays = get_arrays(array)
        if OFFLOAD_API_VERSION in api_version:
            connected_targets = get_targets(array)
            offload_name = check_pg_on_offload(module, array)
            if offload_name and offload_name in module.params['target'][0:4]:
                module.fail_json(msg='Protection Group {0} already exists on offload target {1}.'.format(module.params['pgroup'], offload_name))

        connected_arrays = connected_arrays + connected_targets
        if connected_arrays == []:
            module.fail_json(msg='No connected targets on source array.')
        if set(module.params['target'][0:4]).issubset(connected_arrays):
            try:
                array.create_pgroup(module.params['pgroup'], targetlist=module.params['target'][0:4])
            except Exception:
                module.fail_json(msg='Creation of replicated pgroup {0} failed. {1}'.format(module.params['pgroup'], module.params['target'][0:4]))
        else:
            module.fail_json(msg='Check all selected targets are connected to the source array.')
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
        api_version = array._list_available_rest_versions()
        connected_targets = []
        connected_arrays = get_arrays(array)

        if OFFLOAD_API_VERSION in api_version:
            connected_targets = get_targets(array)
            offload_name = check_pg_on_offload(module, array)
            if offload_name and offload_name in module.params['target'][0:4]:
                module.fail_json(msg='Protection Group {0} already exists on offload target {1}.'.format(module.params['pgroup'], offload_name))

        connected_arrays = connected_arrays + connected_targets
        if connected_arrays == []:
            module.fail_json(msg='No targets connected to source array.')
        current_connects = array.get_pgroup(module.params['pgroup'])['targets']
        current_targets = []

        if current_connects:
            for targetcnt in range(0, len(current_connects)):
                current_targets.append(current_connects[targetcnt]['name'])

        if set(module.params['target'][0:4]) != set(current_targets):
            if not set(module.params['target'][0:4]).issubset(connected_arrays):
                module.fail_json(msg='Check all selected targets are connected to the source array.')
            try:
                array.set_pgroup(module.params['pgroup'], targetlist=module.params['target'][0:4])
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


def eradicate_pgroup(module, array):
    """ Eradicate Protection Group"""
    changed = False
    if ":" in module.params['pgroup']:
        try:
            target = ''.join(module.params['target'])
            array.destroy_pgroup(module.params['pgroup'], on=target, eradicate=True)
            changed = True
        except Exception:
            module.fail_json(msg='Eradicating pgroup {0} failed.'.format(module.params['pgroup']))
    else:
        try:
            array.destroy_pgroup(module.params['pgroup'], eradicate=True)
            changed = True
        except Exception:
            module.fail_json(msg='Eradicating pgroup {0} failed.'.format(module.params['pgroup']))
    module.exit_json(changed=changed)


def delete_pgroup(module, array):
    """ Delete Protection Group"""
    changed = False
    if ":" in module.params['pgroup']:
        try:
            target = ''.join(module.params['target'])
            array.destroy_pgroup(module.params['pgroup'], on=target)
            changed = True
        except Exception:
            module.fail_json(msg='Deleting pgroup {0} failed.'.format(module.params['pgroup']))
    else:
        try:
            array.destroy_pgroup(module.params['pgroup'])
            changed = True
        except Exception:
            module.fail_json(msg='Deleting pgroup {0} failed.'.format(module.params['pgroup']))
    if module.params['eradicate']:
        eradicate_pgroup(module, array)

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
    api_version = array._list_available_rest_versions()
    if ":" in module.params['pgroup'] and OFFLOAD_API_VERSION not in api_version:
        module.fail_json(msg='API version does not support offload protection groups.')

    pgroup = get_pgroup(module, array)
    xpgroup = get_pending_pgroup(module, array)

    if module.params['host']:
        try:
            for hst in module.params['host']:
                array.get_host(hst)
        except Exception:
            module.fail_json(msg='Host {0} not found'.format(hst))

    if module.params['hostgroup']:
        try:
            for hstg in module.params['hostgroup']:
                array.get_hgroup(hstg)
        except Exception:
            module.fail_json(msg='Hostgroup {0} not found'.format(hstg))

    if pgroup and state == 'present':
        update_pgroup(module, array)
    elif pgroup and state == 'absent':
        delete_pgroup(module, array)
    elif xpgroup and state == 'absent' and module.params['eradicate']:
        eradicate_pgroup(module, array)
    elif not pgroup and not xpgroup and state == 'present':
        make_pgroup(module, array)
    elif pgroup is None and state == 'absent':
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
