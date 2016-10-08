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
module: foreman
short_description: Manage Foreman Resources
description:
    - Allows the management of Foreman resources inside your Foreman server
version_added: "2.3"
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
    entity:
        description:
            - The Foreman resource that the action will be performed on (e.g. organization, host)
        required: true
    params:
        description:
            - Parameters associated to the entity resource to set or edit in dictionary format (e.g. name, description)
        required: true
'''

EXAMPLES = '''
- name: "Create CI Organization"
  local_action:
      module: foreman
      username: "admin"
      password: "admin"
      server_url: "https://fakeserver.com"
      entity: "organization"
      params:
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

    def find_organization(self, name, **params):
        org = self._entities.Organization(self._server, name=name, **params)
        response = org.search(set(), {'search': 'name={}'.format(name)})

        if len(response) == 1:
            return response[0]
        else:
            self._module.fail_json(msg="No Content View found for %s" % name)

    def organization(self, params):
        name = params['name']
        del params['name']
        org = self.find_organization(name, **params)

        if org:
            org = self._entities.Organization(self._server, name=name, id=org.id, **params)
            org.update()
        else:
            org = self._entities.Organization(self._server, name=name, **params)
            org.create()

        return True

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            username=dict(required=True, no_log=True),
            password=dict(required=True, no_log=True),
            entity=dict(required=True, no_log=False),
            verify_ssl=dict(required=False, type='bool', default=False),
            params=dict(required=True, no_log=True, type='dict'),
        ),
        supports_check_mode=True
    )

    if not HAS_NAILGUN_PACKAGE:
        module.fail_json(msg="Missing required nailgun module (check docs or install with: pip install nailgun")

    server_url = module.params['server_url']
    username = module.params['username']
    password = module.params['password']
    entity = module.params['entity']
    params = module.params['params']
    verify_ssl = module.params['verify_ssl']

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

    if entity == 'organization':
        ng.organization(params)
        module.exit_json(changed=True, result="%s updated" % entity)
    else:
        module.fail_json(changed=False, result="Unsupported entity supplied")

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
