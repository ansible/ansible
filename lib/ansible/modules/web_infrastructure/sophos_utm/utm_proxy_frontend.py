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
    - Create, update or destroy a reverse_proxy frontend entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.7" 

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    add_content_type_header :
        description:
          - whether to add he content type header or not 
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
          - whether to enable html rewrite or not
        default: False
    htmlrewrite_cookies:
        description:
          - whether to enable html rewrite cookie or not
        default: False
    implicitredirect:
        description:
          - whether to enable implicit redirection or not
        default: False
    lbmethod:
        description:
          - which loadbalancer method should be used
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
          - whether to preserve host header
        default: False
    profile:
        description:
          - the reference string of the reverse_proxy/profile
        default: ""
    status:
        description:
          - whether to activate the frontend entry or not
        default: True
    type:
        description:
          - which protocol should be used
        choices:
          - http
          - https
        default: http
    xheaders:
        description:
          - whether to pass the host header or not
        default: False

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Create utm proxy_frontend
  utm_proxy_backend:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestBackendEntry
    host: REF_OBJECT_STRING
    state: present

- name: Remove utm proxy_backend
  utm_proxy_backend:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestBackendEntry
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
