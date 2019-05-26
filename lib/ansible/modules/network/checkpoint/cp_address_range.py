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
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cp_address_range
short_description: Manages address_range objects on Checkpoint over Web Services API
description:
  - Manages address_range objects on Checkpoint devices including creating, updating and removing objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  ip_address_first:
    description:
      - First IP address in the range. If both IPv4 and IPv6 address ranges are required, use the ipv4-address-first and
        the ipv6-address-first fields instead.
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
      - Last IP address in the range. If both IPv4 and IPv6 address ranges are required, use the ipv4-address-first and
        the ipv6-address-first fields instead.
    type: str
  ipv4_address_last:
    description:
      - Last IPv4 address in the range.
    type: str
  ipv6_address_last:
    description:
      - Last IPv6 address in the range.
    type: str
  nat_settings:
    description:
      - NAT settings.
    type: dict
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: Add address-range object
  cp_address_range:
    name: "New address_range 1"
    ip-address-first: "192.0.2.1"
    ip-address-last: "192.0.2.10"
    state: present
"""

RETURN = """
cp_address_range:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        ip_address_first=dict(type='str'),
        ipv4_address_first=dict(type='str'),
        ipv6_address_first=dict(type='str'),
        ip_address_last=dict(type='str'),
        ipv4_address_last=dict(type='str'),
        ipv6_address_last=dict(type='str'),
        nat_settings=dict(type='dict')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, required_one_of=[['name', 'uid']],
                           mutually_exclusive=[['name', 'uid']])
    api_call_object = "address-range"

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
