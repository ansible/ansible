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
module: katello
short_description: Manage Katello Resources
description:
    - Allows the management of Katello resources inside your Foreman server
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
Simple Example:

- name: "Create Product"
  local_action:
      module: katello
      username: "admin"
      password: "admin"
      server_url: "https://fakeserver.com"
      entity: "product"
      params:
        name: "Centos 7"

Abstraction Example:

katello.yml
---
- name: "{{ name }}"
  local_action:
      module: katello
      username: "admin"
      password: "admin"
      server_url: "https://fakeserver.com"
      entity: "{{ entity }}"
      params: "{{ params }}"

tasks.yml
---
- include: katello.yml
  vars:
    name: "Create Dev Environment"
    entity: "lifecycle_environment"
    params:
      name: "Dev"
      prior: "Library"
      organization: "Default Organization"

- include: katello.yml
  vars:
    name: "Create Centos Product"
    entity: "product"
    params:
      name: "Centos 7"
      organization: "Default Organization"

- include: katello.yml
  vars:
    name: "Create 7.2 Repository"
    entity: "repository"
    params:
      name: "Centos 7.2"
      product: "Centos 7"
      organization: "Default Organization"
      content_type: "yum"
      url: "http://mirror.centos.org/centos/7/os/x86_64/"

- include: katello.yml
  vars:
      name: "Create Centos 7 View"
      entity: "content_view"
      params:
        name: "Centos 7 View"
        organization: "Default Organization"
        repositories:
          - name: "Centos 7.2"
            product: "Centos 7"

- include: katello.yml
  vars:
      name: "Enable RHEL Product"
      entity: "repository_set"
      params:
        name: "Red Hat Enterprise Linux 7 Server (RPMs)"
        product: "Red Hat Enterprise Linux Server"
        organization: "Default Organization"
        basearch: "x86_64"
        releasever: "7"
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

    def find_organization(self, name, **params):
        org = self._entities.Organization(self._server, name=name, **params)
        response = org.search(set(), {'search': 'name={}'.format(name)})

        if len(response) == 1:
            return response[0]
        else:
            self._module.fail_json(msg="No organization found for %s" % name)

    def find_lifecycle_environment(self, name, organization):
        org = self.find_organization(organization)

        lifecycle_env = self._entities.LifecycleEnvironment(self._server, name=name, organization=org)
        response = lifecycle_env.search()

        if len(response) == 1:
            return response[0]
        else:
            self._module.fail_json(msg="No Lifecycle Found found for %s" % name)

    def find_product(self, name, organization):
        org = self.find_organization(organization)

        product = self._entities.Product(self._server, name=name, organization=org)
        response = product.search()

        if len(response) == 1:
            return response[0]
        else:
            self._module.fail_json(msg="No Product found for %s" % name)

    def find_repository(self, name, product, organization):
        product = self.find_product(product, organization)

        repository = self._entities.Repository(self._server, name=name, product=product)
        repository._fields['organization'] = entity_fields.OneToOneField(entities.Organization)
        repository.organization = product.organization
        response = repository.search()

        if len(response) == 1:
            return response[0]
        else:
            self._module.fail_json(msg="No Repository found for %s" % name)

    def find_content_view(self, name, organization):
        org = self.find_organization(organization)

        content_view = self._entities.ContentView(self._server, name=name, organization=org)
        response = content_view.search()

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

    def manifest(self, params):
        org = self.find_organization(params['organization'])
        params['organization'] = org.id

        try:
            file = open(os.getcwd() + params['content'], 'r')
            content = file.read()
        finally:
            file.close()

        manifest = self._entities.Subscription(self._server)

        try:
            manifest.upload(
                data={'organization_id': org.id},
                files={'content': content}
            )
            return True
        except Exception:
            e = get_exception()
            
            if "Import is the same as existing data" in e.message:
                return True
            else:
                self._module.fail_json(msg="Manifest import failed with %s" % e)

    def product(self, params):
        org = self.find_organization(params['organization'])
        params['organization'] = org.id

        product = self._entities.Product(self._server, **params)
        response = product.search()

        if len(response) == 1:
            product.id = response[0].id
            product.update()
        else:
            product.create()

        return True
        
    def sync_product(self, params):
        org = self.find_organization(params['organization'])
        product = self.find_product(params['name'], org.name)

        return product.sync()

    def repository(self, params):
        product = self.find_product(params['product'], params['organization'])
        params['product'] = product.id
        del params['organization']

        repository = self._entities.Repository(self._server, **params)
        repository._fields['organization'] = entity_fields.OneToOneField(entities.Organization)
        repository.organization = product.organization
        response = repository.search()

        if len(response) == 1:
            repository.id = response[0].id
            repository.update()
        else:
            repository.create()

        return True
        
    def sync_repository(self, params):
        org = self.find_organization(params['organization'])
        repository = self.find_repository(params['name'], params['product'], org.name)

        return repository.sync()

    def repository_set(self, params):
        product = self.find_product(params['product'], params['organization'])
        del params['product']
        del params['organization']

        if not product:
            return False
        else:
            reposet = self._entities.RepositorySet(self._server, product=product, name=params['name'])
            reposet = reposet.search()[0]

            formatted_name = [params['name'].replace('(', '').replace(')', '')]
            formatted_name.append(params['basearch'])

            if params['releasever']:
                formatted_name.append(params['releasever'])

            formatted_name = ' '.join(formatted_name)

            repository = self._entities.Repository(self._server, product=product, name=formatted_name)
            repository._fields['organization'] = entity_fields.OneToOneField(entities.Organization)
            repository.organization = product.organization
            repository = repository.search()

            if len(repository) == 0:
                reposet.enable(data={'basearch': params['basearch'], 'releasever': params['releasever']})

        return True

    def sync_plan(self, params):
        org = self.find_organization(params['organization'])
        params['organization'] = org.id
        params['sync_date'] = datetime.datetime.strptime(params['sync_date'], "%H:%M")

        products = params['products']
        del params['products']

        sync_plan = self._entities.SyncPlan(
            self._server,
            name=params['name'],
            organization=org
        )
        response = sync_plan.search()

        sync_plan.sync_date = params['sync_date']
        sync_plan.interval = params['interval']

        if len(response) == 1:
            sync_plan.id = response[0].id
            sync_plan.update()
        else:
            response = sync_plan.create()
            sync_plan.id = response[0].id

        if products:
            ids = []

            for name in products:
                product = self.find_product(name, org.name)
                ids.append(product.id)
            
            sync_plan.add_products(data={'product_ids': ids})

        return True

    def content_view(self, params):
        org = self.find_organization(params['organization'])

        content_view = self._entities.ContentView(self._server, name=params['name'], organization=org)
        response = content_view.search()

        if len(response) == 1:
            content_view.id = response[0].id
            content_view.update()
        else:
            content_view = content_view.create()
        
        if params['repositories']:
            repos = []

            for repository in params['repositories']:
                repository = self.find_repository(repository['name'], repository['product'], org.name)
                repos.append(repository)

            content_view.repository = repos
            content_view.update(['repository'])

    def find_content_view(self, name, organization):
        org = self.find_organization(organization)

        content_view = self._entities.ContentView(self._server, name=name, organization=org)
        response = content_view.search()

        if len(response) == 1:
            return response[0]
        else:
            self._module.fail_json(msg="No Content View found for %s" % name)

    def find_content_view_version(self, name, organization, environment):
        env = self.find_lifecycle_environment(environment, organization)
        content_view = self.find_content_view(name, organization)

        content_view_version = self._entities.ContentViewVersion(self._server, content_view=content_view)
        response = content_view_version.search(['content_view'], {'environment_id': env.id})

        if len(response) == 1:
            return response[0]
        else:
            self._module.fail_json(msg="No Content View version found for %s" % response)

    def publish(self, params):
        content_view = self.find_content_view(params['name'], params['organization'])

        return content_view.publish()

    def promote(self, params):
        to_environment = self.find_lifecycle_environment(params['to_environment'], params['organization'])
        version = self.find_content_view_version(params['name'], params['organization'], params['from_environment'])

        data = {'environment_id': to_environment.id}
        return version.promote(data=data)

    def lifecycle_environment(self, params):
        org = self.find_organization(params['organization'])
        prior_env = self.find_lifecycle_environment(params['prior'], params['organization'])

        lifecycle_env = self._entities.LifecycleEnvironment(self._server, name=params['name'], organization=org, prior=prior_env)
        response = lifecycle_env.search()

        if len(response) == 1:
            lifecycle_env.id = response[0].id
            lifecycle_env.update()
        else:
            lifecycle_env.create()

        return True

    def activation_key(self, params):
        org = self.find_organization(params['organization'])

        activation_key = self._entities.ActivationKey(self._server, name=params['name'], organization=org)
        response = activation_key.search()

        if len(response) == 1:
            activation_key.id = response[0].id
            activation_key.update()
        else:
            activation_key.create()

        if params['content_view']:
            content_view = self.find_content_view(params['content_view'], params['organization'])
            lifecycle_environment = self.find_lifecycle_environment(params['lifecycle_environment'], params['organization'])

            activation_key.content_view = content_view
            activation_key.environment = lifecycle_environment
            activation_key.update()

        return True

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            username=dict(required=True, no_log=True),
            password=dict(required=True, no_log=True),
            entity=dict(required=True, no_log=False),
            action=dict(required=False, no_log=False),
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
    action = module.params['action']
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

    result = False

    if entity == 'product':
        if action == 'sync':
            result = ng.sync_product(params)
        else:
            result = ng.product(params)
    elif entity == 'repository':
        if action == 'sync':
            result = ng.sync_repository(params)
        else:
            result = ng.repository(params)
    elif entity == 'manifest':
        result = ng.manifest(params)
    elif entity == 'repository_set':
        result = ng.repository_set(params)
    elif entity == 'sync_plan':
        result = ng.sync_plan(params)
    elif entity == 'content_view':
        if action == 'publish':
            result = ng.publish(params)
        elif action == 'promote':
            result = ng.promote(params)
        else:
            result = ng.content_view(params)
    elif entity == 'lifecycle_environment':
        result = ng.lifecycle_environment(params)
    elif entity == 'activation_key':
        result = ng.activation_key(params)
    else:
        module.fail_json(changed=False, result="Unsupported entity supplied")

    module.exit_json(changed=result, result="%s updated" % entity)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
