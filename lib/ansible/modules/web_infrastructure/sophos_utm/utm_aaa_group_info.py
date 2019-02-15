#!/usr/bin/python

# Copyright: (c) 2018, Johannes Brunswicker <johannes.brunswicker@gmail.com>
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
module: utm_aaa_group_info

author:
    - Johannes Brunswicker (@MatrixCrawler)

short_description: get info for reverse_proxy frontend entry in Sophos UTM

description:
    - get info for a reverse_proxy frontend entry in SOPHOS UTM.

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
- name: Remove UTM aaa_group
  utm_aaa_group_info:
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
        adirectory_groups:
            description: List of Active Directory Groups
            type: string
        adirectory_groups_sids:
            description: List of Active Directory Groups SIDS
            type: list
        backend_match:
            description: The backend to use
            type: string
        comment:
            description: The comment string
            type: string
        dynamic:
            description: Whether the group match is ipsec_dn or directory_group
            type: string
        edirectory_groups:
            description: List of eDirectory Groups
            type: string
        ipsec_dn:
            description: ipsec_dn identifier to match
            type: string
        ldap_attribute:
            description: The LDAP Attribute to match against
            type: string
        ldap_attribute_value:
            description: The LDAP Attribute Value to match against
            type: string
        members:
            description: List of member identifiers of the group
            type: list
        network:
            description: The identifier of the network (network/aaa)
            type: string
        radius_group:
            description: The radius group identifier
            type: string
        tacacs_group:
            description: The tacacs group identifier
            type: string
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "aaa/group"
    key_to_check_for_changes = []
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True)
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes, info_only=True).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
