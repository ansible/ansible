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
  - Since version 2.8, I(uuid) and I(name) or not mutually exclusive anymore.
  - If I(uuid) option is provided, it takes precedence over I(name) for server selection. This allows to update the server's name.
  - If no I(uuid) option is provided, I(name) is used for server selection. If more than one server with this name exists, execution is aborted.
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
  password:
    description:
       - Password for the server.
    type: str
    version_added: '2.8'
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
      - Mutually exclusive with I(server_groups).
      - Deprecated, removed in version 2.11.
    type: str
  server_groups:
    description:
      - List of UUID or names of server groups.
      - Mutually exclusive with I(anti_affinity_with).
    type: list
    version_added: '2.8'
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
  tags:
    description:
      - Tags assosiated with the servers. Set this to C({}) to clear any tags.
    type: dict
    version_added: '2.9'
extends_documentation_fragment: cloudscale
'''

EXAMPLES = '''
# Create and start a server with an existing server group (shiny-group)
- name: Start cloudscale.ch server
  cloudscale_server:
    name: my-shiny-cloudscale-server
    image: debian-8
    flavor: flex-4
    ssh_keys: ssh-rsa XXXXXXXXXX...XXXX ansible@cloudscale
    server_groups: shiny-group
    use_private_network: True
    bulk_volume_size_gb: 100
    api_token: xxxxxx

# Start another server in anti-affinity (server group shiny-group)
- name: Start second cloudscale.ch server
  cloudscale_server:
    name: my-other-shiny-server
    image: ubuntu-16.04
    flavor: flex-8
    ssh_keys: ssh-rsa XXXXXXXXXXX ansible@cloudscale
    server_groups: shiny-group
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
  description:
  - List of servers in the same anti-affinity group
  - Deprecated, removed in version 2.11.
  returned: success when not state == absent
  type: list
  sample: []
server_groups:
  description: List of server groups
  returned: success when not state == absent
  type: list
  sample: [ {"href": "https://api.cloudscale.ch/v1/server-groups/...", "uuid": "...", "name": "db-group"} ]
  version_added: '2.8'
tags:
  description: Tags assosiated with the volume.
  returned: success
  type: dict
  sample: { 'project': 'my project' }
  version_added: '2.9'
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

    def _update_param(self, param_key, server_info, requires_stop=False):
        param_value = self._module.params.get(param_key)
        if param_value is None:
            return server_info

        if 'slug' in server_info[param_key]:
            server_v = server_info[param_key]['slug']
        else:
            server_v = server_info[param_key]

        if server_v != param_value:
            # Set the diff output
            self._result['diff']['before'].update({param_key: server_v})
            self._result['diff']['after'].update({param_key: param_value})

            if server_info.get('state') == "running":
                if requires_stop and not self._module.params.get('force'):
                    self._module.warn("Some changes won't be applied to running servers. "
                                      "Use force=yes to allow the server '%s' to be stopped/started." % server_info['name'])
                    return server_info

            # Either the server is stopped or change is forced
            self._result['changed'] = True
            if not self._module.check_mode:

                if requires_stop:
                    self._start_stop_server(server_info, target_state="stopped", ignore_diff=True)

                patch_data = {
                    param_key: param_value,
                }

                # Response is 204: No Content
                self._patch('servers/%s' % server_info['uuid'], patch_data)

                # State changes to "changing" after update, waiting for stopped/running
                server_info = self._wait_for_state(('stopped', 'running'))

        return server_info

    def _get_server_group_ids(self):
        server_group_params = self._module.params['server_groups']
        if not server_group_params:
            return None

        matching_group_names = []
        results = []
        server_groups = self._get('server-groups')
        for server_group in server_groups:
            if server_group['uuid'] in server_group_params:
                results.append(server_group['uuid'])
                server_group_params.remove(server_group['uuid'])

            elif server_group['name'] in server_group_params:
                results.append(server_group['uuid'])
                server_group_params.remove(server_group['name'])
                # Remember the names found
                matching_group_names.append(server_group['name'])

            # Names are not unique, verify if name already found in previous iterations
            elif server_group['name'] in matching_group_names:
                self._module.fail_json(msg="More than one server group with name exists: '%s'. "
                                       "Use the 'uuid' parameter to identify the server group." % server_group['name'])

        if server_group_params:
            self._module.fail_json(msg="Server group name or UUID not found: %s" % ', '.join(server_group_params))

        return results

    def _create_server(self, server_info):
        self._result['changed'] = True

        data = deepcopy(self._module.params)
        for i in ('uuid', 'state', 'force', 'api_timeout', 'api_token'):
            del data[i]
        data['server_groups'] = self._get_server_group_ids()

        self._result['diff']['before'] = self._init_server_container()
        self._result['diff']['after'] = deepcopy(data)
        if not self._module.check_mode:
            self._post('servers', data)
            server_info = self._wait_for_state(('running', ))
        return server_info

    def _update_server(self, server_info):

        previous_state = server_info.get('state')

        # The API doesn't support to update server groups.
        # Show a warning to the user if the desired state does not match.
        desired_server_group_ids = self._get_server_group_ids()
        if desired_server_group_ids is not None:
            current_server_group_ids = [grp['uuid'] for grp in server_info['server_groups']]
            if desired_server_group_ids != current_server_group_ids:
                self._module.warn("Server groups can not be mutated, server needs redeployment to change groups.")

        server_info = self._update_param('flavor', server_info, requires_stop=True)
        server_info = self._update_param('name', server_info)
        server_info = self._update_param('tags', server_info)

        if previous_state == "running":
            server_info = self._start_stop_server(server_info, target_state="running", ignore_diff=True)

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
        password=dict(no_log=True),
        use_public_network=dict(type='bool', default=True),
        use_private_network=dict(type='bool', default=False),
        use_ipv6=dict(type='bool', default=True),
        anti_affinity_with=dict(removed_in_version='2.11'),
        server_groups=dict(type='list'),
        user_data=dict(),
        force=dict(type='bool', default=False),
        tags=dict(type='dict'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(('name', 'uuid'),),
        mutually_exclusive=(('anti_affinity_with', 'server_groups'),),
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
