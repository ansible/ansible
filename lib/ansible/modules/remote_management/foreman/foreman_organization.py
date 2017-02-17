#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2016, Eric D Helms <ericdhelms@gmail.com>
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
module: foreman_organization
short_description: Manage Foreman Organization
description:
    - Manage Foreman Organization
author: "Eric D Helms (@ehelms)"
requirements:
    - "nailgun >= 0.28.0"
    - "python >= 2.6"
    - datetime
options:
    server_url:
        description:
            - URL of Foreman server
        required: true
    username:
        description:
            - Username on Foreman server
        required: true
    password:
        description:
            - Password for user accessing Foreman server
        required: true
    verify_ssl:
        description:
            - Verify SSL of the Foreman server
        required: false
    name:
        description:
            - Name of the Foreman organization
        required: true
'''

EXAMPLES = '''
- name: "Create CI Organization"
  local_action:
      module: foreman_organization
      username: "admin"
      password: "admin"
      server_url: "https://fakeserver.com"
      name: "My Cool New Organization"
'''

RETURN = '''# '''

import datetime

try:
    from nailgun import entities, entity_fields
    from nailgun.config import ServerConfig
    HAS_NAILGUN_PACKAGE = True
except:
    HAS_NAILGUN_PACKAGE = False

class NailGun(object):
    def __init__(self, server, entities, module):
        self._server = server
        self._entities = entities
        self._module = module

    def organization(self, name):
        org = self._entities.Organization(self._server, name=name)
        org = org.search(set(), {'search': 'name={}'.format(name)})[0]
        updated = False

        if org and org.name != name:
            org = self._entities.Organization(self._server, name=name, id=org.id)
            org.update()
            updated = True
        elif not org:
            org = self._entities.Organization(self._server, name=name)
            org.create()
            updated = True

        return updated

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            username=dict(required=True, no_log=True),
            password=dict(required=True, no_log=True),
            verify_ssl=dict(required=False, type='bool', default=False),
            name=dict(required=True, no_log=False),
        ),
        supports_check_mode=True
    )

    if not HAS_NAILGUN_PACKAGE:
        module.fail_json(msg="Missing required nailgun module (check docs or install with: pip install nailgun")

    server_url = module.params['server_url']
    username = module.params['username']
    password = module.params['password']
    verify_ssl = module.params['verify_ssl']
    name = module.params['name']

    server = ServerConfig(
        url=server_url,
        auth=(username, password),
        verify=verify_ssl
    )
    ng = NailGun(server, entities, module)

    # Lets make an connection to the server with username and password
    try:
        org = entities.Organization(server)
        org.search()
    except Exception as e:
        module.fail_json(msg="Failed to connect to Foreman server: %s " % e)

    try:
        changed = ng.organization(name)
        module.exit_json(changed=changed)
    except Exception as e:
        module.fail_json(msg=e)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
