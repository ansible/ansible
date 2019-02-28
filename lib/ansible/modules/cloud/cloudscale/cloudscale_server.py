#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# Copyright: (c) 2019, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudscale_server
short_description: Manages servers on the cloudscale.ch IaaS service
description:
  - Create, update, start, stop and delete servers on the cloudscale.ch IaaS service.
notes:
  - If more than one server with the name given by the I(name) option exists, execution is aborted.
  - Only the I(name) and I(flavor) are evaluated for the update.
  - The option I(force=true) must be given to allow the reboot of existing running servers for applying the changes.
version_added: '2.3'
author:
  - Gaudenz Steinlin (@gaudenz)
  - René Moser (@resmo)
options:
  state:
    description:
      - State of the server.
    choices: [ running, stopped, absent ]
    default: running
    type: str
  name:
    description:
      - Name of the Server.
      - Either I(name) or I(uuid) are required.
    type: str
  uuid:
    description:
      - UUID of the server.
      - Either I(name) or I(uuid) are required.
    type: str
  flavor:
    description:
      - Flavor of the server.
    type: str
  image:
    description:
      - Image used to create the server.
  volume_size_gb:
    description:
      - Size of the root volume in GB.
    default: 10
    type: int
  bulk_volume_size_gb:
    description:
      - Size of the bulk storage volume in GB.
      - No bulk storage volume if not set.
    type: int
  ssh_keys:
    description:
       - List of SSH public keys.
       - Use the full content of your .pub file here.
    type: list
  use_public_network:
    description:
      - Attach a public network interface to the server.
    default: yes
    type: bool
  use_private_network:
    description:
      - Attach a private network interface to the server.
    default: no
    type: bool
  use_ipv6:
    description:
      - Enable IPv6 on the public network interface.
    default: yes
    type: bool
  anti_affinity_with:
    description:
      - UUID of another server to create an anti-affinity group with.
    type: str
  user_data:
    description:
      - Cloud-init configuration (cloud-config) data to use for the server.
    type: str
  api_timeout:
    version_added: '2.5'
  force:
    description:
      - Allow to stop the running server for updating if necessary.
    default: no
    type: bool
    version_added: '2.8'
extends_documentation_fragment: cloudscale
'''

EXAMPLES = '''
# Start a server (if it does not exist) and register the server details
- name: Start cloudscale.ch server
  cloudscale_server:
    name: my-shiny-cloudscale-server
    image: debian-8
    flavor: flex-4
    ssh_keys: ssh-rsa XXXXXXXXXX...XXXX ansible@cloudscale
    use_private_network: True
    bulk_volume_size_gb: 100
    api_token: xxxxxx
  register: server1

# Start another server in anti-affinity to the first one
- name: Start second cloudscale.ch server
  cloudscale_server:
    name: my-other-shiny-server
    image: ubuntu-16.04
    flavor: flex-8
    ssh_keys: ssh-rsa XXXXXXXXXXX ansible@cloudscale
    anti_affinity_with: '{{ server1.uuid }}'
    api_token: xxxxxx

# Force to update the flavor of a running server
- name: Start cloudscale.ch server
  cloudscale_server:
    name: my-shiny-cloudscale-server
    image: debian-8
    flavor: flex-8
    force: yes
    ssh_keys: ssh-rsa XXXXXXXXXX...XXXX ansible@cloudscale
    use_private_network: True
    bulk_volume_size_gb: 100
    api_token: xxxxxx
  register: server1

# Stop the first server
- name: Stop my first server
  cloudscale_server:
    uuid: '{{ server1.uuid }}'
    state: stopped
    api_token: xxxxxx

# Delete my second server
- name: Delete my second server
  cloudscale_server:
    name: my-other-shiny-server
    state: absent
    api_token: xxxxxx

# Start a server and wait for the SSH host keys to be generated
- name: Start server and wait for SSH host keys
  cloudscale_server:
    name: my-cloudscale-server-with-ssh-key
    image: debian-8
    flavor: flex-4
    ssh_keys: ssh-rsa XXXXXXXXXXX ansible@cloudscale
    api_token: xxxxxx
  register: server
  until: server.ssh_fingerprints is defined and server.ssh_fingerprints
  retries: 60
  delay: 2
'''

RETURN = '''
href:
  description: API URL to get details about this server
  returned: success when not state == absent
  type: str
  sample: https://api.cloudscale.ch/v1/servers/cfde831a-4e87-4a75-960f-89b0148aa2cc
uuid:
  description: The unique identifier for this server
  returned: success
  type: str
  sample: cfde831a-4e87-4a75-960f-89b0148aa2cc
name:
  description: The display name of the server
  returned: success
  type: str
  sample: its-a-me-mario.cloudscale.ch
state:
  description: The current status of the server
  returned: success
  type: str
  sample: running
flavor:
  description: The flavor that has been used for this server
  returned: success when not state == absent
  type: str
  sample: flex-8
image:
  description: The image used for booting this server
  returned: success when not state == absent
  type: str
  sample: debian-8
volumes:
  description: List of volumes attached to the server
  returned: success when not state == absent
  type: list
  sample: [ {"type": "ssd", "device": "/dev/vda", "size_gb": "50"} ]
interfaces:
  description: List of network ports attached to the server
  returned: success when not state == absent
  type: list
  sample: [ { "type": "public", "addresses": [ ... ] } ]
ssh_fingerprints:
  description: A list of SSH host key fingerprints. Will be null until the host keys could be retrieved from the server.
  returned: success when not state == absent
  type: list
  sample: ["ecdsa-sha2-nistp256 SHA256:XXXX", ... ]
ssh_host_keys:
  description: A list of SSH host keys. Will be null until the host keys could be retrieved from the server.
  returned: success when not state == absent
  type: list
  sample: ["ecdsa-sha2-nistp256 XXXXX", ... ]
anti_affinity_with:
  description: List of servers in the same anti-affinity group
  returned: success when not state == absent
  type: str
  sample: []
'''

from datetime import datetime, timedelta
from time import sleep
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudscale import AnsibleCloudscaleBase, cloudscale_argument_spec

ALLOWED_STATES = ('running',
                  'stopped',
                  'absent',
                  )


class AnsibleCloudscaleServer(AnsibleCloudscaleBase):

    def __init__(self, module):
        super(AnsibleCloudscaleServer, self).__init__(module)

        # Initialize server dictionary
        self._info = {}

    def _init_server_container(self):
        return {
            'uuid': self._module.params.get('uuid') or self._info.get('uuid'),
            'name': self._module.params.get('name') or self._info.get('name'),
            'state': 'absent',
        }

    def _get_server_info(self, refresh=False):
        if self._info and not refresh:
            return self._info

        self._info = self._init_server_container()

        uuid = self._info.get('uuid')
        if uuid is not None:
            server_info = self._get('servers/%s' % uuid)
            if server_info:
                self._info = self._transform_state(server_info)

        else:
            name = self._info.get('name')
            if name is not None:
                servers = self._get('servers') or []
                matching_server = []
                for server in servers:
                    if server['name'] == name:
                        matching_server.append(server)

                if len(matching_server) == 1:
                    self._info = self._transform_state(matching_server[0])
                elif len(matching_server) > 1:
                    self._module.fail_json(msg="More than one server with name '%s' exists. "
                                           "Use the 'uuid' parameter to identify the server." % name)

        return self._info

    @staticmethod
    def _transform_state(server):
        if 'status' in server:
            server['state'] = server['status']
            del server['status']
        else:
            server['state'] = 'absent'
        return server

    def _wait_for_state(self, states):
        start = datetime.now()
        timeout = self._module.params['api_timeout'] * 2
        while datetime.now() - start < timedelta(seconds=timeout):
            server_info = self._get_server_info(refresh=True)
            if server_info.get('state') in states:
                return server_info
            sleep(1)

        # Timeout succeeded
        if server_info.get('name') is not None:
            msg = "Timeout while waiting for a state change on server %s to states %s. " \
                  "Current state is %s." % (server_info.get('name'), states, server_info.get('state'))
        else:
            name_uuid = self._module.params.get('name') or self._module.params.get('uuid')
            msg = 'Timeout while waiting to find the server %s' % name_uuid

        self._module.fail_json(msg=msg)

    def _start_stop_server(self, server_info, target_state="running", ignore_diff=False):
        actions = {
            'stopped': 'stop',
            'running': 'start',
        }

        server_state = server_info.get('state')
        if server_state != target_state:
            self._result['changed'] = True

            if not ignore_diff:
                self._result['diff']['before'].update({
                    'state': server_info.get('state'),
                })
                self._result['diff']['after'].update({
                    'state': target_state,
                })
            if not self._module.check_mode:
                self._post('servers/%s/%s' % (server_info['uuid'], actions[target_state]))
                server_info = self._wait_for_state((target_state, ))

        return server_info

    def _create_server(self, server_info):
        self._result['changed'] = True
        required_params = ('name', 'ssh_keys', 'image', 'flavor')
        self._module.fail_on_missing_params(required_params)
        params = self._module.params
        data = {
            'name': params['name'],
            'image': params['image'],
            'flavor': params['flavor'],
            'volume_size_gb': params['volume_size_gb'],
            'bulk_volume_size_gb': params['bulk_volume_size_gb'],
            'ssh_keys': params['ssh_keys'],
            'use_public_network': params['use_public_network'],
            'use_ipv6': params['use_ipv6'],
            'anti_affinity_with': params['anti_affinity_with'],
            'user_data': params['user_data'],
        }
        self._result['diff']['before'] = self._init_server_container()
        self._result['diff']['after'] = deepcopy(data)
        if not self._module.check_mode:
            self._post('servers', data)
            server_info = self._wait_for_state(('running', ))
        return server_info

    def _get_keys_changed(self, server_info, data):
        # Look if and what changed
        keys_changed = []
        for k, v in data.items():

            if v is None:
                continue

            elif k in server_info:
                # compare with slug field if available
                if 'slug' in server_info[k]:
                    server_v = server_info[k]['slug']
                else:
                    server_v = server_info[k]

                if server_v != v:
                    keys_changed.append(k)
                    # Set the diff output
                    self._result['diff']['before'].update({k: server_v})
                    self._result['diff']['after'].update({k: v})

        return keys_changed

    def _update_server(self, server_info):
        data_requires_stop = {
            'flavor': self._module.params.get('flavor'),
        }
        keys_changed_requires_stop = self._get_keys_changed(server_info, data_requires_stop)

        data = {
            'name': self._module.params.get('name'),
        }
        keys_changed = self._get_keys_changed(server_info, data)

        if not (keys_changed or keys_changed_requires_stop):
            return server_info

        # Keys changed don't require a stopped server
        if keys_changed:
            self._result['changed'] = True
            if not self._module.check_mode:
                # The API does not allow to change multiple attributes at the same time.
                for key_changed in keys_changed:
                    patch_data = {
                        key_changed: data[key_changed],
                    }
                    # Response is 204: No Content
                    self._patch('servers/%s' % server_info['uuid'], patch_data)
                    # State changes to "changing" after update, waiting for stopped or running
                    server_info = self._wait_for_state(('stopped', 'running'))

        # Keys changed require a stopped server
        if keys_changed_requires_stop:
            # We have changed keys but we ignore them unless forced if server is running
            if server_info.get('state') == "running":
                if not self._module.params.get('force'):
                    self._module.warn("Some changes won't be applied to running servers. "
                                      "Use force=yes to allow the server '%s' to be stopped/started." % server_info['name'])
                    return server_info

            # Either the server is stopped or change is forced
            self._result['changed'] = True
            if not self._module.check_mode:
                # Remember the state of the server before we ensure it is stopped
                previous_state = server_info.get('state')
                self._start_stop_server(server_info, target_state="stopped", ignore_diff=True)

                # The API does not allow to change multiple attributes at the same time.
                for key_changed in keys_changed_requires_stop:
                    patch_data = {
                        key_changed: data_requires_stop[key_changed],
                    }
                    # Response is 204: No Content
                    self._patch('servers/%s' % server_info['uuid'], patch_data)
                    # State changes to "changing" after update, waiting for stopped
                    server_info = self._wait_for_state(('stopped', ))

                # Restore the state before we ensure stopped
                if previous_state == "running":
                    self._start_stop_server(server_info, target_state="running", ignore_diff=True)

                server_info = self._get_server_info(refresh=True)

        return server_info

    def present_server(self):
        server_info = self._get_server_info()

        if server_info.get('state') != "absent":

            # If target state is stopped, stop before an potential update and force would not be required
            if self._module.params.get('state') == "stopped":
                server_info = self._start_stop_server(server_info, target_state="stopped")

            server_info = self._update_server(server_info)

            if self._module.params.get('state') == "running":
                server_info = self._start_stop_server(server_info, target_state="running")
        else:
            server_info = self._create_server(server_info)
            server_info = self._start_stop_server(server_info, target_state=self._module.params.get('state'))

        return server_info

    def absent_server(self):
        server_info = self._get_server_info()
        if server_info.get('state') != "absent":
            self._result['changed'] = True
            self._result['diff']['before'] = deepcopy(server_info)
            self._result['diff']['after'] = self._init_server_container()
            if not self._module.check_mode:
                self._delete('servers/%s' % server_info['uuid'])
                server_info = self._wait_for_state(('absent', ))
        return server_info


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        state=dict(default='running', choices=ALLOWED_STATES),
        name=dict(),
        uuid=dict(),
        flavor=dict(),
        image=dict(),
        volume_size_gb=dict(type='int', default=10),
        bulk_volume_size_gb=dict(type='int'),
        ssh_keys=dict(type='list'),
        use_public_network=dict(type='bool', default=True),
        use_private_network=dict(type='bool', default=False),
        use_ipv6=dict(type='bool', default=True),
        anti_affinity_with=dict(),
        user_data=dict(),
        force=dict(type='bool', default=False)
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(('name', 'uuid'),),
        supports_check_mode=True,
    )

    cloudscale_server = AnsibleCloudscaleServer(module)
    if module.params['state'] == "absent":
        server = cloudscale_server.absent_server()
    else:
        server = cloudscale_server.present_server()

    result = cloudscale_server.get_result(server)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
