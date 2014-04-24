#!/usr/bin/python

# vim: ts=4:expandtab:au BufWritePost
# (c) 2014, Patrick "CaptTofu" Galbraith <patg@patg.net>
# Code also from rax_facts and the primary docker module
#
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

# This is a DOCUMENTATION stub specific to this module, it extends
# a documentation fragment located in ansible.utils.module_docs_fragments
DOCUMENTATION = '''
---
module: docker_facts
short_description: Gather facts for Docker containers
description:
     - Gather facts for Docker containers and images
version_added: "0.1"
options:
  id:
    description:
      - container ID to retrieve facts for
    default: null (all containers if neither name nor id specified)
  name:
    description:
      - container name to retrieve facts for
    default: null (all containers if neither name nor id specified)
  images:
    description:
      - image name or 'all'. Off by default.
    default: null
author: Patrick Galbraith
'''

EXAMPLES = '''
- name: Gather info about containers
  hosts: localhost
  gather_facts: False
  tasks:
    - name: Get facts about containers
      local_action:
        module: docker_facts
        name: container1

- name: Gather info about all containers and images
  hosts: docker
  gather_facts: True
  tasks:
    - name: Get facts about containers
      local_action:
        module: docker_facts
        images: all

    - name: containers debug info
      debug: msg="Container Name {{ item.key }} IP Address {{ item.value.docker_networksettings.IPAddress }}"
      with_dict: docker_containers

    - name: images info
      debug: msg="Image ID {{ item.key }} Author {{ item.value.docker_author }} Repo Tags {{ item.value.docker_repotags }}"
      with_dict: docker_images

'''

HAS_DOCKER_PY = True

import re
from urlparse import urlparse
try:
    import docker
    try:
        from docker.errors import APIError as DockerAPIError
    except ImportError:
        from docker.client import APIError as DockerAPIError
except ImportError:
    HAS_DOCKER_PY = False


class DockerManager:

    def __init__(self, module):
        self.module = module
        docker_url = urlparse(module.params.get('docker_url'))
        self.container_id = module.params.get('id')
        self.name = module.params.get('name')
        self.images = module.params.get('images')
        self.all_containers = not (self.name or self.container_id)

        self.client = docker.Client(base_url=docker_url.geturl())
        if self.client is None:
            module.fail_json(msg="Failed to instantiate docker client. This "
                                 "could mean that docker isn't running.")

    def docker_facts_slugify(self, value):
        return 'docker_%s' % (re.sub('[^\w-]', '_', value).lower().lstrip('_'))

    def get_inspect(self, id, type='container'):
        facts = dict()
        if type == 'images':
            inspect = self.client.inspect_image(id)
        else:
            inspect = self.client.inspect_container(id)

        for key in inspect:
            fact_key = self.docker_facts_slugify(key)
            facts[fact_key] = inspect.get(key)

        facts['docker_short_id'] = id[:13]
        return facts

    def entity_conform(self, entity):
        new_entity = dict()

        for key in entity:
            new_key = self.docker_facts_slugify(key)
            new_entity[new_key] = entity.get(key)

        return new_entity

    def search(self, entities, type='containers'):
        search_list = []

        if type == 'images':
            id = self.images
            name = None
        else:
            id = self.container_id
            name = self.name

        for entity in entities:
            entity_name = ''
            # by name, get by name
            if name:
                # names have a leading '/'
                if not name.startswith('/'):
                    entity_name = '/' + name
                if (entity_name in entity['Names']):
                    search_list.append(entity)
            # by name, get by name
            elif id:
                # container_id could be any length, but internally
                # with docker is 64 chars
                if id in entity['Id']:
                    search_list.append(entity)

        # an ID should never yield more than one, but in case
        if len(entity) > 1 and id and type == 'containers':
            module.fail_json(msg='Multiple items found for container id '
                                 '%s' % id)

        return search_list

    def get_facts(self, entities, type='containers'):
        facts = dict()
        entity_dict = dict()
        for entity in entities:
            id = entity.get('Id')
            short_id = id[:13]
            name = short_id

            if type == 'containers':
                try:
                    name = entity.get('Names', list()).pop(0).lstrip('/')
                except IndexError:
                    name = short_id

            entity_dict[name] = self.get_inspect(id, type)
            entity = self.entity_conform(entity)
            # merge both, since both have different members that
            # are useful information
            entity_dict[name] = dict(entity_dict[name].items() +
                                     entity.items())

        facts['docker_' + type] = entity_dict
        return facts

    def docker_facts(self, module):
        changed = False
        # get all containers
        containers = self.client.containers(all=True)

        # limits the containers to only those specified by name or ID
        if not self.all_containers:
            # reduce list to specific containers
            containers = self.search(containers)

        # obtain inspection info and convert to facts dict
        ansible_facts = self.get_facts(containers)

        if self.images:
            images = self.client.images(all=True)
            # limits the images to only those specified by ID
            if self.images != 'all':
                images = self.search(images, 'images')

            # obtain inspection info and convert to facts dict
            image_facts = self.get_facts(images, 'images')
            if len(image_facts):
                ansible_facts = dict(ansible_facts.items() +
                                     image_facts.items())

        module.exit_json(changed=changed, ansible_facts=ansible_facts)


def main():
    if not HAS_DOCKER_PY:
        module.fail_json(msg=
                         'The docker python client is required \
                         for this module')
    argument_spec = dict(
        docker_url=dict(default='unix://var/run/docker.sock'),
        id=dict(default=None),
        name=dict(default=None),
        images=dict(default=None)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['id', 'name']]
    )

    manager = DockerManager(module)

    manager.docker_facts(module)

# import module snippets
from ansible.module_utils.basic import *

### invoke the module
main()
