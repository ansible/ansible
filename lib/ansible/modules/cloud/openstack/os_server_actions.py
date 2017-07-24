#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2015, Jesse Keating <jlk@derpops.bike>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_server_actions
short_description: Perform actions on Compute Instances from OpenStack
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Jesse Keating (@j2sol)"
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
     required: false
     default: 'yes'
   timeout:
     description:
        - The amount of time the module should wait for the instance to perform
          the requested action.
     required: false
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
     default: null
     version_added: "2.3"
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Pauses a compute instance
- os_server_actions:
       action: pause
       auth:
         auth_url: https://mycloud.openstack.blueboxgrid.com:5001/v2.0
         username: admin
         password: admin
         project_name: admin
       server: vm1
       timeout: 200
'''

try:
    import shade
    from shade import meta
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs


_action_map = {'stop': 'SHUTOFF',
               'start': 'ACTIVE',
               'pause': 'PAUSED',
               'unpause': 'ACTIVE',
               'lock': 'ACTIVE', # API doesn't show lock/unlock status
               'unlock': 'ACTIVE',
               'suspend': 'SUSPENDED',
               'resume': 'ACTIVE',
               'rebuild': 'ACTIVE'}

_admin_actions = ['pause', 'unpause', 'suspend', 'resume', 'lock', 'unlock']

def _wait(timeout, cloud, server, action, module):
    """Wait for the server to reach the desired state for the given action."""

    for count in shade._utils._iterate_timeout(
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

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    action = module.params['action']
    wait = module.params['wait']
    timeout = module.params['timeout']
    image = module.params['image']

    try:
        if action in _admin_actions:
            cloud = shade.operator_cloud(**module.params)
        else:
            cloud = shade.openstack_cloud(**module.params)
        server = cloud.get_server(module.params['server'])
        if not server:
            module.fail_json(msg='Could not find server %s' % server)
        status = server.status

        if module.check_mode:
            module.exit_json(changed=_system_state_change(action, status))

        if action == 'stop':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.nova_client.servers.stop(server=server.id)
            if wait:
                _wait(timeout, cloud, server, action, module)
                module.exit_json(changed=True)

        if action == 'start':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.nova_client.servers.start(server=server.id)
            if wait:
                _wait(timeout, cloud, server, action, module)
                module.exit_json(changed=True)

        if action == 'pause':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.nova_client.servers.pause(server=server.id)
            if wait:
                _wait(timeout, cloud, server, action, module)
                module.exit_json(changed=True)

        elif action == 'unpause':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.nova_client.servers.unpause(server=server.id)
            if wait:
                _wait(timeout, cloud, server, action, module)
            module.exit_json(changed=True)

        elif action == 'lock':
            # lock doesn't set a state, just do it
            cloud.nova_client.servers.lock(server=server.id)
            module.exit_json(changed=True)

        elif action == 'unlock':
            # unlock doesn't set a state, just do it
            cloud.nova_client.servers.unlock(server=server.id)
            module.exit_json(changed=True)

        elif action == 'suspend':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.nova_client.servers.suspend(server=server.id)
            if wait:
                _wait(timeout, cloud, server, action, module)
            module.exit_json(changed=True)

        elif action == 'resume':
            if not _system_state_change(action, status):
                module.exit_json(changed=False)

            cloud.nova_client.servers.resume(server=server.id)
            if wait:
                _wait(timeout, cloud, server, action, module)
            module.exit_json(changed=True)

        elif action == 'rebuild':
            image = cloud.get_image(image)

            if image is None:
                module.fail_json(msg="Image does not exist")

            # rebuild doesn't set a state, just do it
            cloud.nova_client.servers.rebuild(server=server.id, image=image.id)
            if wait:
                _wait(timeout, cloud, server, action, module)
            module.exit_json(changed=True)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == '__main__':
    main()
