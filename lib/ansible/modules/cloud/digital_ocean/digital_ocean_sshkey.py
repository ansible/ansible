#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_sshkey
short_description: Manage DigitalOcean SSH keys
description:
     - Create/delete DigitalOcean SSH keys.
version_added: "2.4"
author: "Patrick Marques (@pmarques)"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  fingerprint:
    description:
     - This is a unique identifier for the SSH key used to delete a key
    version_added: 2.4
    aliases: ['id']
  name:
    description:
     - The name for the SSH key
  ssh_pub_key:
    description:
     - The Public SSH key to add.
  oauth_token:
    description:
     - DigitalOcean OAuth token.
    required: true
    version_added: 2.4
notes:
  - Version 2 of DigitalOcean API is used.
requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: "Create ssh key"
  digital_ocean_sshkey:
    oauth_token: "{{ oauth_token }}"
    name: "My SSH Public Key"
    ssh_pub_key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAQQDDHr/jh2Jy4yALcK4JyWbVkPRaWmhck3IgCoeOO3z1e2dBowLh64QAM+Qb72pxekALga2oi4GvT+TlWNhzPH4V example"
    state: present
  register: result

- name: "Delete ssh key"
  digital_ocean_sshkey:
    oauth_token: "{{ oauth_token }}"
    state: "absent"
    fingerprint: "3b:16:bf:e4:8b:00:8b:b8:59:8c:a9:d3:f0:19:45:fa"
'''


RETURN = '''
# Digital Ocean API info https://developers.digitalocean.com/documentation/v2/#list-all-keys
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
        "ssh_key": {
            "id": 512189,
            "fingerprint": "3b:16:bf:e4:8b:00:8b:b8:59:8c:a9:d3:f0:19:45:fa",
            "name": "My SSH Public Key",
            "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAQQDDHr/jh2Jy4yALcK4JyWbVkPRaWmhck3IgCoeOO3z1e2dBowLh64QAM+Qb72pxekALga2oi4GvT+TlWNhzPH4V example"
        }
    }
'''

import json
import hashlib
import base64

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
        timeout = self.module.params['timeout']

        resp, info = fetch_url(self.module, url, data=data, headers=self.headers, method=method, timeout=timeout)

        # Exceptions in fetch_url may result in a status -1, the ensures a
        if info['status'] == -1:
            self.module.fail_json(msg=info['msg'])

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
    state = module.params['state']
    fingerprint = module.params['fingerprint']
    name = module.params['name']
    ssh_pub_key = module.params['ssh_pub_key']

    rest = Rest(module, {'Authorization': 'Bearer {0}'.format(api_token),
                         'Content-type': 'application/json'})

    fingerprint = fingerprint or ssh_key_fingerprint(ssh_pub_key)
    response = rest.get('account/keys/{0}'.format(fingerprint))
    status_code = response.status_code
    json = response.json

    if status_code not in (200, 404):
        module.fail_json(msg='Error getting ssh key [{0}: {1}]'.format(
            status_code, response.json['message']), fingerprint=fingerprint)

    if state in ('present'):
        if status_code == 404:
            # IF key not found create it!

            if module.check_mode:
                module.exit_json(changed=True)

            payload = {
                'name': name,
                'public_key': ssh_pub_key
            }
            response = rest.post('account/keys', data=payload)
            status_code = response.status_code
            json = response.json
            if status_code == 201:
                module.exit_json(changed=True, data=json)

            module.fail_json(msg='Error creating ssh key [{0}: {1}]'.format(
                status_code, response.json['message']))

        elif status_code == 200:
            # If key found was found, check if name needs to be updated
            if name is None or json['ssh_key']['name'] == name:
                module.exit_json(changed=False, data=json)

            if module.check_mode:
                module.exit_json(changed=True)

            payload = {
                'name': name,
            }
            response = rest.put('account/keys/{0}'.format(fingerprint), data=payload)
            status_code = response.status_code
            json = response.json
            if status_code == 200:
                module.exit_json(changed=True, data=json)

            module.fail_json(msg='Error updating ssh key name [{0}: {1}]'.format(
                status_code, response.json['message']), fingerprint=fingerprint)

    elif state in ('absent'):
        if status_code == 404:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        response = rest.delete('account/keys/{0}'.format(fingerprint))
        status_code = response.status_code
        json = response.json
        if status_code == 204:
            module.exit_json(changed=True)

        module.fail_json(msg='Error creating ssh key [{0}: {1}]'.format(
            status_code, response.json['message']))


def ssh_key_fingerprint(ssh_pub_key):
    key = ssh_pub_key.split(None, 2)[1]
    fingerprint = hashlib.md5(base64.b64decode(key)).hexdigest()
    return ':'.join(a + b for a, b in zip(fingerprint[::2], fingerprint[1::2]))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            fingerprint=dict(aliases=['id'], required=False),
            name=dict(required=False),
            ssh_pub_key=dict(required=False),
            oauth_token=dict(
                no_log=True,
                # Support environment variable for DigitalOcean OAuth Token
                fallback=(env_fallback, ['DO_API_TOKEN', 'DO_API_KEY', 'DO_OAUTH_TOKEN']),
                required=True,
            ),
            validate_certs=dict(type='bool', default=True),
            timeout=dict(type='int', default=30),
        ),
        required_one_of=(
            ('fingerprint', 'ssh_pub_key'),
        ),
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
