#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# Copyright (c) 2019, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudscale_server_facts
short_description: Gather server facts on cloudscale.ch IaaS service
description:
  - Gather facts about servers available.
  - If more than one server with the name given by the I(name) option exists, execution is aborted.
author:
  - "Gaudenz Steinlin (@gaudenz)"
  - "René Moser (@resmo)"
version_added: "2.8"
options:
  name:
    description:
      - Name of the server.
      - Either I(name) or I(uuid) are required. These options are mutually exclusive.
  uuid:
    description:
      - UUID of the server.
      - Either I(name) or I(uuid) are required. These options are mutually exclusive.
extends_documentation_fragment: cloudscale
'''

EXAMPLES = '''
- name: Get facts of a server by its name
  cloudscale_server:
    name: my-name
    api_token: xxxxxx

- name: Get facts of a server by its uuid
  cloudscale_server:
    uuid: "{{ my_uuid }}"
    api_token: xxxxxx
'''

RETURN = '''
href:
  description: API URL to get details about this server
  returned: if available
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
  returned: if available
  type: str
  sample: flex-8
image:
  description: The image used for booting this server
  returned: if available
  type: str
  sample: debian-8
volumes:
  description: List of volumes attached to the server
  returned: if available
  type: list
  sample: [ {"type": "ssd", "device": "/dev/vda", "size_gb": "50"} ]
interfaces:
  description: List of network ports attached to the server
  returned: if available
  type: list
  sample: [ { "type": "public", "addresses": [ ... ] } ]
ssh_fingerprints:
  description: A list of SSH host key fingerprints. Will be null until the host keys could be retrieved from the server.
  returned: if available
  type: list
  sample: ["ecdsa-sha2-nistp256 SHA256:XXXX", ... ]
ssh_host_keys:
  description: A list of SSH host keys. Will be null until the host keys could be retrieved from the server.
  returned: if available
  type: list
  sample: ["ecdsa-sha2-nistp256 XXXXX", ... ]
anti_affinity_with:
  description: List of servers in the same anti-affinity group
  returned: if available
  type: str
  sample: []
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudscale import AnsibleCloudscaleBase, cloudscale_argument_spec


class AnsibleCloudscaleServerFacts(AnsibleCloudscaleBase):

    def __init__(self, module):
        super(AnsibleCloudscaleServerFacts, self).__init__(module)

        # Check if server already exists and load properties
        uuid = self._module.params['uuid']
        name = self._module.params['name']

        # Initialize server dictionary
        self.info = {'uuid': uuid, 'name': name, 'state': 'absent'}

        servers = self._get('servers') or []
        matching_server = []
        for s in servers:
            if uuid:
                # Look for server by UUID if given
                if s['uuid'] == uuid:
                    self.info = self._transform_state(s)
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
                                       "Use the 'uuid' parameter to identify the server." % name)

    @staticmethod
    def _transform_state(server):
        if 'status' in server:
            server['state'] = server['status']
            del server['status']
        else:
            server['state'] = 'absent'
        return server


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        name=dict(),
        uuid=dict(),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(('name', 'uuid'),),
        mutually_exclusive=(('name', 'uuid'),),
        supports_check_mode=True,
    )

    server = AnsibleCloudscaleServerFacts(module)
    ansible_facts = {
        'cloudscale_server': server.info,
    }
    module.exit_json(ansible_facts=ansible_facts, **server.info)


if __name__ == '__main__':
    main()
