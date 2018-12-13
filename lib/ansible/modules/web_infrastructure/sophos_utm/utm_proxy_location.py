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
module: utm_proxy_location

author:
    - Johannes Brunswicker (@MatrixCrawler)

short_description: create, update or destroy reverse_proxy location entry in Sophos UTM

description:
    - Create, update or destroy a reverse_proxy location entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    access_control:
        description:
          - whether to activate the access control for the location
        type: str
        default: '0'
        choices:
          - '0'
          - '1'
    allowed_networks:
        description:
          - A list of allowed networks
        type: list
        default: REF_NetworkAny
    auth_profile:
        description:
          - The reference name of the auth profile
    backend:
        description:
          - A list of backends that are connected with this location declaration
        default: []
    be_path:
        description:
          - The path of the backend
    comment:
        description:
          - The optional comment string
    denied_networks:
        description:
          - A list of denied network references
        default: []
    hot_standby:
        description:
          - Activate hot standby mode
        type: bool
        default: False
    path:
        description:
          - The path of the location
        default: "/"
    status:
        description:
          - Whether the location is active or not
        type: bool
        default: True
    stickysession_id:
        description:
          - The stickysession id
        default: ROUTEID
    stickysession_status:
        description:
          - Enable the stickysession
        type: bool
        default: False
    websocket_passthrough:
        description:
          - Enable the websocket passthrough
        type: bool
        default: False

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Create UTM proxy_location
  utm_proxy_backend:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestLocationEntry
    backend: REF_OBJECT_STRING
    state: present

- name: Remove UTM proxy_location
  utm_proxy_backend:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestLocationEntry
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
        access_control:
            description: Whether to use access control state
            type: string
        allowed_networks:
            description: List of allowed network reference names
            type: list
        auth_profile:
            description: The auth profile reference name
            type: string
        backend:
            description: The backend reference name
            type: string
        be_path:
            description: The backend path
            type: string
        comment:
            description: The comment string
            type: string
        denied_networks:
            description: The list of the denied network names
            type: list
        hot_standby:
            description: Use hot standy
            type: bool
        path:
            description: Path name
            type: string
        status:
            description: Whether the object is active or not
            type: boolean
        stickysession_id:
            description: The identifier of the stickysession
            type: string
        stickysession_status:
            description: Whether to use stickysession or not
            type: bool
        websocket_passthrough:
            description: Whether websocket passthrough will be used or not
            type: bool
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "reverse_proxy/location"
    key_to_check_for_changes = ["access_control", "allowed_networks", "auth_profile", "backend", "be_path", "comment",
                                "denied_networks", "hot_standby", "path", "status", "stickysession_id",
                                "stickysession_status", "websocket_passthrough"]
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            access_control=dict(type='str', required=False, default="0", choices=['0', '1']),
            allowed_networks=dict(type='list', elements='str', required=False, default=['REF_NetworkAny']),
            auth_profile=dict(type='str', required=False, default=""),
            backend=dict(type='list', elements='str', required=False, default=[]),
            be_path=dict(type='str', required=False, default=""),
            comment=dict(type='str', required=False, default=""),
            denied_networks=dict(type='list', elements='str', required=False, default=[]),
            hot_standby=dict(type='bool', required=False, default=False),
            path=dict(type='str', required=False, default="/"),
            status=dict(type='bool', required=False, default=True),
            stickysession_id=dict(type='str', required=False, default='ROUTEID'),
            stickysession_status=dict(type='bool', required=False, default=False),
            websocket_passthrough=dict(type='bool', required=False, default=False),
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
