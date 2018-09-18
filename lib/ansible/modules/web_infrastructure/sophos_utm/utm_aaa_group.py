#!/usr/bin/python

# Copyright: (c) 2018, Johannes Brunswicker <johannes.brunswicker@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

from ansible.module_utils.utm_utils import UTM, UTMModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: utm_proxy_frontend

author: 
    - Johannes Brunswicker (@MatrixCrawler)

short_description: create, update or destroy reverse_proxy frontend entry in Sophos UTM

description:
    - Create, update or destroy a reverse_proxy frontend entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8" 

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    adirectory_groups :
        description:
          - list of adirectory group strings 
        type: list
    adirectory_groups_ids :
        description:
          - dictionary of group ids 
        type: list
    backend_match:
        description:
          - The backend for the group
        default: none
        choices:
          - none
          - adirectory
          - edirectory
          - radius
          - tacas
          - ldap
    dynamic:
        description:
          - 
        default: none
        choices:
          - none
          - ipsec_dn
          - directory_groups
    edirectory_groups :
        description:
          - list of edirectory group strings 
        type: list
    ipsec_dn:
        description:
          - The ipsec dn string
        type: str
    ldap_attribute:
        description:
          - The ldap attribute to check against
        type: str
    ldap_attribute_value:
        description:
          - The ldap attribute value to check against
        type: str
    members:
        description:
          - A list of user ref names (aaa/user)
        default: []
    network:
        description:
          - The network reference name. The objects contains the known ip addresses for the authentication object (network/aaa)
        default: ""
    radius_groups:
        description:
          - A list of radius group strings
        default: []
    tacas_groups:
        description:
          - A list of tacas group strings
        default: []

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
# Create a aaa group entry
- name: utm aaa_group
  utm_aaa_group:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestAAAGroupEntry
    backend_match: ldap
    dynamic: directory_groups
    ldap_attributes: memberof
    ldap_attributes_value: "cn=groupname,ou=Groups,dc=mydomain,dc=com"
    network: REF_OBJECT_STRING
    state: present

# Remove a aaa group entry
- name: utm proxy_backend
  utm_proxy_backend:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestAAAGroupEntry
    state: absent
"""

RETURN = """
result:
    description: The utm object that was created
    returned: success
    type: complex
"""


def main():
    endpoint = "aaa/group"
    key_to_check_for_changes = ["comment", "adirectory_groups", "adirectory_groups_sids", "backend_match", "dynamic",
                                "edirectory_groups", "ipsec_dn", "ldap_attribute", "ldap_attribute_value", "members",
                                "network", "radius_groups", "tacas_groups"]
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            adirectory_groups=dict(type='list', elements='str', required=False, default=[]),
            adirectory_groups_sids=dict(type='dict', required=False, default={}),
            backend_match=dict(type='str', required=False, default="none",
                               choices=["none", "adirectory", "edirectory", "radius", "tacas", "ldap"]),
            comment=dict(type='str', required=False, default=""),
            dynamic=dict(type='str', required=False, default="none", choices=["none", "ipsec_dn", "directory_groups"]),
            edirectory_groups=dict(type='list', elements='str', required=False, default=[]),
            ipsec_dn=dict(type='str', required=False, default=""),
            ldap_attribute=dict(type='str', required=False, default=""),
            ldap_attribute_value=dict(type='str', required=False, default=""),
            members=dict(type='list', elements='str', required=False, default=[]),
            network=dict(type='str', required=False, default=""),
            radius_groups=dict(type='list', elements='str', required=False, default=[]),
            tacas_groups=dict(type='list', elements='str', required=False, default=[]),
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
