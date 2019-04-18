#!/usr/bin/python

# Copyright: (c) 2019, Konrad D. Pisarczyk
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
        type: string
    password:
        description:
            - Password used for API authentication (API key).
        type: string
    name:
        description:
            - Name of the instance to be created.
            - Required for I(state=present).
        type: string
    state:
        description:
            - Specify whether instance should be in.
            - If I(state=absent) and instance exists, it will be removed (along with its drives).
            - If I(state=absent) and instance does not exist, the module returns successfully with no changes.
        choices:
            - present
            - absent
        default: present
    uuid:
        description:
            - The UUID of the instance to destroy.
            - Required when I(state=absent).
        type: string
notes:
    - If not supplied to the module, the environment variables C(EHUSER) and C(EHPASS) will be used for authentication, where the C(EHUSER) is the user id, and C(EHPASS) is the API key.
    - Supply auth via environment variables with, for example, C(export EHUSER=123-456-789) and C(export EHPASS=abcdef).
    - See U(https://gitlab.com/konradp/pyeh) and U(https://pypi.org/project/pyeh/) for the C(pyeh) module.
    - See U(https://www.elastichosts.com/api/docs/) for ElasticHosts API reference.
requirements:
    - pyeh
'''

EXAMPLES = '''
# Note: These examples do not set authentication details. See the note below for details.

# Create an instance
- name: Create an instance
  eh_instance:
    name: somename
    state: present

# Destroy an instance (poweroff and delete)
- name: Destroy an instance
  eh_instance:
    uuid: "1da3a8ff-5bb4-4c6f-9413-4fbab7a5dba1"
    state: absent
    force: true

# A minimal playbook which: creates an instance, runs a task on it, destroys the instance
- name: Create instance
  hosts: localhost
  tasks:
  - name: Create instance
    eh_instance:
      name: machine19
    register: instance_info
  - debug:
      var: instance_info
  - add_host:
      hostname: instance
      ansible_host: "{{ instance_info.instance.ip }}"
      ansible_user: root

- name: Work on instance
  hosts: instance
  gather_facts: no
  tasks:
  - wait_for_connection:
      timeout: 20
  - setup:
  - command: uname -a
    register: p
  - debug:
      var: p

- name: Destroy instance
  hosts: localhost
  tasks:
  - debug:
      var: instance_info
  - name: Destroy instance
    eh_instance:
      uuid: "{{ instance_info.instance.uuid }}"
      state: absent
      force: true
'''

RETURN = r'''
instance:
    cpu: 500,
    disk: 09876543-a123-1234-1234-123456789012
    ip: 1.2.3.4,
    name: instancename,
    persistent: true,
    status: active,
    type: container,
    uuid: 1234567b-a123-1234-1234-123456789012
'''

# Imports
from ansible.module_utils.basic import AnsibleModule
import os
import time

# Prerequisites
try:
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
                    'absent'
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

    instance = {}
    if state == 'present':
        # Create instance
        instance.update(
            name=module.params['name']
        )
        if module.check_mode:
            result.update(
                changed=True,
                instance=instance
            )
            module.exit_json(**result)
        instance = client.create_instance(instance)
        result.update(
            instance=instance,
            changed=True
        )
        module.exit_json(**result)
    elif state == 'absent':
        # Destroy instance
        if module.params['uuid'] is None:
            module.fail_json(msg='uuid is not set')
        if module.check_mode:
            # Check
            result.update(changed=True)
            module.exit_json(**result)

        # Get instance
        uuid = module.params['uuid']
        instance = client.get_instance(uuid)
        if instance is None:
            # Already absent, no change
            result.update(changed=False)
            module.exit_json(**result)
        if instance['status'] == 'active':
            # Active
            if module.params['force']:
                if instance['persistent'] == 'false':
                    client.stop_instance(uuid, graceful=True)
                else:
                    # Persistent, graceful shutdown
                    if not client.stop_instance(uuid, graceful=True):
                        module.fail_json(msg=('Could not shutdown instance'))
            else:
                module.fail_json(msg=(
                    'Instance is active, cannot delete. '
                    'Use force=true to force.'
                ))

        if instance['persistent'] == 'true':
            client.delete_instance(uuid)
        client.delete_disk(instance['disk'])
        result.update(
            changed=True
        )
        module.exit_json(**result)

if __name__ == '__main__':
    main()
