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
module: utm_authentication_ldap

author:
    - Johannes Brunswicker (@MatrixCrawler)

short_description: create, update or destroy authentication LDAP server frontend entry in Sophos UTM

description:
    - Create, update or destroy a authentication frontend entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
            - The name of the object. Will be used to identify the entry
        required: True
        type: str
    backend:
        description:
            - The backend to use
        choices:
            - 'edirectory'
            - 'adirectory'
            - 'ldap'
            - 'radius'
            - 'tacacs'
        required: False
        type: str
    base_dn:
        description:
            - LDAP base_dn to be used
        type: str
    bind_dn:
        description:
            - Bind_dn used for the connection to the LDAP server
        type: str
    bind_pw:
        description:
            - Password for the bind_dn
        type: str
    comment:
        description:
            - The comment string
        type: str
    port:
        description:
            - The port used for the connection
        default: 389
        type: int
    prefetch_backend_sync:
        description:
            - Enable or disable prefetch backend sync
        default: False
        type: bool
    prefetch_contexts:
        description:
            - TBA
        default: []
        type: list
    prefetch_interval:
        description:
            - TBA
        default: []
        type: list
    sasl:
        description:
            - En- or disable SASL
        default: False
        type: bool
    server:
        description:
            - The server to use
        required: True
        type: str
    ssl:
        description:
            - Configure SSL for the connection
        default: False
        type: bool
    status:
        description:
            - Status of the entry
        required: False
        default: False
        type: bool
    timeout:
        description:
            - Timeout for the server connection
        default: 10
        type: int
    user_attrib:
        description:
            - Type of userstring used to authenticate at the LDAP server
        default: 'cn'
        type: str

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Create UTM authentication_ldap
  utm_authentication_ldap:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestAuthenticationLDAP
    base_dn: "dc=domain,dc=local"
    bind_dn: "cn=ro_user,dc=domain,dc=local"
    bind_pw: "some_password"
    comment: "Some comments"
    port: 636
    prefetch_backend_sync: false
    sasl: true
    ssl: true
    timeout: 20
    user_attrib: uid
    state: present

- name: Remove UTM authentication_ldap
  utm_authentication_ldap:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestAuthenticationLDAP
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
        server:
            description: This is the reference to the DNS host entry. DO NOT CHANGE IT
            type: string
        backend :
            description: Type of backend used for authentication. In this case it stays empty.
            type: string
        status:
            description: TBA
            type: boolean
        base_dn:
            description: LDAP base_dn to be used
            type: string
        bind_dn:
            description: Bind_dn used for the connection to the LDAP server
            type: string
        bind_pw:
            description: Password for the bind_dn
            type: string
        comment:
            description: The comment string
            type: string
        port:
            description: The port used for the connection
            type: integer
        prefetch_backend_sync:
            description: Enable or disable prefetch backend sync
            type: boolean
        prefetch_contexts:
            description: TBA
            type: list
        prefetch_interval:
            description: TBA
            type: list
        sasl:
            description: En- or disable SASL
            type: boolean
        ssl:
            description: configure SSL for the connection
            type: boolean
        timeout:
            description: Timeout for the server connection
            type: integer
        user_attrib:
            description: Type of userstring used to authenticate at the LDAP server
            type: string
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "authentication/ldap"
    key_to_check_for_changes = ["comment", "base_dn", "bind_dn", "bind_pw", "port",
                                "prefetch_backend_sync", "prefetch_contexts", "prefetch_interval", "sasl", "ssl",
                                "timeout"]
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            backend=dict(type='str', required=False, default="", choices=['edirectory', 'adirectory', 'ldap', 'radius', 'tacacs']),
            base_dn=dict(type='str', required=True),
            bind_dn=dict(type='str', required=True),
            bind_pw=dict(type='str', required=True),
            comment=dict(type='str', required=False, default=""),
            port=dict(type='int', required=False, default=389),
            prefetch_backend_sync=dict(type='bool', required=False, default=False),
            prefetch_contexts=dict(type='list', elements='str', required=False, default=[]),
            prefetch_interval=dict(type='list', elements='str', required=False, default=[]),
            sasl=dict(type='bool', required=False, default=False),
            server=dict(type='str', required=True),
            ssl=dict(type='bool', required=False, default=False),
            status=dict(type='bool', required=False, default=False),
            timeout=dict(type='int', required=False, default=10),
            user_attrib=dict(type='str', required=False, default="cn"),
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
