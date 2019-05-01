#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'host'}

DOCUMENTATION = """
---
module: checkpoint_host
short_description: Manages host objects on Checkpoint over Web Services API
description:
  - Manages host objects on Checkpoint devices including creating, updating, removing host objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  type:
    description:
      - Type of the object.
    type: str
  domain:
    description:
      - Information about the domain the object belongs to.
    type: dict
  groups:
    description:
      - How much details are returned depends on the details-level field of the request. This table shows the level of
        detail shown when details-level is set to standard.
    type: list
  icon:
    description:
      - Object icon.
    type: str
  interfaces:
    description:
      - Host interfaces.
    type: int
  ipv4_address:
    description:
      - IPv4 host address.
    type: str
  ipv6_address:
    description:
      - IPv6 host address.
    type: str
  meta_info:
    description:
      - Object metadata.
    type: dict
  nat_settings:
    description:
      - NAT settings.
    type: dict
  read_only:
    description:
      - Indicates whether the object is read-only.
    type: bool
  host_servers:
    description:
      - Servers Configuration.
    type: str
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: Add host object
  checkpoint_host:
    name: "New Host 1"
    ip-address: "192.0.2.1"
    state: present


- name: Delete host object
  checkpoint_host:
    name: "New Host 1"
    state: absent
"""

RETURN = """
checkpoint_hosts:
  description: The checkpoint host object created or updated.
  returned: always, except when deleting the host.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec, api_call


def main():
    argument_spec = dict(
        ip_address=dict(type='str'),
        ipv4_address=dict(type='str'),
        ipv6_address=dict(type='str'),
        interfaces=dict(type='list'),
        nat_settings=dict(type='dict'),
        host_servers=dict(type='dict')
    )
    argument_spec.update(checkpoint_argument_spec)
    user_parameters = list(argument_spec.keys())
    user_parameters.remove('auto_publish_session')
    user_parameters.remove('state')

    module = AnsibleModule(argument_spec=argument_spec, required_one_of=[['name', 'uid']],
                           mutually_exclusive=[['name', 'uid']])
    api_call_object = "host"

    unique_payload_for_get = {'name': module.params['name']} if module.params['name'] else {'uid': module.params['uid']}

    api_call(module, api_call_object, user_parameters, unique_payload_for_get)


if __name__ == '__main__':
    main()
