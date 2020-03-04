#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Check Point Firewall (c) 2019
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
module: cp_mgmt_multicast_address_range
short_description: Manages multicast-address-range objects on Check Point over Web Services API
description:
  - Manages multicast-address-range objects on Check Point devices including creating, updating and removing objects.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  ip_address:
    description:
      - IPv4 or IPv6 address. If both addresses are required use ipv4-address and ipv6-address fields explicitly.
    type: str
  ipv4_address:
    description:
      - IPv4 address.
    type: str
  ipv6_address:
    description:
      - IPv6 address.
    type: str
  ip_address_first:
    description:
      - First IP address in the range. If both IPv4 and IPv6 address ranges are required, use the ipv4-address-first and the ipv6-address-first fields instead.
    type: str
  ipv4_address_first:
    description:
      - First IPv4 address in the range.
    type: str
  ipv6_address_first:
    description:
      - First IPv6 address in the range.
    type: str
  ip_address_last:
    description:
      - Last IP address in the range. If both IPv4 and IPv6 address ranges are required, use the ipv4-address-first and the ipv6-address-first fields instead.
    type: str
  ipv4_address_last:
    description:
      - Last IPv4 address in the range.
    type: str
  ipv6_address_last:
    description:
      - Last IPv6 address in the range.
    type: str
  tags:
    description:
      - Collection of tag identifiers.
    type: list
  color:
    description:
      - Color of the object. Should be one of existing colors.
    type: str
    choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid', 'dark orange', 'dark sea green',
             'pink', 'turquoise', 'dark blue', 'firebrick', 'brown', 'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon',
             'coral', 'sea green', 'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna', 'yellow']
  comments:
    description:
      - Comments string.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the object to a fully detailed
        representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
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
      - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was omitted - warnings will also be ignored.
    type: bool
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: add-multicast-address-range
  cp_mgmt_multicast_address_range:
    ip_address_first: 224.0.0.1
    ip_address_last: 224.0.0.4
    name: New Multicast Address Range
    state: present

- name: set-multicast-address-range
  cp_mgmt_multicast_address_range:
    ip_address_first: 224.0.0.7
    ip_address_last: 224.0.0.10
    name: New Multicast Address Range
    state: present

- name: delete-multicast-address-range
  cp_mgmt_multicast_address_range:
    name: New Multicast Address Range
    state: absent
"""

RETURN = """
cp_mgmt_multicast_address_range:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        ip_address=dict(type='str'),
        ipv4_address=dict(type='str'),
        ipv6_address=dict(type='str'),
        ip_address_first=dict(type='str'),
        ipv4_address_first=dict(type='str'),
        ipv6_address_first=dict(type='str'),
        ip_address_last=dict(type='str'),
        ipv4_address_last=dict(type='str'),
        ipv6_address_last=dict(type='str'),
        tags=dict(type='list'),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green',
                                        'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown',
                                        'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green',
                                        'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna',
                                        'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        groups=dict(type='list'),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'multicast-address-range'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
