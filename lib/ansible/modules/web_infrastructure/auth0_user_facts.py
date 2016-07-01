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
module: auth0_user_facts
short_description: Module for managing auth0 users
description:
    - Auth0 user managing module. It can search for a given user and
      return it's payload, create/delete user and update application
      metadata.
version_added: "2.2"
options:
  query:
    description:
     - query to select given user
    required: false
  auth0_token:
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
  search_engine:
    description:
      - Select required search engine for user queries
    default: 'v2'
    required: false
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

import sys
import requests

def main():
    module = AnsibleModule(
        argument_spec=dict(
            auth0_token=dict(required=True, type='str'),
            auth0_domain=dict(required=True, type='str'),
            search_engine=dict(required=False, default=None, type='str'),
            query=dict(type='str', required=True),
        ),
        supports_check_mode=False
    )

    auth0_domain=module.params['auth0_domain']
    auth0_token=module.params['auth0_token']
    query=module.params['query']
    search_engine=module.params['search_engine']

    http_headers = {
              'content-type': 'application/json',
              'Authorization': 'Bearer {token}'.format(token=auth0_token)
    }

    url_params = {
      'q': query,
      'search_engine': search_engine
    }

    url = 'https://{domain}/api/v2/users'.format(domain=auth0_domain)

    r = requests.get(url, params=url_params, headers=http_headers)

    if r.status_code != 200:
      module.fail_json(msg='Request to Auth0 failed with return code %s, reason: %s'%(r.status_code, r.reason))

    module.exit_json(results=json.loads(r.text))

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()

