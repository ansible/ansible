#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Nandor Sivok <nandor@gawker.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: netscaler
version_added: "1.1"
short_description: Manages Citrix NetScaler entities
description:
     - Manages Citrix NetScaler server and service entities.
deprecated:
  removed_in: "2.8"
  why: Replaced with Citrix maintained version.
  alternative: Use M(netscaler_service) and M(netscaler_server) instead.
options:
  nsc_host:
    description:
      - Hostname or ip of your netscaler.
    required: true
  nsc_protocol:
    description:
      - Protocol used to access netscaler.
    default: https
  user:
    description:
      - Username.
    required: true
  password:
    description:
      - Password.
    required: true
  action:
    description:
      - The action you want to perform on the entity.
    choices: [ disable, enable ]
    default: disable
  name:
    description:
      - Name of the entity.
    required: true
    default: hostname
  type:
    description:
      - Type of the entity.
    choices: [ server, service ]
    default: server
  validate_certs:
    description:
      - If C(no), SSL certificates for the target url will not be validated.
      - This should only be used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
author:
- Nandor Sivok (@dominis)
'''

EXAMPLES = '''
- name: Disable the server
  netscaler:
    nsc_host: nsc.example.com
    user: apiuser
    password: apipass

- name: Enable the server
  netscaler:
    nsc_host: nsc.example.com
    user: apiuser
    password: apipass
    action: enable

- name: Disable the service local:8080
  netscaler:
    nsc_host: nsc.example.com
    user: apiuser
    password: apipass
    name: local:8080
    type: service
    action: disable
'''

import json
import socket
import traceback
import base64

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_native, to_bytes
from ansible.module_utils.urls import fetch_url


class netscaler(object):

    _nitro_base_url = '/nitro/v1/'

    def __init__(self, module):
        self.module = module

    def http_request(self, api_endpoint, data_json=None):
        data_josn = {} if data_json is None else data_json

        request_url = self._nsc_protocol + '://' + self._nsc_host + self._nitro_base_url + api_endpoint

        data_json = urlencode(data_json)
        if not len(data_json):
            data_json = None

        auth = base64.b64encode(to_bytes('%s:%s' % (self._nsc_user, self._nsc_pass)).replace('\n', '').strip())
        headers = {
            'Authorization': 'Basic %s' % auth,
            'Content-Type': 'application/x-www-form-urlencoded',
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
        argument_spec=dict(
            nsc_host=dict(type='str', required=True),
            nsc_protocol=dict(type='str', default='https'),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            action=dict(type='str', default='enable', choices=['disable', 'enable']),
            name=dict(type='str', default=socket.gethostname()),
            type=dict(type='str', default='server', choices=['server', 'service']),
            validate_certs=dict(type='bool', default=True),
        ),
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
