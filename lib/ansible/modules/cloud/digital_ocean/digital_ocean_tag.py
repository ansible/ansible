#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


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
    - The type of resource to operate on. Currently, only tagging of
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
from ansible.module_utils._text import to_text


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
                return json.loads(to_text(self.info["body"], errors='surrogate_or_strict'))
            return None
        try:
            return json.loads(to_text(self.body, errors='surrogate_or_strict'))
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

    def send(self, method, path, data=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)

        resp, info = fetch_url(self.module, url, data=data, headers=self.headers, method=method)

        return Response(resp, info)

    def get(self, path, data=None):
        return self.send('GET', path, data)

    def put(self, path, data=None):
        return self.send('PUT', path, data)

    def post(self, path, data=None):
        return self.send('POST', path, data)

    def delete(self, path, data=None):
        return self.send('DELETE', path, data)


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

    rest = Rest(module, {'Authorization': 'Bearer {0}'.format(api_token),
                         'Content-type': 'application/json'})

    # Check if api_token is valid or not
    response = rest.get('account')
    if response.status_code == 401:
        module.fail_json(msg='Failed to login using api_token, please verify '
                             'validity of api_token')
    if state == 'present':
        response = rest.get('tags/{0}'.format(name))
        status_code = response.status_code
        resp_json = response.json
        changed = False
        if status_code == 200 and resp_json['tag']['name'] == name:
            changed = False
        else:
            # Ensure Tag exists
            response = rest.post("tags", data={'name': name})
            status_code = response.status_code
            resp_json = response.json
            if status_code == 201:
                changed = True
            elif status_code == 422:
                changed = False
            else:
                module.exit_json(changed=False, data=resp_json)

        if resource_id is None:
            # No resource defined, we're done.
            module.exit_json(changed=changed, data=resp_json)
        else:
            # Check if resource is already tagged or not
            found = False
            url = "{0}?tag_name={1}".format(resource_type, name)
            if resource_type == 'droplet':
                url = "droplets?tag_name={0}".format(name)
            response = rest.get(url)
            status_code = response.status_code
            resp_json = response.json
            if status_code == 200:
                for resource in resp_json['droplets']:
                    if not found and resource['id'] == int(resource_id):
                        found = True
                        break
                if not found:
                    # If resource is not tagged, tag a resource
                    url = "tags/{0}/resources".format(name)
                    payload = {
                        'resources': [{
                            'resource_id': resource_id,
                            'resource_type': resource_type}]}
                    response = rest.post(url, data=payload)
                    if response.status_code == 204:
                        module.exit_json(changed=True)
                    else:
                        module.fail_json(msg="error tagging resource '{0}': {1}".format(resource_id, response.json["message"]))
                else:
                    # Already tagged resource
                    module.exit_json(changed=False)
            else:
                # Unable to find resource specified by user
                module.fail_json(msg=resp_json['message'])

    elif state == 'absent':
        if resource_id:
            url = "tags/{0}/resources".format(name)
            payload = {
                'resources': [{
                    'resource_id': resource_id,
                    'resource_type': resource_type}]}
            response = rest.delete(url, data=payload)
        else:
            url = "tags/{0}".format(name)
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
