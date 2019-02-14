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
module: utm_dns_host

author:
    - Johannes Brunswicker (@MatrixCrawler)

short_description: create, update or destroy dns entry in Sophos UTM

description:
    - Create, update or destroy a dns entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    address:
        description:
          - The IPV4 Address of the entry. Can be left empty for automatic resolving.
        default: 0.0.0.0
    address6:
        description:
          - The IPV6 Address of the entry. Can be left empty for automatic resolving.
        default: "::"
    comment:
        description:
          - An optional comment to add to the dns host object
    hostname:
        description:
          - The hostname for the dns host object
    interface:
        description:
          - The reference name of the interface to use. If not provided the default interface will be used
    resolved:
        description:
          - whether the hostname's ipv4 address is already resolved or not
        default: False
        type: bool
    resolved6:
        description:
          - whether the hostname's ipv6 address is already resolved or not
        default: False
        type: bool
    timeout:
        description:
          - the timeout for the utm to resolve the ip address for the hostname again
        default: 0

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Create UTM dns host entry
  utm_dns_host:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestDNSEntry
    hostname: testentry.some.tld
    state: present

- name: Remove UTM dns host entry
  utm_dns_host:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestDNSEntry
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
        name:
            description: The name of the object
            type: str
        address:
            description: The ipv4 address of the object
            type: str
        address6:
            description: The ipv6 address of the object
            type: str
        comment:
            description: The comment string
            type: str
        hostname:
            description: The hostname of the object
            type: str
        interface:
            description: The reference name of the interface the object is associated with
            type: str
        resolved:
            description: Whether the ipv4 address is resolved or not
            type: bool
        resolved6:
            description: Whether the ipv6 address is resolved or not
            type: bool
        timeout:
            description: The timeout until a new resolving will be attempted
            type: int
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "network/dns_host"
    key_to_check_for_changes = ["comment", "hostname", "interface"]
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            address=dict(type='str', required=False, default='0.0.0.0'),
            address6=dict(type='str', required=False, default='::'),
            comment=dict(type='str', required=False, default=""),
            hostname=dict(type='str', required=False),
            interface=dict(type='str', required=False, default=""),
            resolved=dict(type='bool', required=False, default=False),
            resolved6=dict(type='bool', required=False, default=False),
            timeout=dict(type='int', required=False, default=0),
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
