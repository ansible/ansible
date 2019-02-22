#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Eric D Helms <ericdhelms@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: katello
short_description: Manage Katello Resources
deprecated:
    removed_in: "2.12"
    why: "Replaced by re-designed individual modules living at https://github.com/theforeman/foreman-ansible-modules"
    alternative: https://github.com/theforeman/foreman-ansible-modules
description:
    - Allows the management of Katello resources inside your Foreman server.
version_added: "2.3"
author:
- Eric D Helms (@ehelms)
requirements:
    - nailgun >= 0.28.0
    - python >= 2.6
    - datetime
options:
    server_url:
        description:
            - URL of Foreman server.
        required: true
    username:
        description:
            - Username on Foreman server.
        required: true
    password:
        description:
            - Password for user accessing Foreman server.
        required: true
    entity:
        description:
            - The Foreman resource that the action will be performed on (e.g. organization, host).
        choices:

            - repository
            - manifest
            - repository_set
            - sync_plan
            - content_view
            - lifecycle_environment
            - activation_key
            - product

        required: true
    action:
        description:
            - action associated to the entity resource to set or edit in dictionary format.
            - Possible Action in relation to Entitys.
            - "sync (available when entity=product or entity=repository)"
            - "publish (available when entity=content_view)"
            - "promote (available when entity=content_view)"
        choices:
            - sync
            - publish
            - promote
        required: false
    params:
        description:
            - Parameters associated to the entity resource and action, to set or edit in dictionary format.
            - Each choice may be only available with specific entitys and actions.
            - "Possible Choices are in the format of param_name ([entry,action,action,...],[entity,..],...)."
            - The action "None" means no action specified.
            - Possible Params in relation to entity and action.
            - "name ([product,sync,None], [repository,sync], [repository_set,None], [sync_plan,None],"
            - "[content_view,promote,publish,None], [lifecycle_environment,None], [activation_key,None])"
            - "organization ([product,sync,None] ,[repository,sync,None], [repository_set,None], [sync_plan,None], "
            - "[content_view,promote,publish,None], [lifecycle_environment,None], [activation_key,None])"
            - "content ([manifest,None])"
            - "product ([repository,sync,None], [repository_set,None], [sync_plan,None])"
            - "basearch ([repository_set,None])"
            - "releaserver ([repository_set,None])"
            - "sync_date ([sync_plan,None])"
            - "interval ([sync_plan,None])"
            - "repositories ([content_view,None])"
            - "from_environment ([content_view,promote])"
            - "to_environment([content_view,promote])"
            - "prior ([lifecycle_environment,None])"
            - "content_view ([activation_key,None])"
            - "lifecycle_environment ([activation_key,None])"
        required: true
    task_timeout:
        description:
            - The timeout in seconds to wait for the started Foreman action to finish.
            - If the timeout is reached and the Foreman action did not complete, the ansible task fails. However the foreman action does not get canceled.
        default: 1000
        version_added: "2.7"
        required: false
    verify_ssl:
        description:
            - verify the ssl/https connection (e.g for a valid certificate)
        default: false
        type: bool
        required: false
'''

EXAMPLES = '''
---
# Simple Example:

- name: Create Product
  katello:
      username: admin
      password: admin
      server_url: https://fakeserver.com
      entity: product
      params:
        name: Centos 7
  delegate_to: localhost

# Abstraction Example:
# katello.yml
---
- name: "{{ name }}"
  katello:
      username: admin
      password: admin
      server_url: https://fakeserver.com
      entity: "{{ entity }}"
      params: "{{ params }}"
  delegate_to: localhost

# tasks.yml
---
- include: katello.yml
  vars:
    name: Create Dev Environment
    entity: lifecycle_environment
    params:
      name: Dev
      prior: Library
      organization: Default Organization

- include: katello.yml
  vars:
    name: Create Centos Product
    entity: product
    params:
      name: Centos 7
      organization: Default Organization

- include: katello.yml
  vars:
    name: Create 7.2 Repository
    entity: repository
    params:
      name: Centos 7.2
      product: Centos 7
      organization: Default Organization
      content_type: yum
      url: http://mirror.centos.org/centos/7/os/x86_64/

- include: katello.yml
  vars:
      name: Create Centos 7 View
      entity: content_view
      params:
        name: Centos 7 View
        organization: Default Organization
        repositories:
          - name: Centos 7.2
            product: Centos 7

- include: katello.yml
  vars:
      name: Enable RHEL Product
      entity: repository_set
      params:
        name: Red Hat Enterprise Linux 7 Server (RPMs)
        product: Red Hat Enterprise Linux Server
        organization: Default Organization
        basearch: x86_64
        releasever: 7

- include: katello.yml
  vars:
      name: Promote Contentview Environment with longer timout
      task_timeout: 10800
      entity: content_view
      action: promote
      params:
        name: MyContentView
        organization: MyOrganisation
        from_environment: Testing
        to_environment: Production

# Best Practices

# In Foreman, things can be done in paralell.
# When a conflicting action is already running,
# the task will fail instantly instead of waiting for the already running action to complete.
# So you sould use a "until success" loop to catch this.

- name: Promote Contentview Environment with increased Timeout
  katello:
  username: ansibleuser
  password: supersecret
  task_timeout: 10800
  entity: content_view
  action: promote
  params:
    name: MyContentView
    organization: MyOrganisation
    from_environment: Testing
    to_environment: Production
  register: task_result
  until: task_result is success
  retries: 9
  delay: 120

'''

RETURN = '''# '''

import datetime
import os
import traceback

try:
    from nailgun import entities, entity_fields, entity_mixins
    from nailgun.config import ServerConfig
    HAS_NAILGUN_PACKAGE = True
except Exception:
    HAS_NAILGUN_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class NailGun(object):
    def __init__(self, server, entities, module, task_timeout):
        self._server = server
        self._entities = entities
        self._module = module
        entity_mixins.TASK_TIMEOUT = task_timeout

    def find_organization(self, name, **params):
        org = self._entities.Organization(self._server, name=name, **params)
        response = org.search(set(), {'search': 'name={0}'.format(name)})

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
        except Exception as e:

            if "Import is the same as existing data" in e.message:
                return False
            else:
                self._module.fail_json(msg="Manifest import failed with %s" % to_native(e),
                                       exception=traceback.format_exc())

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

            if 'releasever' in params:
                formatted_name.append(params['releasever'])

            formatted_name = ' '.join(formatted_name)

            repository = self._entities.Repository(self._server, product=product, name=formatted_name)
            repository._fields['organization'] = entity_fields.OneToOneField(entities.Organization)
            repository.organization = product.organization
            repository = repository.search()

            if len(repository) == 0:
                if 'releasever' in params:
                    reposet.enable(data={'basearch': params['basearch'], 'releasever': params['releasever']})
                else:
                    reposet.enable(data={'basearch': params['basearch']})

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
            server_url=dict(type='str', required=True),
            username=dict(type='str', required=True, no_log=True),
            password=dict(type='str', required=True, no_log=True),
            entity=dict(type='str', required=True,
                        choices=['repository', 'manifest', 'repository_set', 'sync_plan',
                                 'content_view', 'lifecycle_environment', 'activation_key', 'product']),
            action=dict(type='str', choices=['sync', 'publish', 'promote']),
            verify_ssl=dict(type='bool', default=False),
            task_timeout=dict(type='int', default=1000),
            params=dict(type='dict', required=True, no_log=True),
        ),
        supports_check_mode=True,
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
    task_timeout = module.params['task_timeout']

    server = ServerConfig(
        url=server_url,
        auth=(username, password),
        verify=verify_ssl
    )
    ng = NailGun(server, entities, module, task_timeout)

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


if __name__ == '__main__':
    main()
