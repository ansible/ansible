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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_auth
short_description: "Module to manage authentication to oVirt/RHV"
author: "Ondra Machacek (@machacekondra)"
version_added: "2.2"
description:
    - "This module authenticates to oVirt/RHV engine and creates SSO token, which should be later used in
       all other oVirt/RHV modules, so all modules don't need to perform login and logout.
       This module returns an Ansible fact called I(ovirt_auth). Every module can use this
       fact as C(auth) parameter, to perform authentication."
options:
    state:
        default: present
        choices: ['present', 'absent']
        description:
            - "Specifies if a token should be created or revoked."
    username:
        required: False
        description:
            - "The name of the user. For example: I(admin@internal)
               Default value is set by I(OVIRT_USERNAME) environment variable."
    password:
        required: False
        description:
            - "The password of the user. Default value is set by I(OVIRT_PASSWORD) environment variable."
    token:
        required: False
        description:
            - "SSO token to be used instead of login with username/password.
               Default value is set by I(OVIRT_TOKEN) environment variable."
        version_added: 2.5
    url:
        required: False
        description:
            - "A string containing the API URL of the server.
               For example: I(https://server.example.com/ovirt-engine/api).
               Default value is set by I(OVIRT_URL) environment variable."
            - "Either C(url) or C(hostname) is required."
    hostname:
        required: False
        description:
            - "A string containing the hostname of the server.
               For example: I(server.example.com).
               Default value is set by I(OVIRT_HOSTNAME) environment variable."
            - "Either C(url) or C(hostname) is required."
        version_added: "2.6"
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
               CA certificate store is used.
               Default value is set by I(OVIRT_CAFILE) environment variable."
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

    headers:
        required: False
        description:
            - "A dictionary of HTTP headers to be added to each API call."
        version_added: "2.4"

requirements:
  - python >= 2.7
  - ovirt-engine-sdk-python >= 4.2.4
notes:
  - "Everytime you use ovirt_auth module to obtain ticket, you need to also revoke the ticket,
     when you no longer need it, otherwise the ticket would be revoked by engine when it expires.
     For an example of how to achieve that, please take a look at I(examples) section."
  - "In order to use this module you have to install oVirt/RHV Python SDK.
     To ensure it's installed with correct version you can create the following task:
     I(pip: name=ovirt-engine-sdk-python version=4.2.4)"
  - "Note that in oVirt/RHV 4.1 if you want to use a user which is not administrator
     you must enable the I(ENGINE_API_FILTER_BY_DEFAULT) variable in engine. In
     oVirt/RHV 4.2 and later it's enabled by default."
'''

EXAMPLES = '''
  - block:
       # Create a vault with `ovirt_password` variable which store your
       # oVirt/RHV user's password, and include that yaml file with variable:
       - include_vars: ovirt_password.yml

       - name: Obtain SSO token with using username/password credentials
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

# When user will set following environment variables:
#   OVIRT_URL = https://fqdn/ovirt-engine/api
#   OVIRT_USERNAME = admin@internal
#   OVIRT_PASSWORD = the_password
# He can login the oVirt using environment variable instead of variables
# in yaml file.
# This is mainly usefull when using Ansible Tower or AWX, as it will work
# for Red Hat Virtualization creadentials type.
  - name: Obtain SSO token
    ovirt_auth:
      state: present
'''

RETURN = '''
ovirt_auth:
    description: Authentication facts, needed to perform authentication to oVirt/RHV.
    returned: success
    type: complex
    contains:
        token:
            description: SSO token which is used for connection to oVirt/RHV engine.
            returned: success
            type: string
            sample: "kdfVWp9ZgeewBXV-iq3Js1-xQJZPSEQ334FLb3eksoEPRaab07DhZ8ED8ghz9lJd-MQ2GqtRIeqhvhCkrUWQPw"
        url:
            description: URL of the oVirt/RHV engine API endpoint.
            returned: success
            type: string
            sample: "https://ovirt.example.com/ovirt-engine/api"
        ca_file:
            description: CA file, which is used to verify SSL/TLS connection.
            returned: success
            type: path
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
        headers:
            description: Dictionary of HTTP headers to be added to each API call.
            returned: success
            type: dict
'''

import os
import traceback

try:
    import ovirtsdk4 as sdk
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import check_sdk


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(default=None),
            hostname=dict(default=None),
            username=dict(default=None),
            password=dict(default=None, no_log=True),
            ca_file=dict(default=None, type='path'),
            insecure=dict(required=False, type='bool', default=None),
            timeout=dict(required=False, type='int', default=0),
            compress=dict(required=False, type='bool', default=True),
            kerberos=dict(required=False, type='bool', default=False),
            headers=dict(required=False, type='dict'),
            state=dict(default='present', choices=['present', 'absent']),
            token=dict(default=None),
            ovirt_auth=dict(required=None, type='dict'),
        ),
        required_if=[
            ('state', 'absent', ['ovirt_auth']),
        ],
        supports_check_mode=True,
    )
    check_sdk(module)

    state = module.params.get('state')
    if state == 'present':
        params = module.params
    elif state == 'absent':
        params = module.params['ovirt_auth']

    def get_required_parameter(param, env_var, required=False):
        var = params.get(param) or os.environ.get(env_var)
        if not var and required and state == 'present':
            module.fail_json(msg="'%s' is a required parameter." % param)

        return var

    url = get_required_parameter('url', 'OVIRT_URL', required=False)
    hostname = get_required_parameter('hostname', 'OVIRT_HOSTNAME', required=False)
    if url is None and hostname is None:
        module.fail_json(msg="You must specify either 'url' or 'hostname'.")

    if url is None and hostname is not None:
        url = 'https://{0}/ovirt-engine/api'.format(hostname)

    username = get_required_parameter('username', 'OVIRT_USERNAME', required=True)
    password = get_required_parameter('password', 'OVIRT_PASSWORD', required=True)
    token = get_required_parameter('token', 'OVIRT_TOKEN')
    ca_file = get_required_parameter('ca_file', 'OVIRT_CAFILE')
    insecure = params.get('insecure') if params.get('insecure') is not None else not bool(ca_file)

    connection = sdk.Connection(
        url=url,
        username=username,
        password=password,
        ca_file=ca_file,
        insecure=insecure,
        timeout=params.get('timeout'),
        compress=params.get('compress'),
        kerberos=params.get('kerberos'),
        headers=params.get('headers'),
        token=token,
    )
    try:
        token = connection.authenticate()
        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_auth=dict(
                    token=token,
                    url=url,
                    ca_file=ca_file,
                    insecure=insecure,
                    timeout=params.get('timeout'),
                    compress=params.get('compress'),
                    kerberos=params.get('kerberos'),
                    headers=params.get('headers'),
                ) if state == 'present' else dict()
            )
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        # Close the connection, but don't revoke token
        connection.close(logout=state == 'absent')


if __name__ == "__main__":
    main()
