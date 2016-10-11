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

DOCUMENTATION = '''
---
module: do_droplet
short_description: Create/delete a droplet in DigitalOcean
description:
     - Create/delete a droplet in DigitalOcean.
version_added: "2.3"
options:
  state:
    description:
     - Indicate desired state of the target.
    required: true
    choices: ['present', 'absent']
  api_token:
    description:
     - DigitalOcean api token.
  api_baseurl:
    description:
     - DigitalOcean api baseurl.
    default: "https://api.digitalocean.com/v2"
  id:
    description:
     - Numeric, the droplet id you want to operate on.
  name:
    description:
     - String, this is the name of the droplet - must be formatted by hostname rules. Required when unique_name=yes.
  unique_name:
    description:
     - Bool, require unique hostnames.  By default, DigitalOcean allows multiple hosts with the same
       name. Setting this to "yes" allows only one host per name. If this option is set to "yes", then 
       the name of the droplet must be provided for both droplet creation and deletion operations.
    default: "no"
    choices: [ "yes", "no" ]
  size:
    description:
     - String, this is the size you would like the droplet to be created with (e.g. "2gb"). Required when state=present.
  image:
    description:
     - This is the image you would like the droplet to be created with (e.g. "ubuntu-14-04-x64"). Required when state=present.
  region:
    description:
     - This is the region you would like your droplet to be created in (e.g. "ams2"). Required when region=present.
  ssh_key_ids:
    description:
     - Optional, array of of SSH key (numeric) ID that you would like to be added to the server.
  private_networking:
    description:
     - Boolean, add an additional private network interface to the droplet for inter-droplet communication."
    default: "no"
    choices: [ "yes", "no" ]
  backups_enabled:
    description:
     - Boolean, enables backups for your droplet.
    default: "no"
    choices: [ "yes", "no" ]
  ipv6:
    description:
     - Boolean, enables ipv6 for your droplet.
    default: "no"
    choices: [ "yes", "no" ]
  user_data:
    description:
      - opaque blob of data which is made available to the droplet
    default: None
  wait:
    description:
     - Boolean, wait for the droplet to be in state 'running' before returning.
    default: "yes"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
     - Numeric, how long before wait gives up in seconds.
    default: 60

notes:
  - Two environment variables can be used, DO_API_KEY and DO_API_TOKEN. They both refer to the v2 token.
author:
    - "Harnek Sidhu (github: @harneksidhu), Vincent Viallet (@zbal), Victor Volle (@kontrafiktion)"
'''


EXAMPLES = '''

# Create a new Droplet
# Will return the droplet details including the droplet id (used for idempotence)

- do_droplet:
    state: present
    name: mydroplet
    api_token: <TOKEN>
    size: 2gb
    region: tor1
    image: ubuntu-16-04-x64
  register: my_droplet

- debug: msg="ID is {{ my_droplet.droplet.id }}"
- debug: msg="IP is {{ my_droplet.droplet.networks.v4[0].ip_address }}"

# Delete droplet using unique_name
# unique_name needs to be set to yes to delete a droplet by hostname

- do_droplet:
  state: absent
  name: mydroplet
  api_token: <TOKEN>
  unique_name: yes

# Delete droplet using id

- do_droplet:
  state: absent
  id: 29325249
  api_token: <TOKEN>


# Ensure a droplet is present using id
# If droplet id already exist, will return the droplet details and changed = False
# If no droplet matches the id, a new droplet will be created and the droplet details (including the new id) are
# returned, changed = True

- do_droplet:
    state: present
    id: 123
    name: mydroplet
    api_token: <TOKEN>
    size: 2gb
    region: ams2
    image: ubuntu-16-04-x64

# Ensure a droplet is present using unique_name
# If droplet hostname already exists, will return the droplet details and changed = False
# If no droplet matches the hostname, a new droplet will be created and the droplet details (including the new id) are
# returned, changed = True

- do_droplet:
  state: present
  name: mydroplet
  unique_name: yes
  api_token: <TOKEN>
  size: 2gb
  region: ams2
  image: ubuntu-16-04-x64

# Create a droplet with ssh key
# The ssh key id can be passed as argument at the creation of a droplet (see ssh_key_ids).
# Several keys can be added to ssh_key_ids
# The keys are used to connect as root to the droplet

- do_sshkeys:
    state: present
    name: key1
    ssh_pub_key: <PUBLIC_KEY>
    api_token: <TOKEN>
  register: key1

- do_droplet:
    state: present
    name: mydroplet
    api_token: <TOKEN>
    size: 2gb
    region: tor1
    image: ubuntu-16-04-x64
    ssh_key_ids: 
      - "{{ key1.data.ssh_key.id }}"
   
'''

RETURN = '''
droplet:
    description: Standard attributes of the droplet
    returned: When state=present 
    type: dict
    sample: {
        "droplet": {
            "backup_ids": [],
            "created_at": "2016-10-15T17:06:40Z",
            "disk": 20,
            "features": [
                "virtio"
            ],
            "id": 29219587,
            "image": {
                "created_at": "2016-10-13T13:42:47Z",
                "distribution": "Ubuntu",
                "id": 20259670,
                "min_disk_size": 20,
                "name": "14.04.5 x64",
                "public": true,
                "regions": [
                    "nyc1",
                    "sfo1",
                    "nyc2",
                    "ams2",
                    "sgp1",
                    "lon1",
                    "nyc3",
                    "ams3",
                    "fra1",
                    "tor1",
                    "sfo2",
                    "blr1"
                ],
                "size_gigabytes": 0.45,
                "slug": "ubuntu-14-04-x64",
                "type": "snapshot"
            },
            "kernel": null,
            "locked": false,
            "memory": 512,
            "name": "1",
            "networks": {
                "v4": [
                    {
                        "gateway": "67.205.144.1",
                        "ip_address": "67.205.150.34",
                        "netmask": "255.255.240.0",
                        "type": "public"
                    }
                ],
                "v6": []
            },
            "next_backup_window": null,
            "region": {
                "available": true,
                "features": [
                    "private_networking",
                    "backups",
                    "ipv6",
                    "metadata",
                    "storage"
                ],
                "name": "New York 1",
                "sizes": [
                    "512mb",
                    "1gb",
                    "2gb",
                    "4gb",
                    "8gb",
                    "16gb"
                ],
                "slug": "nyc1"
            },
            "size": {
                "available": true,
                "disk": 20,
                "memory": 512,
                "price_hourly": 0.00744,
                "price_monthly": 5.0,
                "regions": [
                    "ams1",
                    "ams2",
                    "ams3",
                    "blr1",
                    "fra1",
                    "lon1",
                    "nyc1",
                    "nyc2",
                    "nyc3",
                    "sfo1",
                    "sfo2",
                    "sgp1",
                    "tor1"
                ],
                "slug": "512mb",
                "transfer": 1.0,
                "vcpus": 1
            },
            "size_slug": "512mb",
            "snapshot_ids": [],
            "status": "active",
            "tags": [],
            "vcpus": 1,
            "volume_ids": []
        }
    }
'''

import time
import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.basic import env_fallback
from ansible.module_utils import six

class DropletException(Exception):
    pass

class RestException(Exception):
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

    def __init__(self, module, headers, baseurl):
        self.module = module
        self.headers = headers
        self.baseurl = baseurl

    def _url_builder(self, path):
        if path[0] == '/':
            path = path[1:]
        return '%s/%s' % (self.baseurl, path)

    def send(self, method, path, data=None, headers=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)

        resp, info = fetch_url(self.module, url, data=data, headers=self.headers, method=method)

        response = Response(resp, info)

        if response.status_code >= 500:
            raise RestException('500: Internal server error')
        else:
            return response

    def get(self, path, data=None, headers=None):
        return self.send('GET', path, data, headers)

    def put(self, path, data=None, headers=None):
        return self.send('PUT', path, data, headers)

    def post(self, path, data=None, headers=None):
        return self.send('POST', path, data, headers)

    def delete(self, path, data=None, headers=None):
        return self.send('DELETE', path, data, headers)

class DODroplet(object):

    def __init__(self, module):
        api_token = module.params['api_token']
        api_baseurl = module.params['api_baseurl']
        self.module = module
        self.rest = Rest(module, {'Authorization': 'Bearer {}'.format(api_token),
                         'Content-type': 'application/json'},
                         api_baseurl)

    def get_key_or_fail(self, k):
        v = self.module.params[k]
        if v is None:
            self.module.fail_json(msg='Unable to load %s' % k)
        return v

    def poll_action_for_complete_status(self, action_id):
        url = 'actions/{}'.format(action_id)
        end_time = time.time() + self.module.params['wait_timeout']
        while time.time() < end_time:
            time.sleep(2)
            response = self.rest.get(url)
            status = response.status_code
            json = response.json
            if status == 200:
                if json['action']['status'] == 'completed':
                    return True
                elif json['action']['status'] == 'errored':
                    raise DropletException('Request to api.digitalocean.com has failed')
            elif status >= 400:
                raise DropletException(json['message'])
        raise DropletException('Unknown error occured')

    def power_on_droplet_request(self, droplet_id):
        url = 'droplets/%s/actions' % droplet_id
        data = {'type':'power_on'}
        response = self.rest.post(url, data=data)
        status = response.status_code
        json = response.json
        if status == 201:
            if self.module.params['wait'] == True:
                return self.poll_action_for_complete_status(json['action']['id'])
            else:
                return True
        elif status >= 400:
            raise DropletException(json['message'])
        else:
            raise DropletException('Unknown error occured')

    def create_droplet_request(self, name, size, image, region, ssh_key_ids=None, private_networking=False,
            backups_enabled=False, ipv6=False, user_data=None):
        data = {"name": name, "size": size, "image": image, "region": region,
                "ssh_keys": ssh_key_ids,
                "private_networking": str(private_networking).lower(),
                "backups": str(backups_enabled).lower(), 
                "ipv6": str(ipv6).lower(),
                "user_data": user_data}
        response = self.rest.post('/droplets', data=data)
        status = response.status_code
        json = response.json
        if status == 202:
            if self.module.params['wait'] == True:
                for action in json['links']['actions']:
                    if action['rel'] == 'create':
                        self.poll_action_for_complete_status(action['id'])
                droplet = self.find_droplet_request(id=json['droplet']['id'])
                if droplet is not None:
                    return droplet
                else:
                    raise DropletException('Unable to create droplet')
            else:
                return json['droplet']
        elif status >= 400:
            raise DropletException(json['message'])
        else:
            raise DropletException('Unknown error occured')

    def delete_droplet_request(self, droplet_id):
        url = 'droplets/%s' % droplet_id
        response = self.rest.delete(url)
        status = response.status_code
        json = response.json
        if status == 204:
            return True
        elif status == 404:
            return False
        elif status >=400:
            raise DropletException(json['message'])
        else:
            raise DropletException('Unknown error occured')

    def find_droplet_request(self, id=None, name=None):
        if id is not None:
            url = 'droplets/%s' % id
            response = self.rest.get(url)
            status = response.status_code
            json = response.json
            if status == 200:
                return json['droplet']
            elif status == 404:
                return None
            elif status >= 400:
                raise DropletException(json['message'])
            else:
                raise DropletException('Unknown error occured')
        elif name is not None:
            url = 'droplets?page=1';
            while (url!=None):
                response = self.rest.get(url)
                status = response.status_code
                json = response.json
                if status == 200:
                    for droplet in json['droplets']:
                        if droplet['name']==name:
                            return droplet
                    if json['links'].has_key('pages') and json['links']['pages'].has_key('next'):
                        next_link = json['links']['pages']['next']
                        link_index = next_link.find('v2/') + 3
                        url = next_link[link_index:]
                    else:
                        return None
                elif status >= 400:
                    raise DropletException(json['message'])
                else:
                    raise DropletException('Unknown error occured')
        else:
            return None

    def create_droplet(self):
        droplet = None
        changed = False
        if self.module.params['unique_name']:
            droplet = self.find_droplet_request(name=self.get_key_or_fail('name'))
        else:
            droplet = self.find_droplet_request(id=self.module.params['id'])
        if droplet is None:
            droplet = self.create_droplet_request(
                name=self.get_key_or_fail('name'),
                size=self.get_key_or_fail('size'),
                image=self.get_key_or_fail('image'),
                region=self.get_key_or_fail('region'),
                ssh_key_ids=self.module.params['ssh_key_ids'],
                private_networking=self.module.params['private_networking'],
                backups_enabled=self.module.params['backups_enabled'],
                ipv6=self.module.params['ipv6'],
                user_data=self.module.params.get('user_data'),
            )
            changed = True
        else:
            if droplet['status'] == 'off':
                changed = self.power_on_droplet_request(droplet['id'])
                droplet = self.find_droplet_request(id=droplet['id'])
            elif droplet['status'] == 'archive':
                raise DropletException('Droplet is in archive state')
        self.module.exit_json(changed=changed, droplet=droplet)

    def delete_droplet(self):
        droplet_id = None
        changed = False
        if self.module.params['unique_name']:
            droplet = self.find_droplet_request(name=self.get_key_or_fail('name'))
            if droplet is not None:
                droplet_id = droplet['id']
        else:
            droplet_id = self.get_key_or_fail('id')

        if droplet_id is not None:
            changed = self.delete_droplet_request(droplet_id)

        self.module.exit_json(changed=changed)

def core(module):
    state = module.params['state']
    droplet = DODroplet(module)
    if state == 'present':
        droplet.create_droplet()
    elif state == 'absent':
        droplet.delete_droplet()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], required=True),
            api_token = dict(
                aliases=['API_TOKEN'], 
                no_log=True,
                fallback=(env_fallback, ['DO_API_TOKEN', 'DO_API_KEY']),
                required=True
            ),
            api_baseurl=dict(type='str', default="https://api.digitalocean.com/v2"),
            name=dict(type='str'),
            size=dict(aliases=['size_id']),
            image=dict(aliases=['image_id']),
            region=dict(aliases=['region_id']),
            ssh_key_ids=dict(type='list'),
            private_networking=dict(type='bool', default='no'),
            backups_enabled=dict(type='bool', default='no'),
            ipv6=dict(type='bool', default='no'),
            id=dict(aliases=['droplet_id'], type='int'),
            unique_name=dict(type='bool', default='no'),
            user_data=dict(default=None),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(default=60, type='int'),
        ),
        required_together=(
            ['size', 'image', 'region'],
        ),
        required_one_of=(
            ['id', 'name'],
        ),
    )

    try:
        core(module)
    except DropletException:
        e = get_exception()
        module.fail_json(msg=e.message)
    except RestException:
        e = get_exception()
        module.fail_json(msg=e.message)
    except KeyError:
        e = get_exception()
        module.fail_json(msg='Unable to load %s' % e.message)
    except Exception:
        e = get_exception()
        module.fail_json(msg=e.message)

if __name__ == '__main__':
    main()