#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Bernat Mut <bernat.mut@aireuropa.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: pmp
version_added: "2.5"
short_description: Create and modify accounts and resources in Password Manager Pro (PMP)
description:
  - This allows to create a resource with an account inside Password Manager Pro (PMP).

options:
  uri:
    required: true
    description:
      - Base URI for the PMP instance.
  port:
    required: false
    default:  7272
    description:
      - Base URI for the PMP instance.
  operation:
    required: true
    aliases: [ command ]
    choices: [ create_host ]
    description:
      - The operation to perform.

  token:
    required: true
    description:
      - Token of the API user that performs the action

  group:
    required: false
    description:
      - If exists set the main group of the host.

  resource_name:
    required: true
    description:
     - The name of the resource that will be created.

  account_name:
    required: true
    description:
     - User associated with the created resource.

  password:
    required: true
    description:
     - Password asociated with the user_name.

  owner:
    required: true
    description:
     - Change the default owner, must be an exising user.

  use_proxy:
    required: false
    description:
      - Set if open_url must use proxy
  validate_certs:
    required: false
    description:
      - Set if open_url must validate certificates

author: "Bernat Mut (@berni69)"
"""

EXAMPLES = """
# Retrieve a password:
- name: Retrieve Password
  pmp:
    uri: '{{ pmp_server }}'
    port: '{{ pmp_port }}'
    token: '{{ user_token }}'
    command: 'get_password'
    resource_name: '{{ server_name }}'
    account_name: '{{ user_name }}'
  register: issue

- name: Create server host
  pmp:
    uri: '{{ pmp_server }}'
    port: '{{ pmp_port }}'
    token: '{{ user_token }}'
    resource_name: '{{ server_name }}'
    group: '{{ my_group}}'
    account_name: '{{ user_name }}'
    password: '{{ password }}'
    owner: 'DOMAIN\\USER'

"""

RETURN = '''
status:
    description: status of action executed
    returned: success
    type: string
    sample: 'OK'
password:
    description: password retrieved
    returned: success
    type: string
    sample: "123456"
'''

import json
import urllib
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url


class PasswordManagerPro:

    def format(self, strr):
        for key, value in self.data.items():
            strr = strr.replace('{' + key + '}', value)
        return strr

    def __init__(self, token="", host="", port="", use_proxy=False, validate_certs=True):
        self.data = {'TOKEN': token, 'HOST': host, 'PORT': port}
        self.use_proxy = use_proxy
        self.validate_certs = validate_certs

    def get_resources(self):
        url = self.format('https://{HOST}:{PORT}/restapi/json/v1/resources?AUTHTOKEN={TOKEN}')
        return json.loads(open_url(url, validate_certs=self.validate_certs, use_proxy=self.use_proxy).read())

    def get_accounts_resource(self):
        url = self.format('https://{HOST}:{PORT}/restapi/json/v1/resources/{resourceId}/accounts?AUTHTOKEN={TOKEN}')
        return \
            json.loads(open_url(url, validate_certs=self.validate_certs, use_proxy=self.use_proxy).read())['operation'][
                'Details']['ACCOUNT LIST']

    def get_account_resource_by_name(self, username):
        url = self.format('https://{HOST}:{PORT}/restapi/json/v1/resources/{resourceId}/accounts?AUTHTOKEN={TOKEN}')
        accounts = \
            json.loads(open_url(url, validate_certs=self.validate_certs, use_proxy=self.use_proxy).read())['operation'][
                'Details']['ACCOUNT LIST']
        for acc in accounts:
            if acc['ACCOUNT NAME'] == username:
                return acc
        raise RuntimeError('ACCOUNT not found!')

    def get_account_password(self):
        url = self.format(
            'https://{HOST}:{PORT}/restapi/json/v1/resources/{resourceId}/accounts/{accountId}/password?AUTHTOKEN={TOKEN}')
        res = json.loads(open_url(url, validate_certs=self.validate_certs, use_proxy=self.use_proxy).read())[
            'operation']
        status = res['result']['status']
        if status == 'Failed':
            raise RuntimeError(res['result']['message'])
        return res['Details']['PASSWORD']

    def get_resource_by_name(self, name):
        url = self.format('https://{HOST}:{PORT}/restapi/json/v1/resources?AUTHTOKEN={TOKEN}')
        resources = json.loads(open_url(url, validate_certs=self.validate_certs, use_proxy=self.use_proxy).read())
        for res in resources['operation']['Details']:
            if res['RESOURCE NAME'] == name:
                return res
        raise RuntimeError('RESOURCE not found!')

    def get_password(self, server, username):
        resource = self.get_resource_by_name(server)
        self.data['resourceId'] = resource['RESOURCE ID']
        account = self.get_account_resource_by_name(username)
        self.data['accountId'] = account['ACCOUNT ID']
        return self.get_account_password()

    def create_resource(self, resourcename, accountname, password, ownername, resource_type='Linux', group=''):
        data = {
            "operation": {
                "Details": {
                    "RESOURCENAME": resourcename,
                    "ACCOUNTNAME": accountname,
                    "RESOURCETYPE": resource_type,
                    "PASSWORD": password,
                    "OWNERNAME": ownername,
                }
            }
        }
        if group:
            data["operation"]["Details"]["RESOURCEGROUPNAME"] = group
        headers = {
            'Content-Type': 'text/json',
        }  # admin test

        url = self.format('https://{HOST}:{PORT}/restapi/json/v1/resources?AUTHTOKEN={TOKEN}')
        data = json.dumps(data, sort_keys=False)
        params = urllib.urlencode({'INPUT_DATA': data})
        r = open_url(url, method="POST", headers=headers, data=params, validate_certs=self.validate_certs,
                     use_proxy=self.use_proxy)
        res = json.loads(r.read())['operation']['result']
        status = res['status']
        if status == 'Failed':
            raise RuntimeError(res['message'])
        return status


def get_password(params):
    pmp = PasswordManagerPro(params['token'], params['uri'], params['port'], params['use_proxy'],
                             params['validate_certs'])
    password = pmp.get_password(params['resource_name'], params['account_name'])
    return {'status': 'OK', 'password': password}


def create_host(params):
    pmp = PasswordManagerPro(params['token'], params['uri'], params['port'], params['use_proxy'],
                             params['validate_certs'])
    status = pmp.create_resource(params['resource_name'], params['account_name'], params['password'], params['owner'],
                                 group=params['group'])
    return {'status': status}


# Defining a set of operations
OPERATIONS = {'get_password': get_password, 'create_host': create_host}


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            uri=dict(required=True),
            port=dict(required=False, default="7272"),
            operation=dict(choices=['get_password', 'create_host'],
                           aliases=['command'], required=True),
            token=dict(required=True, no_log=True),
            resource_name=dict(),
            account_name=dict(),
            password=dict(no_log=True),
            owner=dict(),
            group=dict(),
            use_proxy=dict(default=True, type='bool'),
            validate_certs=dict(default=True, type='bool'),
        ),
        required_if=[
            ('operation', 'create_host', ['resource_name', 'account_name', 'password', 'owner']),
            ('operation', 'get_password', ['resource_name', 'account_name']),
        ],
        supports_check_mode=False
    )

    op = module.params['operation']
    # Dispatch
    try:
        ret = OPERATIONS[op](module.params)
    except Exception as e:
        return module.fail_json(msg=e.message)

    module.exit_json(changed=True, meta=ret)


if __name__ == '__main__':
    main()
