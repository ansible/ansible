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
module: utm_proxy_backend

author:
    - Johannes Brunswicker (@MatrixCrawler)

short_description: Create, update or destroy reverse_proxy backend entry in Sophos UTM

description:
    - Create, update or destroy a reverse_proxy backend entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: True
    disable_backend_connection_pooling:
        description:
          - Whether to disable the backend connection pooling
        default: False
        type: bool
    host:
        description:
          - The reference name of the host object. Can be determined with utm_dns_entry.\n
            One of network/dns_host, network/dns_group, network/host
    comment:
        description:
          - An optional comment to add to the object
    keepalive:
        description:
          - Whether to enable the http keepalive
        default: False
        type: bool
    path:
        description:
          - The path for the site path routing
        default: /
    port:
        description:
          - The port of the backend service
        default: 80
    ssl:
        description:
          - Whether to enable ssl or not
        default: False
        type: bool
    status:
        description:
          - The status of the entry
        default: True
        type: bool
    timeout:
        description:
          - The keepalive timeout in seconds
        default: 300

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Create UTM proxy_backend
  utm_proxy_backend:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestBackendEntry
    host: REF_OBJECT_STRING
    state: present

- name: Remove UTM proxy_backend
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
        disable_backend_connection_pooling:
            description: Whether the backend connection pooling is enabled or disabled
            type: bool
        host:
            description: The reference name of the host object
            type: string
        comment:
            description: The comment string
            type: string
        keepalive:
            description: Whether connection keepalive is activated or not
            type: bool
        path:
            description: The backend path
            type: string
        port:
            description: The port the backend is connected to
            type: int
        ssl:
            description: Whether to use SSL or not
            type: bool
        status:
            description: Whether the backend is active or not
            type: bool
        timeout:
            description: The timeout for http keepalive
            type: int
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "reverse_proxy/backend"
    key_to_check_for_changes = ["comment", "disable_backend_connection_pooling", "host", "keepalive", "path", "port",
                                "ssl", "status", "timeout"]
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            disable_backend_connection_pooling=dict(type='bool', required=False, default=False),
            host=dict(type='str', required=False),
            comment=dict(type='str', required=False, default=""),
            keepalive=dict(type='bool', required=False, default=False),
            path=dict(type='str', required=False, default="/"),
            port=dict(type='int', required=False, default=80),
            ssl=dict(type='bool', required=False, default=False),
            status=dict(type='bool', required=False, default=True),
            timeout=dict(type='int', required=False, default=300),
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
