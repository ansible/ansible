#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudscale_server
short_description: Manages servers on the cloudscale.ch IaaS service
description:
  - Create, start, stop and delete servers on the cloudscale.ch IaaS service.
  - All operations are performed using the cloudscale.ch public API v1.
  - "For details consult the full API documentation: U(https://www.cloudscale.ch/en/api/v1)."
  - An valid API token is required for all operations. You can create as many tokens as you like using the cloudscale.ch control panel at
    U(https://control.cloudscale.ch).
notes:
  - Instead of the api_token parameter the CLOUDSCALE_API_TOKEN environment variable can be used.
  - To create a new server at least the C(name), C(ssh_key), C(image) and C(flavor) options are required.
  - If more than one server with the name given by the C(name) option exists, execution is aborted.
  - Once a server is created all parameters except C(state) are read-only. You can't change the name, flavor or any other property. This is a limitation
    of the cloudscale.ch API. The module will silently ignore differences between the configured parameters and the running server if a server with the
    correct name or UUID exists. Only state changes will be applied.
version_added: 2.3
author: "Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>"
options:
  state:
    description:
      - State of the server
    required: False
    default: running
    choices: ['running', 'stopped', 'absent']
  name:
    description:
      - Name of the Server
      - Either C(name) or C(uuid) are required. These options are mutually exclusive.
    required: False
  uuid:
    description:
      - UUID of the server
      - Either C(name) or C(uuid) are required. These options are mutually exclusive.
    required: False
  flavor:
    description:
      - Flavor of the server
    required: False
  image:
    description:
      - Image used to create the server
    required: False
  volume_size_gb:
    description:
      - Size of the root volume in GB
    required: False
    default: 10
  bulk_volume_size_gb:
    description:
      - Size of the bulk storage volume in GB
    required: False
    default: null (no bulk storage volume)
  ssh_keys:
    description:
       - List of SSH public keys
       - Use the full content of your .pub file here.
    required: False
  use_public_network:
    description:
      - Attach a public network interface to the server
    required: False
    default: True
  use_private_network:
    description:
      - Attach a private network interface to the server
    required: False
    default: False
  use_ipv6:
    description:
      - Enable IPv6 on the public network interface
    required: False
    default: True
  anti_affinity_with:
    description:
      - UUID of another server to create an anti-affinity group with
    required: False
  user_data:
    description:
      - Cloud-init configuration (cloud-config) data to use for the server.
    required: False
  api_token:
    description:
      - cloudscale.ch API token.
      - This can also be passed in the CLOUDSCALE_API_TOKEN environment variable.
    required: False
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
  until: server.ssh_fingerprints
  retries: 60
  delay: 2
'''

RETURN = '''
href:
  description: API URL to get details about this server
  returned: success when not state == absent
  type: string
  sample: https://api.cloudscale.ch/v1/servers/cfde831a-4e87-4a75-960f-89b0148aa2cc
uuid:
  description: The unique identifier for this server
  returned: success
  type: string
  sample: cfde831a-4e87-4a75-960f-89b0148aa2cc
name:
  description: The display name of the server
  returned: success
  type: string
  sample: its-a-me-mario.cloudscale.ch
state:
  description: The current status of the server
  returned: success
  type: string
  sample: running
flavor:
  description: The flavor that has been used for this server
  returned: success when not state == absent
  type: string
  sample: flex-8
image:
  description: The image used for booting this server
  returned: success when not state == absent
  type: string
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
  type: string
  sample: []
'''

import json
import os
from datetime import datetime, timedelta
from time import sleep

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import fetch_url


API_URL      = 'https://api.cloudscale.ch/v1/'
TIMEOUT_WAIT = 30
ALLOWED_STATES = ('running',
                  'stopped',
                  'absent',
                  )


class AnsibleCloudscaleServer(object):

    def __init__(self, module, api_token):
        self._module = module
        self._auth_header = {'Authorization': 'Bearer %s' % api_token}

        # Check if server already exists and load properties
        uuid = self._module.params['uuid']
        name = self._module.params['name']

        # Initialize server dictionary
        self.info = {'uuid': uuid, 'name': name, 'state': 'absent'}

        servers = self.list_servers()
        matching_server = []
        for s in servers:
            if uuid:
                # Look for server by UUID if given
                if s['uuid'] == uuid:
                    self.info =  self._transform_state(s)
                    break
            else:
                # Look for server by name
                if s['name'] == name:
                    matching_server.append(s)
        else:
            if len(matching_server) == 1:
                self.info = self._transform_state(matching_server[0])
            elif len(matching_server) > 1:
                self._module.fail_json(msg="More than one server with name '%s' exists. "
                                       "Use the 'uuid' parameter to identify the server" % name)


    def _get(self, api_call):
        resp, info = fetch_url(self._module, API_URL+api_call, headers=self._auth_header)

        if info['status'] == 200:
            return json.loads(resp.read())
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with GET for '
                                       '"%s": %s' % (api_call, info['body']))


    def _post(self, api_call, data=None):
        if data is not None:
            data = urlencode(data)

        resp, info = fetch_url(self._module,
                               API_URL+api_call,
                               headers = self._auth_header,
                               method='POST',
                               data=data)

        if info['status'] == 201:
            return json.loads(resp.read())
        elif info['status'] == 204:
            return None
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with POST for '
                                       '"%s": %s' % (api_call, info['body']))


    def _delete(self, api_call):
        resp, info = fetch_url(self._module,
                               API_URL+api_call,
                               headers = self._auth_header,
                               method='DELETE')

        if info['status'] == 204:
            return None
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with DELETE for '
                                       '"%s": %s' % (api_call, info['body']))


    @staticmethod
    def _transform_state(server):
        if 'status' in server:
            server['state'] = server['status']
            del server['status']
        else:
            server['state'] = 'absent'
        return server


    def update_info(self):

        # If we don't have a UUID (yet) there is nothing to update
        if not 'uuid' in self.info:
            return

        # Can't use _get here because we want to handle 404
        resp, info = fetch_url(self._module,
                               API_URL+'servers/'+self.info['uuid'],
                               headers=self._auth_header)
        if info['status'] == 200:
            self.info = self._transform_state(json.loads(resp.read()))
        elif info['status'] == 404:
            self.info = {'uuid': self.info['uuid'],
                         'name': self.info.get('name', None),
                         'state': 'absent'}
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API for '
                                       'update_info: %s' % info['body'])


    def wait_for_state(self, states):
        start = datetime.now()
        while datetime.now() - start < timedelta(seconds=TIMEOUT_WAIT):
            self.update_info()
            if self.info['state'] in states:
                return True
            sleep(1)

        self._module.fail_json(msg='Timeout while waiting for a state change on server %s to states %s. Current state is %s'
                               % (self.info['name'], states, self.info['state']))


    def create_server(self):
        data = self._module.params.copy()

        # check for required parameters to create a server
        missing_parameters = []
        for p in ('name', 'ssh_keys', 'image', 'flavor'):
            if not p in data or not data[p]:
                missing_parameters.append(p)

        if len(missing_parameters) > 0:
            self._module.fail_json(msg='Missing required parameter(s) to create a new server: %s' %
                                   ' '.join(missing_parameters))

        # Sanitize data dictionary
        for k,v in data.items():

            # Remove items not relevant to the create server call
            if k in ('api_token', 'uuid', 'state'):
                del data[k]
                continue

            # Remove None values, these don't get correctly translated by urlencode
            if v is None:
                del data[k]
                continue

        self.info = self._transform_state(self._post('servers', data))
        self.wait_for_state(('running', ))


    def delete_server(self):
        self._delete('servers/%s' % self.info['uuid'])
        self.wait_for_state(('absent', ))


    def start_server(self):
        self._post('servers/%s/start' % self.info['uuid'])
        self.wait_for_state(('running', ))


    def stop_server(self):
        self._post('servers/%s/stop' % self.info['uuid'])
        self.wait_for_state(('stopped', ))


    def list_servers(self):
        return self._get('servers')


def main():
    module = AnsibleModule(
        argument_spec = dict(
            state               = dict(default='running',
                                       choices=ALLOWED_STATES),
            name                = dict(),
            uuid                = dict(),
            flavor              = dict(),
            image               = dict(),
            volume_size_gb      = dict(type='int', default=10),
            bulk_volume_size_gb = dict(type='int'),
            ssh_keys            = dict(type='list'),
            use_public_network  = dict(type='bool', default=True),
            use_private_network = dict(type='bool', default=False),
            use_ipv6            = dict(type='bool', default=True),
            anti_affinity_with  = dict(),
            user_data           = dict(),
            api_token           = dict(no_log=True),
        ),
        required_one_of=(('name', 'uuid'),),
        mutually_exclusive=(('name', 'uuid'),),
        supports_check_mode=True,
    )

    api_token = module.params['api_token'] or os.environ.get('CLOUDSCALE_API_TOKEN')

    if not api_token:
        module.fail_json(msg='The api_token module parameter or the CLOUDSCALE_API_TOKEN '
                             'environment varialbe are required for this module.')

    target_state = module.params['state']
    server = AnsibleCloudscaleServer(module, api_token)
    # The server could be in a changeing or error state.
    # Wait for one of the allowed states before doing anything.
    # If an allowed state can't be reached, this module fails.
    if not server.info['state'] in ALLOWED_STATES:
        server.wait_for_state(ALLOWED_STATES)
    current_state = server.info['state']

    if module.check_mode:
        module.exit_json(changed=not target_state == current_state,
                         **server.info)

    changed = False
    if current_state == 'absent' and target_state == 'running':
        server.create_server()
        changed = True
    elif current_state == 'absent' and target_state == 'stopped':
        server.create_server()
        server.stop_server()
        changed = True
    elif current_state == 'stopped' and target_state == 'running':
        server.start_server()
        changed = True
    elif current_state in ('running', 'stopped') and target_state == 'absent':
        server.delete_server()
        changed = True
    elif current_state == 'running' and target_state == 'stopped':
        server.stop_server()
        changed = True

    module.exit_json(changed=changed, **server.info)


if __name__ == '__main__':
    main()
