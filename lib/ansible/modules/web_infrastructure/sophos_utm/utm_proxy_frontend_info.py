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
module: utm_proxy_frontend_info

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

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Get utm proxy_frontend
  utm_proxy_frontend_info:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestBackendEntry
    host: REF_OBJECT_STRING
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
        add_content_type_header:
            description: Whether to add the content type header
            type: bool
        address:
            description: The reference name of the address
            type: string
        allowed_networks:
            description: List of reference names of networks associated
            type: list
        certificate:
            description: Reference name of certificate (ca/host_key_cert)
            type: string
        comment:
            description: The comment string
            type: string
        disable_compression:
            description: State of compression support
            type: bool
        domain:
            description: List of hostnames
            type: list
        exceptions:
            description: List of associated proxy exceptions
            type: list
        htmlrewrite:
            description: State of html rewrite
            type: bool
        htmlrewrite_cookies:
            description: whether the html rewrite cookie will be set
            type: bool
        implicitredirect:
            description: whether to use implicit redirection
            type: bool
        lbmethod:
            description: The method of loadbalancer to use
            type: string
        locations:
            description: The reference names of reverse_proxy/locations associated with the object
            type: list
        port:
            description: The port of the frontend connection
            type: int
        preservehost:
            description: Preserve host header
            type: bool
        profile:
            description: The associated reverse_proxy/profile
            type: string
        status:
            description: Whether the frontend object is active or not
            type: bool
        type:
            description: The connection type
            type: string
        xheaders:
            description: The xheaders state
            type: bool
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "reverse_proxy/frontend"
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
