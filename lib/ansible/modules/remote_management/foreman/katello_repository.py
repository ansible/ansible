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
module: katello_repository
short_description: Create and manage Katello repository
description:
    - Crate and manage a Katello repository
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
    name:
        description:
            - Name of the repository
        required: true
    product:
        description:
            - Product to which the repository lives in
        required: true
    organization:
        description:
            - Organization that the Product is in
        required: true
'''

EXAMPLES = '''
- name: "Create repository"
  local_action:
      module: katello
      username: "admin"
      password: "admin"
      server_url: "https://fakeserver.com"
      name: "My repository"
      type: "yum"
      product: "My Product"
      organization: "Default Organization"
'''

RETURN = '''# '''

import datetime

try:
    from nailgun import entities, entity_fields, entity_mixins
    from nailgun.config import ServerConfig
    HAS_NAILGUN_PACKAGE = True
except:
    HAS_NAILGUN_PACKAGE = False


class NailGun(object):
    def __init__(self, server, entities, module):
        self._server = server
        self._entities = entities
        self._module = module
        entity_mixins.TASK_TIMEOUT = 1000

    def find_organization(self, name):
        org = self._entities.Organization(self._server, name=name)
        response = org.search(set(), {'search': 'name={}'.format(name)})

        if len(response) == 1:
            return response[0]
        else:
            self._module.fail_json(msg="No organization found for %s" % name)

    def find_product(self, name, organization):
        org = self.find_organization(organization)

        product = self._entities.Product(self._server, name=name, organization=org)
        response = product.search()

        if len(response) == 1:
            return response[0]
        else:
            self._module.fail_json(msg="No Product found for %s" % name)

    def repository(self, name, type, product, organization):
        updated = False
        product = self.find_product(product, organization)

        repository = self._entities.Repository(self._server, name=name, product=product)
        repository._fields['organization'] = entity_fields.OneToOneField(entities.Organization)
        repository.organization = product.organization
        repository = repository.search()

        if len(repository) == 1:
            repository = repository[0]

        if repository and repository.name != name:
            repository = self._entities.Repository(self._server, name=name, id=repository.id)
            repository.update()
            updated = True
        elif not repository:
            repository = self._entities.Repository(
                    self._server,
                    name=name,
                    content_type=type,
                    product=product,
            )
            repository.create()
            updated = True
        
        return updated

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            username=dict(required=True, no_log=True),
            password=dict(required=True, no_log=True),
            verify_ssl=dict(required=False, type='bool', default=False),
            product=dict(required=True, no_log=False),
            organization=dict(required=True, no_log=False),
            name=dict(required=True, no_log=False),
            type=dict(required=True, no_log=False),
        ),
        supports_check_mode=True
    )

    if not HAS_NAILGUN_PACKAGE:
        module.fail_json(msg="Missing required nailgun module (check docs or install with: pip install nailgun")

    server_url = module.params['server_url']
    verify_ssl = module.params['verify_ssl']
    username = module.params['username']
    password = module.params['password']
    product = module.params['product']
    organization = module.params['organization']
    name = module.params['name']
    type = module.params['type']

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
        changed = ng.repository(name, type, product, organization)
        module.exit_json(changed=changed)
    except Exception as e:
        module.fail_json(msg=e)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
