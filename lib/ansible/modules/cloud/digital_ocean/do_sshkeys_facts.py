#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Patrick F. Marques <patrickfmarques@gmail.com>
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
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: do_sshkeys_facts
short_description: DigitalOcean SSH keys facts
description:
     - Fetch DigitalOcean SSH keys facts.
version_added: "2.4"
author: "Patrick Marques (@pmarques)"
options:
  oauth_token:
    description:
     - DigitalOcean API token.
    required: true

notes:
  - Version 2 of DigitalOcean API is used.
requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: "List all sshkeys"
  do_sshkeys_facts:
    register: result
'''


RETURN = '''
# Digital Ocean API info https://developers.digitalocean.com/documentation/v2/#list-all-keys
data:
    description: List of SSH keys on DigitalOcean
    returned: success and no resource constraint
    type: dict
    sample: {
      "ssh_keys": [
        {
          "id": 512189,
          "fingerprint": "3b:16:bf:e4:8b:00:8b:b8:59:8c:a9:d3:f0:19:45:fa",
          "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAQQDDHr/jh2Jy4yALcK4JyWbVkPRaWmhck3IgCoeOO3z1e2dBowLh64QAM+Qb72pxekALga2oi4GvT+TlWNhzPH4V example",
          "name": "My SSH Public Key"
        }
      ],
      "links": {
      },
      "meta": {
        "total": 1
      }
    }
'''

import json

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


class Response(object):

    def __init__(self, resp, info):
        self.body = None
        if resp:
            self.body = resp.read()
        self.info = info

    @property
    def json(self):
        if not self.body:
            if "body" in self.info:
                return json.loads(self.info["body"])
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            return None

    @property
    def status_code(self):
        return self.info["status"]


class Rest(object):

    def __init__(self, module, headers):
        self.module = module
        self.headers = headers
        self.baseurl = 'https://api.digitalocean.com/v2'

    def _url_builder(self, path):
        if path[0] == '/':
            path = path[1:]
        return '%s/%s' % (self.baseurl, path)

    def send(self, method, path, data=None, headers=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)

        resp, info = fetch_url(self.module, url, data=data, headers=self.headers, method=method)

        return Response(resp, info)

    def get(self, path, data=None, headers=None):
        return self.send('GET', path, data, headers)

    def put(self, path, data=None, headers=None):
        return self.send('PUT', path, data, headers)

    def post(self, path, data=None, headers=None):
        return self.send('POST', path, data, headers)

    def delete(self, path, data=None, headers=None):
        return self.send('DELETE', path, data, headers)


def core(module):
    api_token = module.params['oauth_token']

    rest = Rest(module, {'Authorization': 'Bearer {}'.format(api_token),
                         'Content-type': 'application/json'})

    response = rest.get("account/keys")
    status_code = response.status_code
    json = response.json
    if status_code == 200:
        module.exit_json(changed=False, ansible_facts=json)
    else:
        module.fail_json(msg='Error fecthing facts [{}: {}]'.format(
            status_code, response.json['message']))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            oauth_token=dict(
                no_log=True,
                # Support environment variable for DigitalOcean OAuth Token
                fallback=(env_fallback, ['DO_API_TOKEN', 'DO_API_KEY']),
                required=True,
            ),
        ),
        supports_check_mode=True,
    )

    core(module)

if __name__ == '__main__':
    main()
