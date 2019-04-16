#!/usr/bin/python

# Copyright: (c) 2019, Ansible Project

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'
}

DOCUMENTATION ='''
---
module: eh_instance
short_description: Create or remove ElasticHosts instances (container or VM)
description:
    - Create or remove a container or a VM on ElasticHosts platfom.
    - Supports C(check_mode).
version_added: "2.7"
author: "Konrad Pisarczyk (@nickyfow)"
options:
    force:
        description:
            - Ignore warnings and complete actions.
            - If C(yes) is used with C(state=absent), the instance will be destroyed even if it is powered on.
            - If C(no) is used with C(state=absent), the modle will fail on powered-on instances.
        type: bool
        default: no
    username:
        description:
            - User name used for API authentication (user UUID).
        type: str
    password:
        description:
            - Password used for API authentication (API key).
    name:
        description:
            - Name of the instance to be created
            - Required for C(state=present)
    state:
        description:
            - Specify whether instance should be in.
            - If C(state=absent) and instance exists, it will be removed (along with its drives).
            - If C(state=absent) and instance does not exist, the module returns successfully with no changes.
        choices:
          - present
          - absent
        default: present
    uuid:
      description:
          - The UUID of the instance to destroy.
          - Required when C(state=absent).
      type: str
notes:
    - If not supplied to the module, the environment variables C(EHUSER) and C(EHPASS) will be used for authentication.
    - See U(https://gitlab.com/konradp/pyeh) and U(https://pypi.org/project/pyeh/) for the C(pyeh) module.
    - See U(https://www.elastichosts.com/api/docs/) for ElasticHosts API reference.
requirements:
    - pyeh
'''

EXAMPLES = '''
# Note: These examples do not set authentication details. See the note below for details.

# Create an instance
- eh_instance:
    name: somename
    state: present

# Destroy an instance (poweroff and delete)
- eh_instance:
    uuid: "51eff35b-b044-4544-b202-f37557d4d932"
    state: absent
    force: true
'''

RETURN = r'''
instance:
    cpu: 500,
    disk: "1da3a8ff-5bb4-4c6f-9413-4fbab7a5dba1",
    ip: "5.152.176.139",
    name: "machine19",
    persistent: "true",
    status: "active",
    type: "container",
    uuid: "51eff35b-b044-4544-b202-f37557d4d932"
'''

# Imports
from ansible.module_utils.basic import AnsibleModule
import os
import time

# Prerequisites
try:
    #import pyeh
    from pyeh.main import Client
    HAS_PYEH = True
except Exception:
    HAS_PYEH = False


def main():
    module = AnsibleModule(
        argument_spec = dict(
            force = dict(
                type='bool',
                default=False,
            ),
            name=dict(type='str'),
            password = dict(
                type='str',
                no_log=True,
                default=os.environ.get('EHPASS'),
            ),
            state=dict(
                required=False,
                choices=[
                    'present',
                    'absent',
                    'restarted'
                ],
                default='present'
            ),
            username = dict(
                type='str',
                default=os.environ.get('EHUSER'),
                no_log=True,
            ),
            uuid = dict(type='str'),
        ),
        required_one_of=[
            ['name', 'uuid']
        ],
        supports_check_mode=True
    ) # Module

    # Check pyeh library
    if not HAS_PYEH:
        module.fail_json(msg='pyeh Python library required for this module')

    # Params
    debug = False
    username = module.params['username']
    password = module.params['password']
    state = module.params['state']
    if password is None:
        module.fail_json(msg='Password was not specified')
    if username is None:
        module.fail_json(msg='Username was not specified')

    result = { 'failed': False, 'changed': False }

    # Create EH client
    client = Client(
        zone='lon-b',
        user=username,
        pwd=password,
        debug=debug
    )

    node = {}
    if state == 'present':
        # Create node
        node.update(
          name=module.params['name']
        )
        if module.check_mode:
            result.update(
                changed=True,
                node=node
            )
            module.exit_json(**result)
        node = client.create_node(node)
        result.update(
          node=node,
          changed=True
        )
        module.exit_json(**result)
    elif state == 'absent':
        # Destroy node
        if module.params['uuid'] is None:
            module.fail_json(msg='uuid is not set')
        if module.check_mode:
            # Check
            result.update(changed=True)
            module.exit_json(**result)

        # Get node
        uuid = module.params['uuid']
        node = client.get_node(uuid)
        if node is None:
            # Already absent, no change
            result.update(changed=False)
            module.exit_json(**result)
        if node['status'] == 'active':
            # Active
            if module.params['force']:
                if node['persistent'] == 'false':
                    client.stop_node(uuid, graceful=True)
                else:
                    # Persistent, graceful shutdown
                    if not client.stop_node(uuid, graceful=True):
                        module.fail_json(msg=('Could not shutdown node'))
            else:
                module.fail_json(msg=(
                    'Node is active, cannot delete. '
                    'Use force=true to force.'
                ))

        if node['persistent'] == 'true':
            client.delete_node(uuid)
        client.delete_disk(node['disk'])
        result.update(changed=True)
        module.exit_json(**result)

if __name__ == '__main__':
    main()
