#!/usr/bin/python

from __future__ import absolute_import, division, print_function

from lib.ansible.module_utils.utm_utils import UTM, UTMModule

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

short_description: create, update or destroy reverse_proxy backend entry in Sophos UTM

description:
    - Create, update or destroy a reverse_proxy backend entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.7" 

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    disable_backend_connection_pooling:
        description:
          - whether to disable the backend connection pooling
        default: False
    host:
        description:
          - The reference name of the host object. Can be determined with utm_dns_entry
    comment:
        description:
          - An optional comment to add to the object
    keepalive:
        description:
          - Whether to enable the http keepalive
        default: False
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
          - whether to enable ssl or not
        default: False
    status: 
        description:
          - the status of the entry
        default: True
    timeout: 
        description:
          - The keepalive timeout in seconds
        default: 300

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
# Create a proxy_backend entry
- name: utm proxy_backend
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
        ),
        supports_check_mode=False
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
