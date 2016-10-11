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
DOCUMENTATION = '''
---
module: do_floating_ip
short_description: Manage DigitalOcean Floating IPs
description:
     - Create/delete/assign a floating IP.
version_added: "2.3"
author: "Patrick Marques (@patrickfmarques)"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  ip:
    description:
     - Public IP address of the Floating IP. Used to remove an IP
    required: false
    default: None
  region:
    description:
     - The region that the Floating IP is reserved to.
    required: false
    default: None
  droplet_id:
    description:
     - The Droplet that the Floating IP has been assigned to.
    required: false
    default: None
  oauth_token:
    description:
     - DigitalOcean OAuth token.
    required: true

notes:
  - Version 2 of DigitalOcean API is used.
requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: "Create a Floating IP in regigin lon1"
  do_floating_ip:
    state: present
    region: lon1

- name: "Create a Floating IP assigned to Droplet ID 123456"
  do_floating_ip:
    state: present
    droplet_id: 123456

- name: "Delete a Floating IP with ip 1.2.3.4"
  do_floating_ip:
    state: present
    ip: "1.2.3.4"

'''


RETURN = '''
data:
    description: a DigitalOcean Floating IP resource
    Digital Ocean API info https://developers.digitalocean.com/documentation/v2/#floating-ips
    returned: success and no resource constraint
    type: dict
    sample: {
      "action": {
        "id": 68212728,
        "status": "in-progress",
        "type": "assign_ip",
        "started_at": "2015-10-15T17:45:44Z",
        "completed_at": null,
        "resource_id": 758603823,
        "resource_type": "floating_ip",
        "region": {
          "name": "New York 3",
          "slug": "nyc3",
          "sizes": [
            "512mb",
            "1gb",
            "2gb",
            "4gb",
            "8gb",
            "16gb",
            "32gb",
            "48gb",
            "64gb"
          ],
          "features": [
            "private_networking",
            "backups",
            "ipv6",
            "metadata"
          ],
          "available": true
        },
        "region_slug": "nyc3"
      }
    }
'''

import json
import os

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
    state = module.params['state']
    ip = module.params['ip']
    droplet_id = module.params['droplet_id']
    region = module.params['region']

    rest = Rest(module, {'Authorization': 'Bearer {}'.format(api_token),
                         'Content-type': 'application/json'})

    if state in ('present'):
        if module.params['droplet_id'] is not None and module.params['ip'] is not None:
            # Lets try to associate the ip to the specified droplet
            result = associate_floating_ips(module, rest)
        else:
            result = create_floating_ips(module, rest)

    elif state in ('absent'):
        response = rest.delete("floating_ips/{}".format(ip))
        status_code = response.status_code
        json = response.json
        if status_code == 204:
            module.exit_json(changed=True)
        elif status_code == 404:
            module.exit_json(changed=False)
        else:
            module.exit_json(changed=False, data=json)


def get_floating_ip_details(module, rest):
    ip = module.params['ip']

    response = rest.get("floating_ips/{}".format(ip))
    status_code = response.status_code
    json = response.json
    if status_code == 200:
        return response.json['floating_ip']
    else:
        module.fail_json(msg="Error assigning floating ip [{}: {}]".format(
            status_code, response.json["message"]), region=module.params['region'])


def assign_floating_id_to_droplet(module, rest):
    ip = module.params['ip']

    payload = {
        "type": "assign",
        "droplet_id": module.params['droplet_id'],
    }

    response = rest.post("floating_ips/{}/actions".format(ip), data=payload)
    status_code = response.status_code
    json = response.json
    if status_code == 201:
        module.exit_json(changed=True, data=response.json)
    else:
        module.fail_json(msg="Error creating floating ip [{}: {}]".format(
            status_code, response.json["message"]), region=module.params['region'])

def associate_floating_ips(module, rest):
    floating_ip = get_floating_ip_details(module, rest)
    droplet = floating_ip['droplet']

    # TODO: If already assigned to a droplet verify if is one of the specified as valid
    if droplet is not None and str(droplet['id']) in [module.params['droplet_id']]:
        module.exit_json(changed=False)
    else:
        assign_floating_id_to_droplet(module, rest)

def create_floating_ips(module, rest):
    payload = {
    }

    if module.params['region'] is not None:
        payload["region"] = module.params['region']
    if module.params['droplet_id'] is not None:
        payload["droplet_id"] = module.params['droplet_id']

    response = rest.post("floating_ips", data=payload)
    status_code = response.status_code
    json = response.json
    if status_code == 202:
        module.exit_json(changed=True, data=response.json)
    else:
        module.fail_json(msg="Error creating floating ip [{}: {}]".format(
            status_code, response.json["message"]), region=module.params['region'])


def main():
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(choices=['present', 'absent'], default='present'),
            ip = dict(aliases=['id'], required=False),
            region = dict(required=False),
            droplet_id = dict(required=False),
            oauth_token = dict(
                no_log=True,
                # Support environment variable for DigitalOcean OAuth Token
                fallback=(env_fallback, ['DO_OAUTH_TOKEN']),
                required=True,
            ),
        ),
        # required_one_of = (
        # ),
        required_if = ([
            ('state','delete',['ip'])
        ]),
        # required_together = (),
        mutually_exclusive = (
            ['region', 'droplet_id']
        ),
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
