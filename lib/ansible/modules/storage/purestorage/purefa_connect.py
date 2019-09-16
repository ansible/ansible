#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_connect
version_added: '2.9'
short_description: Manage replication connections between two FlashArrays
description:
- Manage array connections to specified target array
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Create or delete array connection
    default: present
    type: str
    choices: [ absent, present ]
  target_url:
    description:
    - Management IP address of remote array.
    type: str
    required: true
  target_api:
    description:
    - API token for target array
    type: str
  connection:
    description: Type of connection between arrays.
    type: str
    choices: [ sync, async ]
    default: async
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create an async connection to remote array
  purefa_connect:
    target_url: 10.10.10.20
    target_api:
    connection: async
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete connection to remote array
  purefa_connect:
    state: absent
    target_url: 10.10.10.20
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

'''

RETURN = r'''
'''

HAS_PURESTORAGE = True
try:
    from purestorage import FlashArray
except ImportError:
    HAS_PURESTORAGE = False

import platform
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def _check_connected(module, array):
    connected_arrays = array.list_array_connections()
    for target in range(0, len(connected_arrays)):
        if connected_arrays[target]['management_address'] == module.params['target_url'] and \
           connected_arrays[target]['connected']:
            return connected_arrays[target]
    return None


def break_connection(module, array, target_array):
    """Break connection between arrays"""
    changed = True
    if not module.check_mode:
        source_array = array.get()['array_name']
        try:
            array.disconnect_array(target_array['array_name'])
        except Exception:
            module.fail_json(msg="Failed to disconnect {0} from {1}.".format(target_array['array_name'], source_array))
    module.exit_json(changed=changed)


def create_connection(module, array):
    """Create connection between arrays"""
    changed = True
    if not module.check_mode:
        remote_array = module.params['target_url']
        user_agent = '%(base)s %(class)s/%(version)s (%(platform)s)' % {
            'base': 'Ansible',
            'class': __name__,
            'version': 1.2,
            'platform': platform.platform()
        }
        try:
            remote_system = FlashArray(module.params['target_url'],
                                       api_token=module.params['target_api'],
                                       user_agent=user_agent)
            connection_key = remote_system.get(connection_key=True)['connection_key']
            remote_array = remote_system.get()['array_name']
            array.connect_array(module.params['target_url'], connection_key, [module.params['connection']])
        except Exception:
            module.fail_json(msg="Failed to connect to remote array {0}.".format(remote_array))
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        connection=dict(type='str', default='async', choices=['async', 'sync']),
        target_url=dict(type='str', required=True),
        target_api=dict(type='str'),
    ))

    required_if = [('state', 'present', ['target_api'])]

    module = AnsibleModule(argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    if not HAS_PURESTORAGE:
        module.fail_json(msg='purestorage sdk is required for this module')

    state = module.params['state']
    array = get_system(module)
    target_array = _check_connected(module, array)

    if state == 'present' and target_array is None:
        create_connection(module, array)
    elif state == 'absent'and target_array is not None:
        break_connection(module, array, target_array)

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
