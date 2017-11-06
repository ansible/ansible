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
short_description: Create and modify accounts and groups in Password Manager Pro (PMP)
description:
  - Create and modify accounts and groups in Password Manager Pro (PMP).

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

import json
import sys
import urllib
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url


class PasswordManagerPro:
    data = {
        'HOST': '',
        'PORT': '',
        'TOKEN': '',
    }

    use_proxy = False
    validate_certs = False

    def format(self, strr):
        for key, value in self.data.iteritems():
            strr = strr.replace('{' + key + '}', value)
        return strr

    def __init__(self, args=None):
        if args:
            if 'TOKEN' in args:
                self.data['TOKEN'] = args['TOKEN']
            if 'HOST' in args:
                self.data['HOST'] = args['HOST']
            if 'HOST' in args:
                self.data['PORT'] = args['PORT']
            if 'use_proxy' in args:
                self.use_proxy = args['use_proxy']
            if 'validate_certs' in args:
                self.validate_certs = args['validate_certs']

    def getResources(self):
        url = self.format('https://{HOST}:{PORT}/restapi/json/v1/resources?AUTHTOKEN={TOKEN}')
        return json.loads(open_url(url, validate_certs=self.validate_certs, use_proxy=self.use_proxy).read())

    def getAccountsResource(self):
        url = self.format('https://{HOST}:{PORT}/restapi/json/v1/resources/{resourceId}/accounts?AUTHTOKEN={TOKEN}')
        return json.loads(open_url(url, validate_certs=self.validate_certs, use_proxy=self.use_proxy).read())['operation']['Details']['ACCOUNT LIST']

    def getAccountResourceByName(self, username):
        url = self.format('https://{HOST}:{PORT}/restapi/json/v1/resources/{resourceId}/accounts?AUTHTOKEN={TOKEN}')
        accounts = json.loads(open_url(url, validate_certs=self.validate_certs, use_proxy=self.use_proxy).read())['operation']['Details']['ACCOUNT LIST']
        for acc in accounts:
            if acc['ACCOUNT NAME'] == username:
                return acc
        raise RuntimeError('ACCOUNT not found!')

    def getAccountPwd(self):
        url = self.format(
            'https://{HOST}:{PORT}/restapi/json/v1/resources/{resourceId}/accounts/{accountId}/password?AUTHTOKEN={TOKEN}')
        res = json.loads(open_url(url, validate_certs=self.validate_certs, use_proxy=self.use_proxy).read())['operation']
        status = res['result']['status']
        if status == 'Failed':
            raise RuntimeError(res['result']['message'])
        return res['Details']['PASSWORD']

    def getResourceByName(self, name):
        url = self.format('https://{HOST}:{PORT}/restapi/json/v1/resources?AUTHTOKEN={TOKEN}')
        resources = json.loads(open_url(url, validate_certs=self.validate_certs, use_proxy=self.use_proxy).read())
        for res in resources['operation']['Details']:
            if res['RESOURCE NAME'] == name:
                return res
        raise RuntimeError('RESOURCE not found!')

    def getPassword(self, server, username):
        resource = self.getResourceByName(server)
        self.data['resourceId'] = resource['RESOURCE ID']
        account = self.getAccountResourceByName(username)
        self.data['accountId'] = account['ACCOUNT ID']
        return self.getAccountPwd()

    def createResource(self, resourcename, accountname, password, ownername, resource_type='Linux', group=''):
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

        params = urllib.urlencode({'INPUT_DATA': unicode(data)})
        
        r = open_url(url, method="POST", headers=headers, data=params, validate_certs=self.validate_certs, use_proxy=self.use_proxy)

        res = json.loads(r.read())['operation']['result']
        status = res['status']
        if status == 'Failed':
            raise RuntimeError(res['message'])
        return status


def get_password(auth_pmp, params):
    pmp = PasswordManagerPro(auth_pmp)
    password = pmp.getPassword(params['resource_name'], params['account_name'])
    return {'status': 'OK', 'password': password}


def create_host(auth_pmp, params):
    pmp = PasswordManagerPro(auth_pmp)
    status = pmp.createResource(params['resource_name'], params['account_name'], params['password'], params['owner'],
                                group=params['group'])
    return {'status': status}


# Some parameters are required depending on the operation:
OP_REQUIRED = dict(create_host=['resource_name', 'account_name', 'password', 'owner'],
                   get_password=['resource_name', 'account_name'],
                   )


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
            use_proxy=dict(default=False),
            validate_certs=dict(default=False),
            timeout=dict(type='float', default=10),
        ),
        supports_check_mode=False
    )

    op = module.params['operation']
    # Check we have the necessary per-operation parameters
    missing = []
    for parm in OP_REQUIRED[op]:
        if not module.params[parm]:
            missing.append(parm)
    if missing:
        module.fail_json(msg="Operation %s require the following missing parameters: %s" % (op, ",".join(missing)))

    # Handle rest of parameters
    pmp_auth = {
        'HOST': module.params['uri'],
        'PORT': module.params['port'],
        'TOKEN': module.params['token'],
    }

    # Dispatch
    try:
        # Lookup the corresponding method for this operation. This is
        # safe as the AnsibleModule should remove any unknown operations.
        thismod = sys.modules[__name__]
        method = getattr(thismod, op)

        ret = method(pmp_auth, module.params)

    except Exception as e:
        return module.fail_json(msg=e.message)

    module.exit_json(changed=True, meta=ret)


if __name__ == '__main__':
    main()
