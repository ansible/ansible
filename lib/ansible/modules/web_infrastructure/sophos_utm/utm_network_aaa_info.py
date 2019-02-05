#!/usr/bin/python

# Copyright: (c) 2018, Stephan Schwarz <stearz@gmx.de>
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
module: utm_network_aaa_info

author:
    - Stephan Schwarz (@stearz)

short_description: Get a network aaa entry in Sophos UTM

description:
    - Get a network aaa entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Get UTM network_aaa
  utm_network_aaa_info:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestAAAGroupEntry
"""

RETURN = """
result:
    description: The utm object that was created
    returned: success
    type: complex
    contains:
        _ref:
            description: The reference name of the object
            type: string
        _locked:
            description: Whether or not the object is currently locked
            type: boolean
        _type:
            description: The type of the object
            type: string
        name:
            description: The name of the object
            type: string
        addresses:
            description: List of IPv4 addresses
            type: list
        addresses6:
            description: List of IPv6 addresses
            type: list
        comment:
            description: Optional comment string
            type: string
        resolved:
            description: Optional boolean
            type: boolean
        resolved6:
            description: Optional boolean
            type: boolean
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "network/aaa"
    key_to_check_for_changes = []
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes, info_only=True).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
