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
module: utm_proxy_frontend

author:
    - Johannes Brunswicker (@MatrixCrawler)

short_description: create, update or destroy reverse_proxy frontend entry in Sophos UTM

description:
    - Create, update or destroy a reverse_proxy frontend entry in Sophos UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    add_content_type_header :
        description:
          - Whether to add the content type header or not
        type: bool
        default: False
    address:
        description:
          - The reference name of the network/interface_address object.
        default: REF_DefaultInternalAddress
    allowed_networks:
        description:
          - A list of reference names for the allowed networks.
        default: ['REF_NetworkAny']
    certificate:
        description:
          - The reference name of the ca/host_key_cert object.
        default: ""
    comment:
        description:
          - An optional comment to add to the object
        default: ""
    disable_compression:
        description:
          - Whether to enable the compression
        type: bool
        default: False
    domain:
        description:
          - A list of domain names for the frontend object
    exceptions:
        description:
          - A list of exception ref names (reverse_proxy/exception)
        default: []
    htmlrewrite:
        description:
          - Whether to enable html rewrite or not
        type: bool
        default: False
    htmlrewrite_cookies:
        description:
          - Whether to enable html rewrite cookie or not
        type: bool
        default: False
    implicitredirect:
        description:
          - Whether to enable implicit redirection or not
        type: bool
        default: False
    lbmethod:
        description:
          - Which loadbalancer method should be used
        choices:
          - ""
          - bybusyness
          - bytraffic
          - byrequests
        default: bybusyness
    locations:
        description:
          - A list of location ref names (reverse_proxy/location)
        default: []
    port:
        description:
          - The frontend http port
        default: 80
    preservehost:
        description:
          - Whether to preserve host header
        type: bool
        default: False
    profile:
        description:
          - The reference string of the reverse_proxy/profile
        default: ""
    status:
        description:
          - Whether to activate the frontend entry or not
        type: bool
        default: True
    type:
        description:
          - Which protocol should be used
        choices:
          - http
          - https
        default: http
    xheaders:
        description:
          - Whether to pass the host header or not
        type: bool
        default: False

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Create utm proxy_frontend
  utm_proxy_frontend:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestFrontendEntry
    host: REF_OBJECT_STRING
    state: present

- name: Remove utm proxy_frontend
  utm_proxy_frontend:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestFrontendEntry
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
            description: Whether the html rewrite cookie will be set
            type: bool
        implicitredirect:
            description: Whether to use implicit redirection
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
    key_to_check_for_changes = ["add_content_type_header", "address", "allowed_networks", "certificate",
                                "comment", "disable_compression", "domain", "exceptions", "htmlrewrite",
                                "htmlrewrite_cookies", "implicitredirect", "lbmethod", "locations",
                                "port", "preservehost", "profile", "status", "type", "xheaders"]
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            add_content_type_header=dict(type='bool', required=False, default=False),
            address=dict(type='str', required=False, default="REF_DefaultInternalAddress"),
            allowed_networks=dict(type='list', elements='str', required=False, default=["REF_NetworkAny"]),
            certificate=dict(type='str', required=False, default=""),
            comment=dict(type='str', required=False, default=""),
            disable_compression=dict(type='bool', required=False, default=False),
            domain=dict(type='list', elements='str', required=False),
            exceptions=dict(type='list', elements='str', required=False, default=[]),
            htmlrewrite=dict(type='bool', required=False, default=False),
            htmlrewrite_cookies=dict(type='bool', required=False, default=False),
            implicitredirect=dict(type='bool', required=False, default=False),
            lbmethod=dict(type='str', required=False, default="bybusyness",
                          choices=['bybusyness', 'bytraffic', 'byrequests', '']),
            locations=dict(type='list', elements='str', required=False, default=[]),
            port=dict(type='int', required=False, default=80),
            preservehost=dict(type='bool', required=False, default=False),
            profile=dict(type='str', required=False, default=""),
            status=dict(type='bool', required=False, default=True),
            type=dict(type='str', required=False, default="http", choices=['http', 'https']),
            xheaders=dict(type='bool', required=False, default=False),
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
