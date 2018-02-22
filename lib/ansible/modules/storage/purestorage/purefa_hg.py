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
module: purefa_hg
version_added: '2.4'
short_description: Manage hostgroups on Pure Storage FlashArrays
description:
- Create, delete or modifiy hostgroups on Pure Storage FlashArrays.
author:
- Simon Dodsley (@sdodsley)
options:
  hostgroup:
    description:
    - The name of the hostgroup.
    required: true
  state:
    description:
    - Define whether the hostgroup should exist or not.
    default: present
    choices: [ absent, present ]
  host:
    description:
    - List of existing hosts to add to hostgroup.
  volume:
    description:
    - List of existing volumes to add to hostgroup.
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create new hostgroup
  purefa_hg:
    hostgroup: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

# This will disconnect all hosts and volumes in the hostgroup
- name: Delete hostgroup
  purefa_hg:
    hostgroup: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
    state: absent

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

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


try:
    from purestorage import purestorage
    HAS_PURESTORAGE = True
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
    argument_spec.update(dict(
        hostgroup=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        host=dict(type='list'),
        volume=dict(type='list'),
    ))

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
