#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2015, Jesse Keating <jlk@derpops.bike>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_server_action
short_description: Perform actions on Compute Instances from OpenStack
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Jesse Keating (@omgjlk)"
description:
   - Perform server actions on an existing compute instance from OpenStack.
     This module does not return any data other than changed true/false.
     When I(action) is 'rebuild', then I(image) parameter is required.
options:
   server:
     description:
        - Name or ID of the instance
     required: true
   wait:
     description:
        - If the module should wait for the instance action to be performed.
     type: bool
     default: 'yes'
   timeout:
     description:
        - The amount of time the module should wait for the instance to perform
          the requested action.
     default: 180
   action:
     description:
       - Perform the given action. The lock and unlock actions always return
         changed as the servers API does not provide lock status.
     choices: [stop, start, pause, unpause, lock, unlock, suspend, resume,
               rebuild]
     default: present
   image:
     description:
       - Image the server should be rebuilt with
     version_added: "2.3"
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''

EXAMPLES = '''
# Pauses a compute instance
- os_server_action:
      action: pause
      auth:
        auth_url: https://identity.example.com
        username: admin
        password: admin
        project_name: admin
      server: vm1
      timeout: 200
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module

_action_map = {'stop': 'SHUTOFF',
               'start': 'ACTIVE',
               'pause': 'PAUSED',
               'unpause': 'ACTIVE',
               'lock': 'ACTIVE',  # API doesn't show lock/unlock status
               'unlock': 'ACTIVE',
               'suspend': 'SUSPENDED',
               'resume': 'ACTIVE',
               'rebuild': 'ACTIVE'}

_admin_actions = ['pause', 'unpause', 'suspend', 'resume', 'lock', 'unlock']


def _action_url(server_id):
    return '/servers/{server_id}/action'.format(server_id=server_id)


def _wait(timeout, cloud, server, action, module, sdk):
    """Wait for the server to reach the desired state for the given action."""

    for count in sdk.utils.iterate_timeout(
            timeout,
            "Timeout waiting for server to complete %s" % action):
        try:
            server = cloud.get_server(server.id)
        except Exception:
            continue

        if server.status == _action_map[action]:
            return

        if server.status == 'ERROR':
            module.fail_json(msg="Server reached ERROR state while attempting to %s" % action)


def _system_state_change(action, status):
    """Check if system state would change."""
    if status == _action_map[action]:
        return False
    return True


def main():
    argument_spec = openstack_full_argument_spec(
        server=dict(required=True),
        action=dict(required=True, choices=['stop', 'start', 'pause', 'unpause',
                                            'lock', 'unlock', 'suspend', 'resume',
                                            'rebuild']),
        image=dict(required=False),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, supports_check_mode=True,
                           required_if=[('action', 'rebuild', ['image'])],
                           **module_kwargs)

    if module._name == 'os_server_actions':
        module.deprecate("The 'os_server_actions' module is being renamed 'os_server_action'", version=2.8)

    action = module.params['action']
    wait = module.params['wait']
    timeout = module.params['timeout']
    image = module.params['image']

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        server = cloud.get_server(module.params['server'])
        if not server:
            module.fail_json(msg='Could not find server %s' % server)
        status = server.status

        if module.check_mode:
            module.exit_json(changed=_system_state_change(action, status))

        if action == 'stop':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.compute.post(
                _action_url(server.id),
                json={'os-stop': None})
            if wait:
                _wait(timeout, cloud, server, action, module, sdk)
                module.exit_json(changed=True)

        if action == 'start':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.compute.post(
                _action_url(server.id),
                json={'os-start': None})
            if wait:
                _wait(timeout, cloud, server, action, module, sdk)
                module.exit_json(changed=True)

        if action == 'pause':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.compute.post(
                _action_url(server.id),
                json={'pause': None})
            if wait:
                _wait(timeout, cloud, server, action, module, sdk)
                module.exit_json(changed=True)

        elif action == 'unpause':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.compute.post(
                _action_url(server.id),
                json={'unpause': None})
            if wait:
                _wait(timeout, cloud, server, action, module, sdk)
            module.exit_json(changed=True)

        elif action == 'lock':
            # lock doesn't set a state, just do it
            cloud.compute.post(
                _action_url(server.id),
                json={'lock': None})
            module.exit_json(changed=True)

        elif action == 'unlock':
            # unlock doesn't set a state, just do it
            cloud.compute.post(
                _action_url(server.id),
                json={'unlock': None})
            module.exit_json(changed=True)

        elif action == 'suspend':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.compute.post(
                _action_url(server.id),
                json={'suspend': None})
            if wait:
                _wait(timeout, cloud, server, action, module, sdk)
            module.exit_json(changed=True)

        elif action == 'resume':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.compute.post(
                _action_url(server.id),
                json={'resume': None})
            if wait:
                _wait(timeout, cloud, server, action, module, sdk)
            module.exit_json(changed=True)

        elif action == 'rebuild':
            image = cloud.get_image(image)

            if image is None:
                module.fail_json(msg="Image does not exist")

            # rebuild doesn't set a state, just do it
            cloud.compute.post(
                _action_url(server.id),
                json={'rebuild': None})
            if wait:
                _wait(timeout, cloud, server, action, module, sdk)
            module.exit_json(changed=True)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == '__main__':
    main()
