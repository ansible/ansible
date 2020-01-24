#!/usr/bin/python

# Copyright: (c) 2018, Juergen Wiebe <wiebe@e-spirit.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: utm_network_interface_address

author:
    - Juergen Wiebe (@steamx)

short_description: Create, update or destroy network/interface_address object

description:
    - Create, update or destroy a network/interface_address object in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    address:
        description:
          - The ip4 address of the network/interface_address object.
        required: true
    address6:
        description:
          - The ip6 address of the network/interface_address object.
        required: false
    comment:
        description:
          - An optional comment to add to the object
    resolved:
        description:
          - Whether or not the object is resolved
    resolved6:
        description:
          - Whether or not the object is resolved

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
# Create a network interface address
- name: utm network interface address
  utm_proxy_backend:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestNetworkInterfaceAddress
    address: 0.0.0.0
    state: present

# Remove a network interface address
- name: utm network interface address
  network_interface_address:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestNetworkInterfaceAddress
    address: 0.0.0.0
    state: absent
"""

RETURN = """
result:
    description: The utm object that was created
    returned: success
    type: complex
    contains:
        _ref:
            description: The reference name of the object
            type: str
        _locked:
            description: Whether or not the object is currently locked
            type: bool
        _type:
            description: The type of the object
            type: str
        name:
            description: The name of the object
            type: str
        address:
             description: The ip4 address of the network/interface_address object
             type: str
        address6:
             description: The ip6 address of the network/interface_address object
             type: str
        comment:
            description: The comment string
            type: str
        resolved:
             description: Whether or not the object is resolved
             type: bool
        resolved6:
             description: Whether or not the object is resolved
             type: bool
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "network/interface_address"
    key_to_check_for_changes = ["comment", "address"]
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            address=dict(type='str', required=True),
            comment=dict(type='str', required=False, default=""),
            address6=dict(type='str', required=False),
            resolved=dict(type='boolean', required=False),
            resolved6=dict(type='boolean', required=False)
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
