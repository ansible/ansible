#!/usr/bin/python
# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: tetration_user_annotations
version_added: "2.10"
author: Brandon Beck (@techbeck03)
description:
- Enables management of Cisco Tetration user annotations.
- Enables creation, modification, deletion, and query of annotations.
short_description: Manage tetration user annotations
extends_documentation_fragment: tetration
notes:
- Requires the tetpyclient Python module.
- Supports check mode.
options:
  annotations:
    description:
    - Dictionary containing annotation key/value pairs
    - Required if I(state=present)
    type: dict
  columns:
    description:
    - Dictionary containing annotation key/value pairs
    - Required if I(state=delete_columns)
    type: list
  ip:
    description:
    - IP or subnet address to associate with annotations
    - Required if I(state=present)
    - Required if I(state=absent)
    - Required if I(state=query)
    type: str
    version_added: "2.10"
  name:
    description: Name of the tenant
    required: true
    type: str
    aliases:
      - tenant
  state:
    choices:
      - present
      - absent
      - query
      - delete_columns
    default: present
    description: Add, change, clear, or delete columns from Tetration user annotations
    required: true
    type: str

'''

EXAMPLES = r'''
- name: Assign annotations to a single host
  tetration_user_annotations:
    name: Default
    ip: 172.16.1.10/32
    annotations:
      location: us-dc-01
      lifecycle: dev
      owner: user@company.com
    state: present
    provider:
      host: "tetration-cluster@company.com"
      api_key: 1234567890QWERTY
      api_secret: 1234567890QWERTY

- name: Assign annotations to a subnet
  tetration_user_annotations:
    name: Default
    ip: 172.16.1.0/24
    annotations:
      location: us-dc-01
      lifecycle: dev
      owner: user@company.com
    state: present
    provider:
      host: "tetration-cluster@company.com"
      api_key: 1234567890QWERTY
      api_secret: 1234567890QWERTY

- name: Remove annotations from a host
  tetration_user_annotations:
    name: Default
    ip: 172.16.1.10/32
    annotations:
      location: us-dc-01
      lifecycle: dev
      owner: user@company.com
    state: absent
    provider:
      host: "tetration-cluster@company.com"
      api_key: 1234567890QWERTY
      api_secret: 1234567890QWERTY

- name: Get annotations for target IP/subnet
  tetration_user_annotations:
    name: Default
    ip: 172.16.1.10/32
    state: query
    provider:
      host: "tetration-cluster@company.com"
      api_key: 1234567890QWERTY
      api_secret: 1234567890QWERTY

- name: Delete specific annotation columns
  tetration_user_annotations:
    name: Default
    state: delete_columns
    columns:
      - Unwanted Column 1
      - Unwanted Column 2
    provider:
      host: "tetration-cluster@company.com"
      api_key: 1234567890QWERTY
      api_secret: 1234567890QWERTY
'''

RETURN = r'''
---
object:
  description: a dict with key value pairs for each annotation associated with C(ip)
    when C(state) is present or query
  contains: dict
  returned: always
  type: complex
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems, iterkeys
from ansible.module_utils.network.tetration import TetrationApiModule
from ansible.module_utils.network.tetration import TETRATION_API_INVENTORY_TAG, TETRATION_COLUMN_NAMES


def main():
    ''' Main entry point for module execution
    '''
    # Module specific spec
    tetration_spec = dict(
        name=dict(type='str', required=False, aliases=['tenant']),
        ip=dict(type='str', required=False),
        annotations=dict(type='dict'),
        columns=dict(type='list', required=False)
    )
    # Common spec for tetration modules
    argument_spec = dict(
        provider=dict(required=True),
        state=dict(default='present', choices=['present', 'absent', 'query',
                                               'delete_columns'])
    )

    # Combine specs and include provider parameter
    argument_spec.update(tetration_spec)
    argument_spec.update(TetrationApiModule.provider_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['annotations', 'name', 'ip']],
            ['state', 'absent', ['name', 'ip']],
            ['state', 'query', ['name', 'ip']],
            ['state', 'delete_columns', ['name', 'columns']],
        ]
    )

    # These are all elements we put in our return JSON object for clarity
    tet_module = TetrationApiModule(module)
    result = dict(
        changed=False,
        object=None,
    )

    name = module.params.get('name')
    ip = module.params.get('ip')
    annotations = module.params.get('annotations')
    columns = module.params.get('columns')

    # Throw error if state is absent and annotations passed
    if module.params['state'] in 'absent' and 'annotations' in module.params and module.params['annotations']:
        module.fail_json(msg='annotations cannot be passed for state absent because all annotations are cleared')

    # =========================================================================
    # Get current state of the object
    query_result = tet_module.run_method(
        'get',
        target='%s/%s' % (TETRATION_API_INVENTORY_TAG, module.params['name']),
        params=dict(ip=module.params['ip']),
    )
    annotations = query_result if query_result else None

    # ---------------------------------
    # STATE == 'present'
    # ---------------------------------
    if module.params['state'] in 'present':
        result['changed'] = tet_module.filter_object(
            module.params['annotations'], annotations)
        if not result['changed']:
            result['object'] = annotations
            module.exit_json(**result)
        if not module.check_mode:
            tet_module.run_method(
                'post',
                target='%s/%s' % (TETRATION_API_INVENTORY_TAG, module.params['name']),
                req_payload=dict(ip=module.params['ip'],
                                 attributes=module.params['annotations'])
            )
        if annotations:
            annotations.update(module.params['annotations'])
        else:
            annotations = module.params['annotations']
        result['object'] = annotations
        module.exit_json(**result)
    # ---------------------------------
    # STATE == 'absent'
    # ---------------------------------
    elif module.params['state'] in 'absent':
        result['changed'] = True if annotations else False
        if not result['changed']:
            module.exit_json(**result)
        else:
            if not module.check_mode:
                tet_module.run_method(
                    'delete',
                    target='%s/%s' % (TETRATION_API_INVENTORY_TAG,
                                      module.params['name']),
                    req_payload=dict(
                        ip=module.params['ip']
                    )
                )
            module.exit_json(**result)
    # ---------------------------------
    # STATE == 'query'
    # ---------------------------------
    elif module.params['state'] == 'query':
        if annotations:
            result['object'] = annotations
        module.exit_json(**result)

    # ---------------------------------
    # STATE == 'delete_columns'
    # ---------------------------------
    elif module.params['state'] == 'delete_columns':
        for column in columns:
            tet_module.run_method(
                'delete',
                target='%s/%s/%s' % (TETRATION_COLUMN_NAMES, name, column),
            )
        module.exit_json(**result)


if __name__ == '__main__':
    main()
