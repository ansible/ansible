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

def digitalocean_api_call(module, method, url, data=None, retry=0):
    """ Get digitalocean floating ips """

    headers = {
        "Authorization" : "Bearer %s" % (module.params['oauth_token']),
        "Content-Type"  : "application/json"
    }

    if data:
        data = module.jsonify(data)

    response, info = fetch_url(module, url, headers=headers, method=method, data=data)

    if info['status'] == 204:
        # 204 has no content
        response = {}
    elif info['status'] in [404, 422]:
        try:
            # TODO: Return as a message?
            info['body'] = json.loads(info['body'])
            response = {}
        except Exception:
            module.fail_json(changed=False, msg="Error parsing digitalocean response", response=response, info=info)
    else:
        try:
            response = response.read()
            response = json.loads(response)
        except Exception:
            module.fail_json(changed=False, msg="Error parsing digitalocean response", response=response, info=info)

    return info, response

def get_floating_ip_details(module):
    ip = module.params['ip']

    info, response = digitalocean_api_call(module, "GET", "https://api.digitalocean.com/v2/floating_ips/%s" % (ip))

    status_code = info['status']

    if status_code == 404:
        body_id = info['body']['id']
        if body_id == "not_found":
            module.fail_json(changed=False,
                             msg="Floating IP does not exist!",
                             response=response,
                             info=info,
                            )

    if status_code != 200:
        status_code = status_code
        module.fail_json(changed=False, msg="unknow response: HTTP status_code=%s" % (status_code), response=response, info=info)

    return response['floating_ip']

def assign_floating_id_to_droplet(module):
    ip = module.params['ip']

    data = {
        "type": "assign",
        "droplet_id": module.params['droplet_id'],
    }

    # Floating IP is pointing to the wrong Droplet, update it!
    info, response = digitalocean_api_call(module, "POST", "https://api.digitalocean.com/v2/floating_ips/%s/actions" % (ip), data)

    status_code = info['status']

    if status_code == 201:
        changed = True
    elif status_code == 422:
        unprocessable_entity = info['body']['id']
        if unprocessable_entity == "unprocessable_entity":
            message = info['body']['message']
            if message == "Droplet can't be blank":
                module.fail_json(changed=False,
                                 msg="This returned '%s', provided Droplet ID doesn't exists!" % (message),
                                 response=response,
                                 info=info,
                                )
            else:
                module.fail_json(changed=False,
                                 msg="Droplet have already a Floating IP assigned!",
                                 response=response,
                                 info=info,
                                )
        else:
            module.fail_json(changed=False,
                             msg="Unknown id on body response: id=%s" % (unprocessable_entity),
                             response=response,
                             info=info,
                            )
    else:
        module.fail_json(changed=False, msg="Error parsing digitalocean response", response=response, info=info)

    return info, response, changed

def associate_floating_ips(module):
    floating_ip = get_floating_ip_details(module)
    droplet = floating_ip['droplet']

    # If already assigned to a droplet verify if is one of the specified as valid
    if droplet is not None and str(droplet['id']) in [module.params['droplet_id']]:
        changed = False
    else:
        info, response, changed = assign_floating_id_to_droplet(module)

    response = {
        "changed": changed,
        "http_response": response,
    }

    return response

def create_floating_ips(module):
    changed = False
    data = {
    }

    if module.params['region'] is not None:
        data["region"] = module.params['region']
    if module.params['droplet_id'] is not None:
        data["droplet_id"] = module.params['droplet_id']

    # How to detect if "this" Floating IP is already created? tags are only supported for droplets -.-'
    info, response = digitalocean_api_call(module, "POST", "https://api.digitalocean.com/v2/floating_ips", data)

    status_code = info['status']

    if status_code == 202:
        changed = True

    response = {
        "changed": changed,
        "http_response": response,
        "public_ip": response['floating_ip']['ip'],
    }

    return response


def delete_floating_ips(module):
    url = "https://api.digitalocean.com/v2/floating_ips/%s" % (module.params['ip'])
    info, response = digitalocean_api_call(module, "DELETE", url)

    status_code = info['status']
    changed = False

    # sucesseful DELETE will return HTTP 204 status code
    if status_code == 204:
        changed = True
    # Floating IP not found!
    elif status_code == 404:
        # If id is not_found, awesome! if not... dammit!
        body_id = info['body']['id']
        if body_id != "not_found":
            module.fail_json(changed=False,
                             msg="Unknown id on body response: id=%s" % (body_id),
                             response=response,
                             info=info,
                            )
        # Is not present so, is not changed but is as expected!
    else:
        module.fail_json(changed=False, msg="unknow response: HTTP status_code=%s" % (status_code), response=response, info=info)

    return {
        "changed": changed,
        "http_response": response,
    }

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

    if module.params['state'] == 'absent':
        result = delete_floating_ips(module)
    elif module.params['state'] == 'present':
        if module.params['droplet_id'] is not None and module.params['ip'] is not None:
            # Lets try to associate the ip to the specified droplet
            result = associate_floating_ips(module)
        else:
            result = create_floating_ips(module)
    else:
        module.fail_json(changed=False, msg="Unknown action!")

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.urls import *
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
