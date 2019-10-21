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
module: purefa_host
version_added: '2.4'
short_description: Manage hosts on Pure Storage FlashArrays
description:
- Create, delete or modify hosts on Pure Storage FlashArrays.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
notes:
- If specifying C(lun) option ensure host support requested value
options:
  host:
    description:
    - The name of the host.
    type: str
    required: true
  state:
    description:
    - Define whether the host should exist or not.
    - When removing host all connected volumes will be disconnected.
    type: str
    default: present
    choices: [ absent, present ]
  protocol:
    description:
    - Defines the host connection protocol for volumes.
    type: str
    default: iscsi
    choices: [ fc, iscsi, nvme, mixed ]
  wwns:
    type: list
    description:
    - List of wwns of the host if protocol is fc or mixed.
  iqn:
    type: list
    description:
    - List of IQNs of the host if protocol is iscsi or mixed.
  nqn:
    type: list
    description:
    - List of NQNs of the host if protocol is nvme or mixed.
    version_added: '2.8'
  volume:
    type: str
    description:
    - Volume name to map to the host.
  lun:
    description:
    - LUN ID to assign to volume for host. Must be unique.
    - If not provided the ID will be automatically assigned.
    - Range for LUN ID is 1 to 4095.
    type: int
    version_added: '2.8'
  personality:
    type: str
    description:
    - Define which operating system the host is. Recommended for
      ActiveCluster integration.
    default: ''
    choices: ['hpux', 'vms', 'aix', 'esxi', 'solaris', 'hitachi-vsp', 'oracle-vm-server', 'delete', '']
    version_added: '2.7'
  preferred_array:
    type: list
    description:
    - List of preferred arrays in an ActiveCluster environment.
    - To remove existing preferred arrays from the host, specify I(delete).
    version_added: '2.9'
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create new AIX host
  purefa_host:
    host: foo
    personaility: aix
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete host
  purefa_host:
    host: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: absent

- name: Make host bar with wwn ports
  purefa_host:
    host: bar
    protocol: fc
    wwns:
    - 00:00:00:00:00:00:00
    - 11:11:11:11:11:11:11
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Make host bar with iSCSI ports
  purefa_host:
    host: bar
    protocol: iscsi
    iqn:
    - iqn.1994-05.com.redhat:7d366003913
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Make host bar with NVMe ports
  purefa_host:
    host: bar
    protocol: nvme
    nqn:
    - nqn.2014-08.com.vendor:nvme:nvm-subsystem-sn-d78432
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Make mixed protocol host
  purefa_host:
    host: bar
    protocol: mixed
    nqn:
    - nqn.2014-08.com.vendor:nvme:nvm-subsystem-sn-d78432
    iqn:
    - iqn.1994-05.com.redhat:7d366003914
    wwns:
    - 00:00:00:00:00:00:01
    - 11:11:11:11:11:11:12
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Map host foo to volume bar as LUN ID 12
  purefa_host:
    host: foo
    volume: bar
    lun: 12
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Add preferred arrays to host foo
  purefa_host:
    host: foo
    preferred_array:
    - array1
    - array2
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete preferred arrays from host foo
  purefa_host:
    host: foo
    preferred_array: delete
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


AC_REQUIRED_API_VERSION = '1.14'
PREFERRED_ARRAY_API_VERSION = '1.15'
NVME_API_VERSION = '1.16'


def _is_cbs(module, array, is_cbs=False):
    """Is the selected array a Cloud Block Store"""
    model = ''
    ct0_model = array.get_hardware('CT0')['model']
    if ct0_model:
        model = ct0_model
    else:
        ct1_model = array.get_hardware('CT1')['model']
        model = ct1_model
    if 'CBS' in model:
        is_cbs = True
    return is_cbs


def _set_host_initiators(module, array):
    """Set host initiators."""
    if module.params['protocol'] in ['nvme', 'mixed']:
        if module.params['nqn']:
            try:
                array.set_host(module.params['host'],
                               nqnlist=module.params['nqn'])
            except Exception:
                module.fail_json(msg='Setting of NVMe NQN failed.')
    if module.params['protocol'] in ['iscsi', 'mixed']:
        if module.params['iqn']:
            try:
                array.set_host(module.params['host'],
                               iqnlist=module.params['iqn'])
            except Exception:
                module.fail_json(msg='Setting of iSCSI IQN failed.')
    if module.params['protocol'] in ['fc', 'mixed']:
        if module.params['wwns']:
            try:
                array.set_host(module.params['host'],
                               wwnlist=module.params['wwns'])
            except Exception:
                module.fail_json(msg='Setting of FC WWNs failed.')


def _update_host_initiators(module, array, answer=False):
    """Change host initiator if iscsi or nvme or add new FC WWNs"""
    if module.params['protocol'] in ['nvme', 'mixed']:
        if module.params['nqn']:
            current_nqn = array.get_host(module.params['host'])['nqn']
            if current_nqn != module.params['nqn']:
                try:
                    array.set_host(module.params['host'],
                                   nqnlist=module.params['nqn'])
                    answer = True
                except Exception:
                    module.fail_json(msg='Change of NVMe NQN failed.')
    if module.params['protocol'] in ['iscsi', 'mixed']:
        if module.params['iqn']:
            current_iqn = array.get_host(module.params['host'])['iqn']
            if current_iqn != module.params['iqn']:
                try:
                    array.set_host(module.params['host'],
                                   iqnlist=module.params['iqn'])
                    answer = True
                except Exception:
                    module.fail_json(msg='Change of iSCSI IQN failed.')
    if module.params['protocol'] in ['fc', 'mixed']:
        if module.params['wwns']:
            module.params['wwns'] = [wwn.replace(':', '') for wwn in module.params['wwns']]
            module.params['wwns'] = [wwn.upper() for wwn in module.params['wwns']]
            current_wwn = array.get_host(module.params['host'])['wwn']
            if current_wwn != module.params['wwns']:
                try:
                    array.set_host(module.params['host'],
                                   wwnlist=module.params['wwns'])
                    answer = True
                except Exception:
                    module.fail_json(msg='FC WWN change failed.')
    return answer


def _connect_new_volume(module, array, answer=False):
    """Connect volume to host"""
    api_version = array._list_available_rest_versions()
    if AC_REQUIRED_API_VERSION in api_version and module.params['lun']:
        try:
            array.connect_host(module.params['host'],
                               module.params['volume'],
                               lun=module.params['lun'])
            answer = True
        except Exception:
            module.fail_json(msg='LUN ID {0} invalid. Check for duplicate LUN IDs.'.format(module.params['lun']))
    else:
        array.connect_host(module.params['host'], module.params['volume'])
        answer = True
    return answer


def _set_host_personality(module, array):
    """Set host personality. Only called when supported"""
    if module.params['personality'] != 'delete':
        array.set_host(module.params['host'],
                       personality=module.params['personality'])
    else:
        array.set_host(module.params['host'], personality='')


def _set_preferred_array(module, array):
    """Set preferred array list. Only called when supported"""
    if module.params['preferred_array'] != ['delete']:
        array.set_host(module.params['host'],
                       preferred_array=module.params['preferred_array'])
    else:
        array.set_host(module.params['host'], personality='')


def _update_host_personality(module, array, answer=False):
    """Change host personality. Only called when supported"""
    personality = array.get_host(module.params['host'], personality=True)['personality']
    if personality is None and module.params['personality'] != 'delete':
        try:
            array.set_host(module.params['host'],
                           personality=module.params['personality'])
            answer = True
        except Exception:
            module.fail_json(msg='Personality setting failed.')
    if personality is not None:
        if module.params['personality'] == 'delete':
            try:
                array.set_host(module.params['host'], personality='')
                answer = True
            except Exception:
                module.fail_json(msg='Personality deletion failed.')
        elif personality != module.params['personality']:
            try:
                array.set_host(module.params['host'],
                               personality=module.params['personality'])
                answer = True
            except Exception:
                module.fail_json(msg='Personality change failed.')
    return answer


def _update_preferred_array(module, array, answer=False):
    """Update existing preferred array list. Only called when supported"""
    preferred_array = array.get_host(module.params['host'], preferred_array=True)['preferred_array']
    if preferred_array == [] and module.params['preferred_array'] != ['delete']:
        try:
            array.set_host(module.params['host'],
                           preferred_array=module.params['preferred_array'])
            answer = True
        except Exception:
            module.fail_json(msg='Preferred array list creation failed for {0}.'.format(module.params['host']))
    elif preferred_array != []:
        if module.params['preferred_array'] == ['delete']:
            try:
                array.set_host(module.params['host'], preferred_array=[])
                answer = True
            except Exception:
                module.fail_json(msg='Preferred array list deletion failed for {0}.'.format(module.params['host']))
        elif preferred_array != module.params['preferred_array']:
            try:
                array.set_host(module.params['host'],
                               preferred_array=module.params['preferred_array'])
                answer = True
            except Exception:
                module.fail_json(msg='Preferred array list change failed for {0}.'.format(module.params['host']))
    return answer


def get_host(module, array):
    host = None
    for hst in array.list_hosts():
        if hst["name"] == module.params['host']:
            host = hst
            break
    return host


def make_host(module, array):
    changed = True
    if not module.check_mode:
        try:
            array.create_host(module.params['host'])
        except Exception:
            module.fail_json(msg='Host {0} creation failed.'.format(module.params['host']))
        try:
            _set_host_initiators(module, array)
            api_version = array._list_available_rest_versions()
            if AC_REQUIRED_API_VERSION in api_version and module.params['personality']:
                _set_host_personality(module, array)
            if PREFERRED_ARRAY_API_VERSION in api_version and module.params['preferred_array']:
                _set_preferred_array(module, array)
            if module.params['volume']:
                if module.params['lun']:
                    array.connect_host(module.params['host'],
                                       module.params['volume'],
                                       lun=module.params['lun'])
                else:
                    array.connect_host(module.params['host'], module.params['volume'])
        except Exception:
            module.fail_json(msg='Host {0} configuration failed.'.format(module.params['host']))
    module.exit_json(changed=changed)


def update_host(module, array):
    changed = True
    if not module.check_mode:
        init_changed = vol_changed = pers_changed = pref_changed = False
        volumes = array.list_host_connections(module.params['host'])
        if module.params['iqn'] or module.params['wwns'] or module.params['nqn']:
            init_changed = _update_host_initiators(module, array)
        if module.params['volume']:
            current_vols = [vol['vol'] for vol in volumes]
            if not module.params['volume'] in current_vols:
                vol_changed = _connect_new_volume(module, array)
        api_version = array._list_available_rest_versions()
        if AC_REQUIRED_API_VERSION in api_version:
            if module.params['personality']:
                pers_changed = _update_host_personality(module, array)
        if PREFERRED_ARRAY_API_VERSION in api_version:
            if module.params['preferred_array']:
                pref_changed = _update_preferred_array(module, array)
        changed = init_changed or vol_changed or pers_changed or pref_changed
    module.exit_json(changed=changed)


def delete_host(module, array):
    changed = True
    if not module.check_mode:
        try:
            for vol in array.list_host_connections(module.params['host']):
                array.disconnect_host(module.params['host'], vol["vol"])
            array.delete_host(module.params['host'])
        except Exception:
            module.fail_json(msg='Host {0} deletion failed'.format(module.params['host']))
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        host=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        protocol=dict(type='str', default='iscsi', choices=['fc', 'iscsi', 'nvme', 'mixed']),
        nqn=dict(type='list'),
        iqn=dict(type='list'),
        wwns=dict(type='list'),
        volume=dict(type='str'),
        lun=dict(type='int'),
        personality=dict(type='str', default='',
                         choices=['hpux', 'vms', 'aix', 'esxi', 'solaris',
                                  'hitachi-vsp', 'oracle-vm-server', 'delete', '']),
        preferred_array=dict(type='list'),
    ))

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    array = get_system(module)
    if _is_cbs(module, array) and module.params['wwns'] or module.params['nqn']:
        module.fail_json(msg='Cloud block Store only support iSCSI as a protocol')
    api_version = array._list_available_rest_versions()
    if module.params['nqn'] is not None and NVME_API_VERSION not in api_version:
        module.fail_json(msg='NVMe protocol not supported. Please upgrade your array.')
    state = module.params['state']
    host = get_host(module, array)
    if module.params['lun'] and not 1 <= module.params['lun'] <= 4095:
        module.fail_json(msg='LUN ID of {0} is out of range (1 to 4095)'.format(module.params['lun']))
    if module.params['volume']:
        try:
            array.get_volume(module.params['volume'])
        except Exception:
            module.fail_json(msg='Volume {0} not found'.format(module.params['volume']))
    if module.params['preferred_array']:
        try:
            if module.params['preferred_array'] != ['delete']:
                all_connected_arrays = array.list_array_connections()
                if not all_connected_arrays:
                    module.fail_json(msg='No target arrays connected to source array. Setting preferred arrays not possible.')
                else:
                    current_arrays = []
                    for current_array in range(0, len(all_connected_arrays)):
                        current_arrays.append(all_connected_arrays[current_array]['array_name'])
                for array_to_connect in range(0, len(module.params['preferred_array'])):
                    if module.params['preferred_array'][array_to_connect] not in current_arrays:
                        module.fail_json(msg='Array {0} not in existing array connections.'.format(module.params['preferred_array'][array_to_connect]))
        except Exception:
            module.fail_json(msg='Failed to get existing array connections.')

    if host is None and state == 'present':
        make_host(module, array)
    elif host and state == 'present':
        update_host(module, array)
    elif host and state == 'absent':
        delete_host(module, array)
    elif host is None and state == 'absent':
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
