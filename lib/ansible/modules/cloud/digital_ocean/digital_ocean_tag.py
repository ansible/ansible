#!/usr/bin/python
# -*- coding: utf-8 -*-

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
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_tag
short_description: Create and remove tag(s) to DigitalOcean resource.
description:
    - Create and remove tag(s) to DigitalOcean resource.
author: "Victor Volle (@kontrafiktion)"
version_added: "2.2"
options:
  name:
    description:
     - The name of the tag. The supported characters for names include
       alphanumeric characters, dashes, and underscores.
    required: true
  resource_id:
    description:
    - The ID of the resource to operate on.
  resource_type:
    description:
    - The type of resource to operate on. Currently only tagging of
      droplets is supported.
    default: droplet
    choices: ['droplet']
  state:
    description:
     - Whether the tag should be present or absent on the resource.
    default: present
    choices: ['present', 'absent']
  api_token:
    description:
     - DigitalOcean api token.

notes:
  - Two environment variables can be used, DO_API_KEY and DO_API_TOKEN.
    They both refer to the v2 token.
  - As of Ansible 2.0, Version 2 of the DigitalOcean API is used.

requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: create a tag
  digital_ocean_tag:
    name: production
    state: present

- name: tag a resource; creating the tag if it does not exists
  digital_ocean_tag:
    name: "{{ item }}"
    resource_id: YYY
    state: present
  with_items:
    - staging
    - dbserver

- name: untag a resource
  digital_ocean_tag:
    name: staging
    resource_id: YYY
    state: absent

# Deleting a tag also untags all the resources that have previously been
# tagged with it
- name: remove a tag
  digital_ocean_tag:
    name: dbserver
    state: absent
'''


RETURN = '''
data:
    description: a DigitalOcean Tag resource
    returned: success and no resource constraint
    type: dict
    sample: {
        "tag": {
        "name": "awesome",
        "resources": {
          "droplets": {
            "count": 0,
            "last_tagged": null
          }
        }
      }
    }
'''

import json
import os

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
    try:
        api_token = module.params['api_token'] or \
            os.environ['DO_API_TOKEN'] or os.environ['DO_API_KEY']
    except KeyError as e:
        module.fail_json(msg='Unable to load %s' % e.message)

    state = module.params['state']
    name = module.params['name']
    resource_id = module.params['resource_id']
    resource_type = module.params['resource_type']

    rest = Rest(module, {'Authorization': 'Bearer {}'.format(api_token),
                         'Content-type': 'application/json'})

    if state in ('present'):
        if name is None:
            module.fail_json(msg='parameter `name` is missing')

        # Ensure Tag exists
        response = rest.post("tags", data={'name': name})
        status_code = response.status_code
        json = response.json
        if status_code == 201:
            changed = True
        elif status_code == 422:
            changed = False
        else:
            module.exit_json(changed=False, data=json)

        if resource_id is None:
            # No resource defined, we're done.
            if json is None:
                module.exit_json(changed=changed, data=json)
            else:
                module.exit_json(changed=changed, data=json)
        else:
            # Tag a resource
            url = "tags/{}/resources".format(name)
            payload = {
                'resources': [{
                    'resource_id': resource_id,
                    'resource_type': resource_type}]}
            response = rest.post(url, data=payload)
            if response.status_code == 204:
                module.exit_json(changed=True)
            else:
                module.fail_json(msg="error tagging resource '{}': {}".format(
                    resource_id, response.json["message"]))

    elif state in ('absent'):
        if name is None:
            module.fail_json(msg='parameter `name` is missing')

        if resource_id:
            url = "tags/{}/resources".format(name)
            payload = {
                'resources': [{
                    'resource_id': resource_id,
                    'resource_type': resource_type}]}
            response = rest.delete(url, data=payload)
        else:
            url = "tags/{}".format(name)
            response = rest.delete(url)
        if response.status_code == 204:
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=False, data=response.json)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            resource_id=dict(aliases=['droplet_id'], type='int'),
            resource_type=dict(choices=['droplet'], default='droplet'),
            state=dict(choices=['present', 'absent'], default='present'),
            api_token=dict(aliases=['API_TOKEN'], no_log=True),
        )
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
