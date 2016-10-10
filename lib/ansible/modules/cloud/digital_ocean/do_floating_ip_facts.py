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
module: do_floating_ip_facts
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
  do_floating_ip_facts:
    state: present
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

def list_floating_ips(module):
    info, response = digitalocean_api_call(module, "GET", "https://api.digitalocean.com/v2/floating_ips?page=1&per_page=20")

    # TODO: recursive fetch!
    floating_ips = response['floating_ips']

    return {
        "changed": False,
        "http_response": response,
        "floating_ips": floating_ips,
    }

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(choices=['present'], default='present'),
            oauth_token = dict(
                no_log=True,
                # Support environment variable for DigitalOcean OAuth Token
                fallback=(env_fallback, ['DO_OAUTH_TOKEN']),
                required=True,
            ),
        ),
    )

    result = list_floating_ips(module)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.urls import *
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
