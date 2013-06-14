#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to manage Citrix NetScaler entities
(c) 2013, Nandor Sivok <nandor@gawker.com>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

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
requirements: [ "urllib", "urllib2" ]
author: Nandor Sivok
'''

EXAMPLES = '''
# Disable the server
ansible host -m netscaler -a "nsc_host=nsc.example.com user=apiuser password=apipass"

# Enable the server
ansible host -m netscaler -a "nsc_host=nsc.example.com user=apiuser password=apipass action=enable"

# Disable the service local:8080
ansible host -m netscaler -a "nsc_host=nsc.example.com user=apiuser password=apipass name=local:8080 type=service action=disable"
'''


import json
import urllib
import urllib2
import base64
import socket


class netscaler(object):

    _nitro_base_url = '/nitro/v1/'

    def http_request(self, api_endpoint, data_json={}):
        request_url = self._nsc_protocol + '://' + self._nsc_host + self._nitro_base_url + api_endpoint
        data_json = urllib.urlencode(data_json)

        if len(data_json):
            req = urllib2.Request(request_url, data_json)
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        else:
            req = urllib2.Request(request_url)

        base64string = base64.encodestring('%s:%s' % (self._nsc_user, self._nsc_pass)).replace('\n', '').strip()
        req.add_header('Authorization', "Basic %s" % base64string)

        resp = urllib2.urlopen(req)
        resp = json.load(resp)

        return resp

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
    n = netscaler()
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
            password = dict(required=True),
            action = dict(default='enable', choices=['enable','disable']),
            name = dict(default=socket.gethostname()),
            type = dict(default='server', choices=['service', 'server'])
        )
    )

    rc = 0
    try:
        rc, result = core(module)
    except Exception, e:
        module.fail_json(msg=str(e))

    if rc != 0:
        module.fail_json(rc=rc, msg=result)
    else:
        result['changed'] = True
        module.exit_json(**result)


# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()
