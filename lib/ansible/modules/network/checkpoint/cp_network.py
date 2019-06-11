#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage CheckPoint Firewall (c) 2019
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
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cp_network
short_description: Manages network objects on Checkpoint over Web Services API
description:
  - Manages network objects on Checkpoint devices including creating, updating and removing objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
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
  tags:
    description:
      - Collection of tag identifiers.
    type: list
  broadcast:
    description:
      - Allow broadcast address inclusion.
    type: str
    choices:
      - disallow
      - allow
  color:
    description:
      - Color of the object. Should be one of existing colors.
    choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid',
              'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown', 'forest green',
              'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green',
              'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red',
              'sienna', 'yellow']
  comments:
    description:
      - Comments string.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the
        object to a fully detailed representation of the object.
    type: str
    choices: [uid, standard, full]
  groups:
    description:
      - Collection of group identifiers.
    type: list
  ignore_warnings:
    description:
      - Apply changes ignoring warnings.
    type: bool
  ignore_errors:
    description:
      - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was omitted
        - warnings will also be ignored.
    type: bool
  uid:
    description:
      - Object unique identifier.
    type: str
  new_name:
    description:
      - New name of the object.
    type: str
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: add-network
  cp_network:
    name: New Network 3
    nat_settings:
      auto-rule: true
      hide-behind: ip-address
      install-on: All
      ip-address: 192.0.2.1
      method: static
    state: present
    subnet: 192.0.2.1
    subnet_mask: 255.255.255.0

- name: set-network
  cp_network:
    name : New Network 1
    new-name : New Network 2
    color : green
    subnet : 192.0.0.0
    mask-length : 16
    groups : New Group 1
    state: present

- name: delete-network
  cp_network:
    name : New Network 2
    state: absent
"""

RETURN = """
cp_network:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str'),
        subnet=dict(type='str'),
        subnet4=dict(type='str'),
        subnet6=dict(type='str'),
        mask_length=dict(type='int'),
        mask_length4=dict(type='int'),
        mask_length6=dict(type='int'),
        subnet_mask=dict(type='str'),
        nat_settings=dict(type='dict'),
        tags=dict(type='list'),
        broadcast=dict(type='str', choices=['disallow', 'allow']),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green',
                                        'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise',
                                        'dark blue', 'firebrick', 'brown', 'forest green', 'gold', 'dark gold', 'gray',
                                        'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green', 'sky blue',
                                        'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange',
                                        'red', 'sienna', 'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        groups=dict(type='list'),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool'),
        uid=dict(type='str'),
        new_name=dict(type='str')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, required_one_of=[['name', 'uid']],
                           mutually_exclusive=[['name', 'uid']],
                           supports_check_mode=True)

    api_call_object = 'network'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
