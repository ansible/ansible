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
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: checkpoint_network
short_description: Manages network objects on Checkpoint over Web Services API
description:
  - Manages network objects on Checkpoint devices including creating, updating, removing network objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  subnet:
    description:
      - IPv4 or IPv6 network address. If both addresses are required use subnet4 and subnet6 fields explicitly.
    type: str
  subnet4:
    description:
      - IPv4 network address.
    type: str
  subnet6:
    description:
      - IPv6 network address.
    type: str
  mask_length:
    description:
      - IPv4 or IPv6 network mask length. If both masks are required use mask-length4 and mask-length6 fields
        explicitly. Instead of IPv4 mask length it is possible to specify IPv4 mask itself in subnet-mask field.
    type: int
  mask_length4:
    description:
      - IPv4 network mask length.
    type: int
  mask_length6:
    description:
      - IPv6 network mask length.
    type: int
  subnet_mask:
    description:
      - IPv4 network mask.
    type: str
  nat_settings:
    description:
      - NAT settings.
    type: dict
  broadcast:
    description:
      - Allow broadcast address inclusion.
    type: str
    choices: ['disallow', 'allow']
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: Add network object
  checkpoint_network:
    name: "New Network 1"
    subnet: "192.0.2.0"
    subnet_mask : "255.255.255.0"
    state: present


- name: Delete network object
  checkpoint_network:
    name: "New Network 1"
    state: absent
"""

RETURN = """
api_result:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        subnet=dict(type='str'),
        subnet4=dict(type='str'),
        subnet6=dict(type='str'),
        mask_length=dict(type='int'),
        mask_length4=dict(type='int'),
        mask_length6=dict(type='int'),
        subnet_mask=dict(type='str'),
        nat_settings=dict(type='dict'),
        broadcast=dict(type='str', choices=['disallow', 'allow'])
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, required_one_of=[['name', 'uid']],
                           mutually_exclusive=[['name', 'uid']])
    api_call_object = "network"

    api_call(module, api_call_object)


if __name__ == '__main__':
    main()
