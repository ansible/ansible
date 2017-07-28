#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: purefa_host
version_added: "2.4"
short_description: Create, Delete and Modify Hosts on Pure Storage FlashArray
description:
    - This module creates, deletes or modifies hosts on Pure Storage FlashArray.
author: Simon Dodsley (@simondodsley)
options:
  host:
    description:
      - Host Name
    required: true
  state:
    description:
      - Creates host.
      - When removing host all connected volumes will be disconnected.
    required: false
    default: present
    choices: [ "present", "absent" ]
  protocol:
    description:
      - Defines the host connection protocol for volumes.
    required: false
    default: iscsi
    choices: [ "iscsi", "fc" ]
  wwns:
    description:
      - List of wwns of the host if protocol is fc
    required: false
  iqn:
    description:
      - List of IQNs of the host if protocol is iscsi
    required: false
  volume:
    description:
      - Volume name to map to the host
    required: false
extends_documentation_fragment:
    - purestorage
'''

EXAMPLES = '''
- name: Create new new host
  purefa_host:
    host: foo
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete host
  purefa_host:
    host: foo
    state: absent
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Make sure host bar is available with wwn ports
  purefa_host:
    host: bar
    protocol: fc
    wwns:
      - "00:00:00:00:00:00:00"
      - "11:11:11:11:11:11:11"
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Make sure host bar is available with iSCSI ports
  purefa_host:
    host: bar
    protocol: iscsi
    iqn:
      - "iqn.1994-05.com.redhat:7d366003913"
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Map host foo to volume bar
  purefa_host:
    host: foo
    volume: bar
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


def get_host(module, array):

    host = None

    for h in array.list_hosts():
        if h["name"] == module.params['host']:
            host = h
            break

    return host


def make_host(module, array):

    changed = True

    if not module.check_mode:
        host = array.create_host(module.params['host'])
        if module.params['protocol'] == 'iscsi':
            if module.params['iqn']:
                array.set_host(module.params['host'], addiqnlist=module.params['iqn'])
        if module.params['protocol'] == 'fc':
            if module.params['wwns']:
                array.set_host(module.params['host'], addwwnlist=module.params['wwns'])
        if module.params['volume']:
            array.connect_host(module.params['host'], module.params['volume'])
    module.exit_json(changed=changed)


def update_host(module, array):
    changed = False
    host = module.params['host']
    module.exit_json(changed=changed)


def delete_host(module, array):
    changed = True
    if not module.check_mode:
        for vol in array.list_host_connections(module.params['host']):
            array.disconnect_host(module.params['host'], vol["vol"])
        array.delete_host(module.params['host'])
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(
        dict(
            host=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            protocol=dict(default='iscsi', choices=['iscsi', 'fc']),
            iqn=dict(type='list'),
            wwns=dict(type='list'),
            volume=dict()
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_PURESTORAGE:
        module.fail_json(msg='purestorage sdk is required for this module in host')

    state = module.params['state']
    protocol = module.params['protocol']
    array = get_system(module)
    host = get_host(module, array)

    if module.params['volume']:
        try:
            array.get_volume(module.params['volume'])
        except:
            module.fail_json(msg='Volume {} not found'.format(module.params['volume']))

    if host and state == 'present':
        update_host(module, array)
    elif host and state == 'absent':
        delete_host(module, array)
    elif host is None and state == 'absent':
        module.exit_json(changed=False)
    else:
        make_host(module, array)


if __name__ == '__main__':
    main()
