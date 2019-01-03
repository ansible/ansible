#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Itential <opensource@itential.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
This module provides the token for Itential Automation Platform
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: iap_token
version_added: "2.8"
author: "Itential (@cma0) <opensource@itential.com>"
short_description: Get token for the Itential Automation Platform
description:
  - Checks the connection to IAP and retrieves a login token.
options:
  iap_port:
    description:
      - Provide the port number for the Itential Automation Platform
    required: true
    default: null

  iap_fqdn:
    description:
      - Provide the fqdn or ip-address for the Itential Automation Platform
    required: true
    default: null

  username:
    description:
      - Provide the username for the Itential Automation Platform
    required: true
    default: null

  password:
    description:
      - Provide the password for the Itential Automation Platform
    required: true
    default: null

  https:
    description:
      - Use HTTPS to connect
      - By default using http
    type: bool
    default: False

  validate_certs:
    description:
      - If C(no), SSL certificates for the target url will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    type: bool
    default: False
"""

EXAMPLES = '''
- name: Get token for the Itential Automation Platform
  iap_token:
    iap_port: 3000
    iap_fqdn: localhost
    username: myusername
    password: mypass
  register: result

- debug: var=result.token
'''

RETURN = '''
token:
    description: The token acquired from the Itential Automation Platform
    type: str
    returned: always
'''
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def get_token(module):
    """
    :param module:
    :return: token
    """
    # defaulting the value for transport_protocol to be : http
    transport_protocol = 'http'
    if module.params['https'] or module.params['validate_certs'] is True:
        transport_protocol = 'https'

    url = transport_protocol + "://" + module.params['iap_fqdn'] + ":" + module.params['iap_port'] + "/login"
    username = module.params['username']
    password = module.params['password']

    login = {
        "user": {
            "username": username,
            "password": password
        }
    }
    json_body = module.jsonify(login)
    headers = {}
    headers['Content-Type'] = 'application/json'

    # Using fetch url instead of requests
    response, info = fetch_url(module, url, data=json_body, headers=headers)
    response_code = str(info['status'])
    if info['status'] not in [200, 201]:
        module.fail_json(msg="Failed to connect to Itential Automation Platform" + response_code)
    response = response.read()
    module.exit_json(changed=True, token=response)


def main():
    """
    :return: token
    """
    # define the available arguments/parameters that a user can pass to
    # the module
    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=dict(
            iap_port=dict(type='int', required=True),
            iap_fqdn=dict(type='str', required=True),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            https=(dict(type='bool', default=False)),
            validate_certs=dict(type='bool', default=False)
        )
    )
    get_token(module)


if __name__ == '__main__':
    main()
