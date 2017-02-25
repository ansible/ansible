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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: auth0_user_facts
short_description: Module for gathering facts about auth0 users.
description:
    - Auth0 user gathering facts module. It can search for a given user and
      return it's payload.
version_added: 2.3
options:
  query:
    description:
     - Query used to select wanted user.
    required: true
  auth0_token:
    description:
     - Authentication token used for auth0 communication.
    required: true
    aliases: ['token']
  auth0_domain:
    description:
     - Auth0 domain used for authentication.
    required: true
    aliases: ['domain']
  search_engine:
    description:
      - Select required search engine for user queries.
    default: 'v2'
'''

EXAMPLES = '''
# Fetch facts about auth0 user/users fetched by a given query.
- auth0_user_facts:
    auth0_token: token
    auth0_domain: domain-url
    query: app_metadata.currentTenantId:t2 AND app_metadata.isTechnical:true
    search_engine: v2
  register: auth_user
'''

RETURN = '''
#only defaults
'''

import json
import requests

# import module snippets
from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec=dict(
            auth0_token=dict(required=True, type='str', no_log=True),
            auth0_domain=dict(required=True, type='str'),
            search_engine=dict(required=False, default='v2', type='str'),
            query=dict(required=True, type='str'),
        ),
        supports_check_mode=False
    )

    auth0_domain = module.params['auth0_domain']
    auth0_token = module.params['auth0_token']
    query = module.params['query']
    search_engine = module.params['search_engine']

    http_headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer %s'%(auth0_token)
    }

    url_params = {
        'q': query,
        'search_engine': search_engine
    }

    url = 'https://%s/api/v2/users'%(auth0_domain)

    req = requests.get(url, params=url_params, headers=http_headers)

    if req.status_code != 200:
        module.fail_json(msg='Request to Auth0 failed with return code %s, reason: %s'%
                         (req.status_code, req.reason))

    module.exit_json(results=json.loads(req.text))

if __name__ == '__main__':
    main()

