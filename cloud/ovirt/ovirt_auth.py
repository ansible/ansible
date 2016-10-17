#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

try:
    import ovirtsdk4 as sdk
except ImportError:
    pass


DOCUMENTATION = '''
---
module: ovirt_auth
short_description: "Module to manage authentication to oVirt."
author: "Ondra Machacek (@machacekondra)"
version_added: "2.2"
description:
    - "This module authenticates to oVirt engine and creates SSO token, which should be later used in
       all other oVirt modules, so all modules don't need to perform login and logout.
       This module returns an Ansible fact called I(ovirt_auth). Every module can use this
       fact as C(auth) parameter, to perform authentication."
options:
    state:
        default: present
        choices: ['present', 'absent']
        description:
            - "Specifies if a token should be created or revoked."
    username:
        required: True
        description:
            - "The name of the user. For example: I(admin@internal)."
    password:
        required: True
        description:
            - "The password of the user."
    url:
        required: True
        description:
            - "A string containing the base URL of the server.
               For example: I(https://server.example.com/ovirt-engine/api)."
    insecure:
        required: False
        description:
            - "A boolean flag that indicates if the server TLS certificate and host name should be checked."
    ca_file:
        required: False
        description:
            - "A PEM file containing the trusted CA certificates. The
               certificate presented by the server will be verified using these CA
               certificates. If C(ca_file) parameter is not set, system wide
               CA certificate store is used."
    timeout:
        required: False
        description:
            - "The maximum total time to wait for the response, in
               seconds. A value of zero (the default) means wait forever. If
               the timeout expires before the response is received an exception
               will be raised."
    compress:
        required: False
        description:
            - "A boolean flag indicating if the SDK should ask
               the server to send compressed responses. The default is I(True).
               Note that this is a hint for the server, and that it may return
               uncompressed data even when this parameter is set to I(True)."
    kerberos:
        required: False
        description:
            - "A boolean flag indicating if Kerberos authentication
               should be used instead of the default basic authentication."
notes:
  - "Everytime you use ovirt_auth module to obtain ticket, you need to also revoke the ticket,
     when you no longer need it, otherwise the ticket would be revoked by engine when it expires.
     For an example of how to achieve that, please take a look at I(examples) section."
'''

EXAMPLES = '''
tasks:
  - block:
       # Create a vault with `ovirt_password` variable which store your
       # oVirt user's password, and include that yaml file with variable:
       - include_vars: ovirt_password.yml

       - name: Obtain SSO token with using username/password credentials:
         ovirt_auth:
           url: https://ovirt.example.com/ovirt-engine/api
           username: admin@internal
           ca_file: ca.pem
           password: "{{ ovirt_password }}"

       # Previous task generated I(ovirt_auth) fact, which you can later use
       # in different modules as follows:
       - ovirt_vms:
           auth: "{{ ovirt_auth }}"
           state: absent
           name: myvm

      always:
        - name: Always revoke the SSO token
          ovirt_auth:
            state: absent
            ovirt_auth: "{{ ovirt_auth }}"
'''

RETURN = '''
ovirt_auth:
    description: Authentication facts, needed to perform authentication to oVirt.
    returned: success
    type: dictionary
    contains:
        token:
            description: SSO token which is used for connection to oVirt engine.
            returned: success
            type: string
            sample: "kdfVWp9ZgeewBXV-iq3Js1-xQJZPSEQ334FLb3eksoEPRaab07DhZ8ED8ghz9lJd-MQ2GqtRIeqhvhCkrUWQPw"
        url:
            description: URL of the oVirt engine API endpoint.
            returned: success
            type: string
            sample: "https://ovirt.example.com/ovirt-engine/api"
        ca_file:
            description: CA file, which is used to verify SSL/TLS connection.
            returned: success
            type: string
            sample: "ca.pem"
        insecure:
            description: Flag indicating if insecure connection is used.
            returned: success
            type: bool
            sample: False
        timeout:
            description: Number of seconds to wait for response.
            returned: success
            type: int
            sample: 0
        compress:
            description: Flag indicating if compression is used for connection.
            returned: success
            type: bool
            sample: True
        kerberos:
            description: Flag indicating if kerberos is used for authentication.
            returned: success
            type: bool
            sample: False
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(default=None),
            username=dict(default=None),
            password=dict(default=None, no_log=True),
            ca_file=dict(default=None, type='path'),
            insecure=dict(required=False, type='bool', default=False),
            timeout=dict(required=False, type='int', default=0),
            compress=dict(required=False, type='bool', default=True),
            kerberos=dict(required=False, type='bool', default=False),
            state=dict(default='present', choices=['present', 'absent']),
            ovirt_auth=dict(required=None, type='dict'),
        ),
        required_if=[
            ('state', 'absent', ['ovirt_auth']),
            ('state', 'present', ['username', 'password', 'url']),
        ],
    )
    check_sdk(module)

    state = module.params.get('state')
    if state == 'present':
        params = module.params
    elif state == 'absent':
        params = module.params['ovirt_auth']

    connection = sdk.Connection(
        url=params.get('url'),
        username=params.get('username'),
        password=params.get('password'),
        ca_file=params.get('ca_file'),
        insecure=params.get('insecure'),
        timeout=params.get('timeout'),
        compress=params.get('compress'),
        kerberos=params.get('kerberos'),
        token=params.get('token'),
    )
    try:
        token = connection.authenticate()
        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_auth=dict(
                    token=token,
                    url=params.get('url'),
                    ca_file=params.get('ca_file'),
                    insecure=params.get('insecure'),
                    timeout=params.get('timeout'),
                    compress=params.get('compress'),
                    kerberos=params.get('kerberos'),
                ) if state == 'present' else dict()
            )
        )
    except Exception as e:
        module.fail_json(msg="Error: %s" % e)
    finally:
        # Close the connection, but don't revoke token
        connection.close(logout=state == 'absent')


from ansible.module_utils.basic import *
from ansible.module_utils.ovirt import *
if __name__ == "__main__":
    main()
