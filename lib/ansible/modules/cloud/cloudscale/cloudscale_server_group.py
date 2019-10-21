#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudscale_server_group
short_description: Manages server groups on the cloudscale.ch IaaS service
description:
  - Create, update and remove server groups.
author:
  - René Moser (@resmo)
version_added: '2.8'
options:
  name:
    description:
      - Name of the server group.
      - Either I(name) or I(uuid) is required. These options are mutually exclusive.
    type: str
  uuid:
    description:
      - UUID of the server group.
      - Either I(name) or I(uuid) is required. These options are mutually exclusive.
    type: str
  type:
    description:
      - Type of the server group.
    default: anti-affinity
    type: str
  state:
    description:
      - State of the server group.
    choices: [ present, absent ]
    default: present
    type: str
  tags:
    description:
      - Tags assosiated with the server groups. Set this to C({}) to clear any tags.
    type: dict
    version_added: '2.9'
extends_documentation_fragment: cloudscale
'''

EXAMPLES = '''
---
- name: Ensure server group exists
  cloudscale_server_group:
    name: my-name
    type: anti-affinity
    api_token: xxxxxx

- name: Ensure a server group is absent
  cloudscale_server_group:
    name: my-name
    state: absent
    api_token: xxxxxx
'''

RETURN = '''
---
href:
  description: API URL to get details about this server group
  returned: if available
  type: str
  sample: https://api.cloudscale.ch/v1/server-group/cfde831a-4e87-4a75-960f-89b0148aa2cc
uuid:
  description: The unique identifier for this server
  returned: always
  type: str
  sample: cfde831a-4e87-4a75-960f-89b0148aa2cc
name:
  description: The display name of the server group
  returned: always
  type: str
  sample: load balancers
type:
  description: The type the server group
  returned: if available
  type: str
  sample: anti-affinity
servers:
  description: A list of servers that are part of the server group.
  returned: if available
  type: list
  sample: []
state:
  description: State of the server group.
  returned: always
  type: str
  sample: present
tags:
  description: Tags assosiated with the server group.
  returned: success
  type: dict
  sample: { 'project': 'my project' }
  version_added: '2.9'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudscale import AnsibleCloudscaleBase, cloudscale_argument_spec


class AnsibleCloudscaleServerGroup(AnsibleCloudscaleBase):

    def __init__(self, module, namespace):
        super(AnsibleCloudscaleServerGroup, self).__init__(module)
        self._info = {}

    def _init_container(self):
        return {
            'uuid': self._module.params.get('uuid') or self._info.get('uuid'),
            'name': self._module.params.get('name') or self._info.get('name'),
            'state': 'absent',
        }

    def _create_server_group(self, server_group):
        self._module.fail_on_missing_params(['name'])
        self._result['changed'] = True
        data = {
            'name': self._module.params.get('name'),
            'type': self._module.params.get('type'),
            'tags': self._module.params.get('tags'),
        }
        if not self._module.check_mode:
            server_group = self._post('server-groups', data)
        return server_group

    def _update_server_group(self, server_group):
        updated = self._param_updated('name', server_group)
        updated = self._param_updated('tags', server_group) or updated

        # Refresh if resource was updated in live mode
        if updated and not self._module.check_mode:
            server_group = self.get_server_group()
        return server_group

    def get_server_group(self):
        self._info = self._init_container()

        uuid = self._info.get('uuid')
        if uuid is not None:
            server_group = self._get('server-groups/%s' % uuid)
            if server_group:
                self._info.update(server_group)
                self._info.update(dict(state='present'))

        else:
            name = self._info.get('name')
            matching_server_groups = []
            for server_group in self._get('server-groups'):
                if server_group['name'] == name:
                    matching_server_groups.append(server_group)

            if len(matching_server_groups) > 1:
                self._module.fail_json(msg="More than one server group with name exists: '%s'. "
                                       "Use the 'uuid' parameter to identify the server group." % name)
            elif len(matching_server_groups) == 1:
                self._info.update(matching_server_groups[0])
                self._info.update(dict(state='present'))
        return self._info

    def present_group(self):
        server_group = self.get_server_group()
        if server_group.get('state') == 'absent':
            server_group = self._create_server_group(server_group)
        else:
            server_group = self._update_server_group(server_group)
        return server_group

    def absent_group(self):
        server_group = self.get_server_group()
        if server_group.get('state') != 'absent':
            self._result['changed'] = True
            if not self._module.check_mode:
                self._delete('server-groups/%s' % server_group['uuid'])
        return server_group


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        name=dict(),
        uuid=dict(),
        type=dict(default='anti-affinity'),
        tags=dict(type='dict'),
        state=dict(default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(('name', 'uuid'),),
        supports_check_mode=True,
    )
    cloudscale_server_group = AnsibleCloudscaleServerGroup(module, 'cloudscale_server_group')

    if module.params['state'] == 'absent':
        server_group = cloudscale_server_group.absent_group()
    else:
        server_group = cloudscale_server_group.present_group()

    result = cloudscale_server_group.get_result(server_group)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
