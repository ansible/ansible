#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Nandor Sivok <nandor@gawker.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: netscaler
version_added: "1.1"
short_description: Manages Citrix NetScaler entities
description:
     - Manages Citrix NetScaler server and service entities.
options:
  nsc_host:
    description:
      - hostname or ip of your netscaler
    required: true
    default: null
    aliases: []
  nsc_protocol:
    description:
      - protocol used to access netscaler
    required: false
    default: https
    aliases: []
  user:
    description:
      - username
    required: true
    default: null
    aliases: []
  password:
    description:
      - password
    required: true
    default: null
    aliases: []
  action:
    description:
      - the action you want to perform on the entity
    required: false
    default: disable
    choices: ["enable", "disable"]
    aliases: []
  name:
    description:
      - name of the entity
    required: true
    default: hostname
    aliases: []
  type:
    description:
      - type of the entity
    required: false
    default: server
    choices: ["server", "service"]
    aliases: []
  validate_certs:
    description:
      - If C(no), SSL certificates for the target url will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']

requirements: []
author: "Nandor Sivok (@dominis)"
'''

EXAMPLES = '''
# Disable the server
- netscaler:
    nsc_host: nsc.example.com
    user: apiuser
    password: apipass

# Enable the server
- netscaler:
    nsc_host: nsc.example.com
    user: apiuser
    password: apipass
    action: enable

# Disable the service local:8080
- netscaler:
    nsc_host: nsc.example.com
    user: apiuser
    password: apipass
    name: 'local:8080'
    type: service
    action: disable
'''


import base64
import json
import socket
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


class netscaler(object):

    _nitro_base_url = '/nitro/v1/'

    def __init__(self, module):
        self.module = module

    def http_request(self, api_endpoint, data_json={}):
        request_url = self._nsc_protocol + '://' + self._nsc_host + self._nitro_base_url + api_endpoint

        data_json = urlencode(data_json)
        if not len(data_json):
            data_json = None

        auth = base64.encodestring('%s:%s' % (self._nsc_user, self._nsc_pass)).replace('\n', '').strip()
        headers = {
            'Authorization': 'Basic %s' % auth,
            'Content-Type' : 'application/x-www-form-urlencoded',
        }

        response, info = fetch_url(self.module, request_url, data=data_json, headers=headers)

        return json.load(response)

    def prepare_request(self, action):
        resp = self.http_request(
            'config',
            {
                "object":
                {
                    "params": {"action": action},
                    self._type: {"name": self._name}
                }
            }
        )

        return resp


def core(module):
    n = netscaler(module)
    n._nsc_host = module.params.get('nsc_host')
    n._nsc_user = module.params.get('user')
    n._nsc_pass = module.params.get('password')
    n._nsc_protocol = module.params.get('nsc_protocol')
    n._name = module.params.get('name')
    n._type = module.params.get('type')
    action = module.params.get('action')

    r = n.prepare_request(action)

    return r['errorcode'], r


def main():

    module = AnsibleModule(
        argument_spec = dict(
            nsc_host = dict(required=True),
            nsc_protocol = dict(default='https'),
            user = dict(required=True),
            password = dict(required=True, no_log=True),
            action = dict(default='enable', choices=['enable','disable']),
            name = dict(default=socket.gethostname()),
            type = dict(default='server', choices=['service', 'server']),
            validate_certs=dict(default='yes', type='bool'),
        )
    )

    rc = 0
    try:
        rc, result = core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    if rc != 0:
        module.fail_json(rc=rc, msg=result)
    else:
        result['changed'] = True
        module.exit_json(**result)


if __name__ == '__main__':
    main()
