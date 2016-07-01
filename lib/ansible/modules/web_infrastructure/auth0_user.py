#!/usr/bin/python
#
# (c) 2015, RSD Services S.A
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
module: auth0_user
short_description: Module for managing auth0 users
description:
    - Auth0 user managing module. It can search for a given user and
      return it's payload, create/delete user and update application
      metadata.
version_added: "2.2"
options:
  state:
    description:
     - the state of the collection. Either present or absent
    default: 'present'
    required: true
    aliases: []
    choices: ['present', 'absent', 'delete_all']
  user_data:
    description:
     - data used to update given user definition
    required: false
    aliases: ['body']
  user_id:
    description:
     - data used to update given user definition
    required: false
  auth_token:
    description:
     - authentication token used for auth0 communication
    default: null
    required: true
    aliases: ['token']
  auth0_domain:
    description:
     - auth0 domain used for authentication
    default: null
    required: true
    aliases: ['domain']
'''

EXAMPLES = '''
# Update some user attributes on auth0
- auth0_user:
    state: present
    auth0_token: token
    auth0_domain: domain
    user_data:
      app_metadata:
        app_specific_key: value
      password: new_password
    user_id: userid

# Create new auth0 user for a given domain
- auth0_user:
    state: present
    auth0_token: token
    auth0_domain: domain
    user_data:
      connection: Username-Password-Authentication
      email: john.doe@domain.com
      password: SecretPassword
      email_verified: true
      app_metadata:

      user_metadata:
        firstName: John,
        language: en,
        lastName: Doe,

# Remove all users from given auth0 domain
- auth0_user:
    state: delete_all
    auth0_token: token
    auth0_domain: domain
'''

RETURN = '''
#only defaults
'''

import sys
import requests

def main():
    module = AnsibleModule(
        argument_spec=dict(
            auth0_token=dict(required=True, type='str', aliases=['token']),
            auth0_domain=dict(required=True, type='str', aliases=['domain']),
            state=dict(choices=['present', 'absent', 'delete_all']),
            user_id=dict(required=False, type='str'),
            user_data=dict(type='dict', required=False, aliases=['body']),

        ),
        supports_check_mode=False
    )

    auth0_domain=module.params['auth0_domain']
    auth0_token=module.params['auth0_token']
    state=module.params['state']
    user_id=module.params['user_id']
    user_data=module.params['user_data']

    if state == 'present' or state == 'absent':
      if not user_data:
        module.fail_json(msg='user_data is required parameter for this state')

    if state == 'absent':
      if not user_id:
        module.fail_json(msg='user_id is required parameter for this state')

    http_headers = {
              'content-type': 'application/json',
              'Authorization': 'Bearer {token}'.format(token=auth0_token)
    }

    url_params = user_data

    if state == 'present':
      if user_id:
        url = 'https://{domain}/api/v2/users/{userid}'.format(domain=auth0_domain, userid=user_id)
        r = requests.patch(url, json=user_data, headers=http_headers)
      else:
        url = 'https://{domain}/api/v2/users'.format(domain=auth0_domain)
        r = requests.post(url, json=user_data, headers=http_headers)
    elif state == 'absent':
      url = 'https://{domain}/api/v2/users/{userid}'.format(domain=auth0_domain, userid=user_id)
      r = requests.delete(url, headers=http_headers)
    elif state == 'delete_all':
      url = 'https://{domain}/api/v2/users'.format(domain=auth0_domain)
      r = requests.delete(url, headers=http_headers)

    if r.status_code not in [ 200, 201, 202, 203, 204 ]:
      module.fail_json(msg='Request to Auth0 failed with return code %s, reason: %s'%(r.status_code, r.reason))

    if r.text:
      result = json.loads(r.text)
    else:
      result = "Rest call has not returned any data."

    module.exit_json(results=result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()

