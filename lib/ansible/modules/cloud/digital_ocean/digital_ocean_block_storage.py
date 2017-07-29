#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_block_storage
short_description: Create/destroy or attach/detach Block Storage volumes in DigitalOcean
description:
     - Create/destroy Block Storage volume in DigitalOcean, or attach/detach Block Storage volume to a droplet.
version_added: "2.2"
options:
  command:
    description:
     - Which operation do you want to perform.
    choices: ['create', 'attach']
    required: true
  state:
    description:
     - Indicate desired state of the target.
    choices: ['present', 'absent']
    required: true
  api_token:
    description:
     - DigitalOcean api token.
    required: true
  block_size:
    description:
    - The size of the Block Storage volume in gigabytes. Required when command=create and state=present.
  volume_name:
    description:
    - The name of the Block Storage volume.
    required: true
  description:
    description:
    - Description of the Block Storage volume.
  region:
    description:
    - The slug of the region where your Block Storage volume should be located in.
    required: true
  droplet_id:
    description:
    - The droplet id you want to operate on. Required when command=attach.
  timeout:
    description:
    - The timeout in seconds used for polling DigitalOcean's API.
    default: 10

notes:
  - Two environment variables can be used, DO_API_KEY and DO_API_TOKEN.
    They both refer to the v2 token.

author:
    - "Harnek Sidhu (github: @harneksidhu)"
'''

EXAMPLES = '''
# Create new Block Storage
- digital_ocean_block_storage:
    state: present
    command: create
    api_token: <TOKEN>
    region: nyc1
    block_size: 10
    volume_name: nyc1-block-storage
# Delete Block Storage
- digital_ocean_block_storage:
    state: absent
    command: create
    api_token: <TOKEN>
    region: nyc1
    volume_name: nyc1-block-storage
# Attach Block Storage to a Droplet
- digital_ocean_block_storage:
    state: present
    command: attach
    api_token: <TOKEN>
    volume_name: nyc1-block-storage
    region: nyc1
    droplet_id: <ID>
# Detach Block Storage from a Droplet
- digital_ocean_block_storage:
    state: absent
    command: attach
    api_token: <TOKEN>
    volume_name: nyc1-block-storage
    region: nyc1
    droplet_id: <ID>
'''

RETURN = '''
id:
    description: Unique identifier of a Block Storage volume returned during creation.
    returned: changed
    type: string
    sample: "69b25d9a-494c-12e6-a5af-001f53126b44"
'''

import json
import os
import time
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


class DOBlockStorageException(Exception):
    pass


class Response(object):

    def __init__(self, resp, info):
        self.body = None
        if resp:
            self.body = resp.read()
        self.info = info

    @property
    def json(self):
        if self.body:
            return json.loads(self.body)
        elif "body" in self.info:
            return json.loads(self.info["body"])
        else:
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


class DOBlockStorage(object):

    def __init__(self, module):
        api_token = module.params['api_token'] or \
            os.environ['DO_API_TOKEN'] or os.environ['DO_API_KEY']
        self.module = module
        self.rest = Rest(module, {'Authorization': 'Bearer {}'.format(api_token),
                                  'Content-type': 'application/json'})

    def get_key_or_fail(self, k):
        v = self.module.params[k]
        if v is None:
            self.module.fail_json(msg='Unable to load %s' % k)
        return v

    def poll_action_for_complete_status(self, action_id):
        url = 'actions/{}'.format(action_id)
        end_time = time.time() + self.module.params['timeout']
        while time.time() < end_time:
            time.sleep(2)
            response = self.rest.get(url)
            status = response.status_code
            json = response.json
            if status == 200:
                if json['action']['status'] == 'completed':
                    return True
                elif json['action']['status'] == 'errored':
                    raise DOBlockStorageException(json['message'])
        raise DOBlockStorageException('Unable to reach api.digitalocean.com')

    def get_attached_droplet_ID(self, volume_name, region):
        url = 'volumes?name={}&region={}'.format(volume_name, region)
        response = self.rest.get(url)
        status = response.status_code
        json = response.json
        if status == 200:
            volumes = json['volumes']
            if len(volumes) > 0:
                droplet_ids = volumes[0]['droplet_ids']
                if len(droplet_ids) > 0:
                    return droplet_ids[0]
            return None
        else:
            raise DOBlockStorageException(json['message'])

    def attach_detach_block_storage(self, method, volume_name, region, droplet_id):
        data = {
            'type': method,
            'volume_name': volume_name,
            'region': region,
            'droplet_id': droplet_id
        }
        response = self.rest.post('volumes/actions', data=data)
        status = response.status_code
        json = response.json
        if status == 202:
            return self.poll_action_for_complete_status(json['action']['id'])
        elif status == 200:
            return True
        elif status == 422:
            return False
        else:
            raise DOBlockStorageException(json['message'])

    def create_block_storage(self):
        block_size = self.get_key_or_fail('block_size')
        volume_name = self.get_key_or_fail('volume_name')
        region = self.get_key_or_fail('region')
        description = self.module.params['description']
        data = {
            'size_gigabytes': block_size,
            'name': volume_name,
            'description': description,
            'region': region
        }
        response = self.rest.post("volumes", data=data)
        status = response.status_code
        json = response.json
        if status == 201:
            self.module.exit_json(changed=True, id=json['volume']['id'])
        elif status == 409 and json['id'] == 'already_exists':
            self.module.exit_json(changed=False)
        else:
            raise DOBlockStorageException(json['message'])

    def delete_block_storage(self):
        volume_name = self.get_key_or_fail('volume_name')
        region = self.get_key_or_fail('region')
        url = 'volumes?name={}&region={}'.format(volume_name, region)
        attached_droplet_id = self.get_attached_droplet_ID(volume_name, region)
        if attached_droplet_id is not None:
            self.attach_detach_block_storage('detach', volume_name, region, attached_droplet_id)
        response = self.rest.delete(url)
        status = response.status_code
        json = response.json
        if status == 204:
            self.module.exit_json(changed=True)
        elif status == 404:
            self.module.exit_json(changed=False)
        else:
            raise DOBlockStorageException(json['message'])

    def attach_block_storage(self):
        volume_name = self.get_key_or_fail('volume_name')
        region = self.get_key_or_fail('region')
        droplet_id = self.get_key_or_fail('droplet_id')
        attached_droplet_id = self.get_attached_droplet_ID(volume_name, region)
        if attached_droplet_id is not None:
            if attached_droplet_id == droplet_id:
                self.module.exit_json(changed=False)
            else:
                self.attach_detach_block_storage('detach', volume_name, region, attached_droplet_id)
        changed_status = self.attach_detach_block_storage('attach', volume_name, region, droplet_id)
        self.module.exit_json(changed=changed_status)

    def detach_block_storage(self):
        volume_name = self.get_key_or_fail('volume_name')
        region = self.get_key_or_fail('region')
        droplet_id = self.get_key_or_fail('droplet_id')
        changed_status = self.attach_detach_block_storage('detach', volume_name, region, droplet_id)
        self.module.exit_json(changed=changed_status)


def handle_request(module):
    block_storage = DOBlockStorage(module)
    command = module.params['command']
    state = module.params['state']
    if command == 'create':
        if state == 'present':
            block_storage.create_block_storage()
        elif state == 'absent':
            block_storage.delete_block_storage()
    elif command == 'attach':
        if state == 'present':
            block_storage.attach_block_storage()
        elif state == 'absent':
            block_storage.detach_block_storage()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], required=True),
            command=dict(choices=['create', 'attach'], required=True),
            api_token=dict(aliases=['API_TOKEN'], no_log=True),
            block_size=dict(type='int'),
            volume_name=dict(type='str', required=True),
            description=dict(type='str'),
            region=dict(type='str', required=True),
            droplet_id=dict(type='int'),
            timeout=dict(type='int', default=10),
        ),
    )
    try:
        handle_request(module)
    except DOBlockStorageException as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc())
    except KeyError as e:
        module.fail_json(msg='Unable to load %s' % e.message, exception=traceback.format_exc())


if __name__ == '__main__':
    main()
