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
    comment:
        description:
          - An optional comment to add to the object
    disable_compression:
        description:
          - Whether to enable the compression
        default: False
    domain:
        description:
          - A list of domain names for the frontend object
        default: []
    exceptions:
        description:
          - A list of exception ref names (reverse_proxy/exception)
        default: []
    htmlrewrite:
        description:
          - whether to enable html rewrite or not
        default: False
    htmlrewrite_cookie:
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
        default: False
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
        default: False
    xheader:
        description:
          - whether to pass the host header or not
        default: False

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
# Create a proxy_frontend entry
- name: utm proxy_frontend
  utm_proxy_backend:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestBackendEntry
    host: REF_OBJECT_STRING
    state: present

# Remove a proxy_backend entry
- name: utm proxy_backend
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
"""


def main():
    endpoint = "reverse_proxy/frontend"
    key_to_check_for_changes = ["comment", "disable_backend_connection_pooling", "host", "keepalive", "path", "port",
                                "ssl", "status", "timeout"]
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            add_content_type_header=dict(type='bool', required=False, default=False),
            address=dict(type='str', required=False, default="REF_DefaultInternalAddress"),
            allowed_networks=dict(type='list', elements='str', required=False, default="REF_NetworkAny"),
            certificate=dict(type='str', required=False, default=""),
            comment=dict(type='str', required=False, default=""),
            disable_compression=dict(type='bool', required=False, default=False),
            domain=dict(type='list', elements='str', required=False),
            exceptions=dict(type='list', elements='str', required=False, default=[]),
            htmlrewrite=dict(type='bool', required=False, default=False),
            htmlrewrite_cookie=dict(type='bool', required=False, default=False),
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
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
