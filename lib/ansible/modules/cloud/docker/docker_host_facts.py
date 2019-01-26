#!/usr/bin/python
#
# (c) 2019 Piotr Wojciechowski <piotr@it-playground.pl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: docker_host_facts

short_description: Retrieves facts about docker host and lists of objects of the services

description:
  - Retrieves facts about a docker host.
  - Essentially returns the output of C(docker system info).
  - Returns lists of objects names for the services - images, networks, volumes, containers.
  - Returns disk usage information.
  - The output differs depending on API version available on docker host.
  - Must be executed on a host running a Docker, otherwise the module will fail.

version_added: "2.8"

options:
    services:
        description: List of services for which list of items should be listed in output

extends_documentation_fragment:
    - docker

author:
    - Piotr Wojciechowski (@wojciechowskipiotr)

requirements:
    - "python >= 2.6"
    - "docker-py >= 1.10.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       For Python 2.6, C(docker-py) must be used. Otherwise, it is recommended to
       install the C(docker) Python module. Note that both modules should I(not)
       be installed at the same time. Also note that when both modules are installed
       and one of them is uninstalled, the other might no longer function and a
       reinstall of it is required."
    - "Docker API >= 1.21"
'''

EXAMPLES = '''
- name: Get info on docker host
  docker_host_facts:
  register: result

'''

RETURN = '''
exists:
    description:
      - Returns whether the node exists in docker swarm cluster.
    type: bool
    returned: always
    sample: true
docker_host_facts:
    description:
      - Facts representing the current state of the docker host. Matches the C(docker system info) output.
    returned: always
    type: dict

'''

from ansible.module_utils.docker_common import AnsibleDockerClient, DockerBaseClass
from ansible.module_utils._text import to_native

try:
    from docker.errors import APIError, NotFound
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass


class DockerHostManager(DockerBaseClass):

    def __init__(self, client, results):

        super(DockerHostManager, self).__init__()

        self.client = client
        self.results = results

        listed_objects = ['volumes', 'networks', 'containers', 'images']

        self.results['docker_host_facts'] = self.get_docker_host_facts()

        for docker_object in listed_objects:
            if self.client.module.params[docker_object] is True:
                returned_name = "docker_" + docker_object + "_list"
                self.results[returned_name] = self.get_docker_items_list(docker_object)

    def get_docker_host_facts(self):
        try:
            return self.client.info()
        except APIError as exc:
            self.client.fail_json(msg="Error inspecting docker host: %s" % to_native(exc))

    def get_docker_items_list(self, object=None):
        items = None
        items_list = []

        header_containers = ['Id', 'Image', 'Command', 'Created', 'Status', 'Ports', 'Names']
        header_volumes = ['Driver', 'Name']
        header_images = ['Id', 'RepoTags', 'Created', 'Size']
        header_networks = ['Id', 'Driver', 'Name', 'Scope']

        try:
            if object == 'containers':
                items = self.client.containers()
            if object == 'networks':
                items = self.client.networks()
            if object == 'images':
                items = self.client.images()
            if object == 'volumes':
                items = self.client.volumes()
        except APIError as exc:
            self.client.fail_json(msg="Error inspecting docker host: %s" % to_native(exc))

        if object != 'volumes':
            for item in items:
                item_record = dict()

                if object == 'containers':
                    for key in header_containers:
                        item_record[key] = item.get(key)
                if object == 'networks':
                    for key in header_networks:
                        item_record[key] = item.get(key)
                if object == 'images':
                    for key in header_images:
                        item_record[key] = item.get(key)

                items_list.append(item_record)

        else:
            for item in items['Volumes']:
                item_record = dict()

                for key in header_volumes:
                    item_record[key] = item.get(key)

                items_list.append(item_record)

        return items_list


def main():
    argument_spec = dict(
        containers=dict(type='bool', default=False),
        containers_filters=dict(type='dict'),
        images=dict(type='bool', default=False),
        images_filters=dict(type='dict'),
        networks=dict(type='bool', default=False),
        networks_filters=dict(type='dict'),
        volumes=dict(type='bool', default=False),
        volumes_filters=dict(type='dict'),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='1.10.0',
        min_docker_api_version='1.21',
    )

    results = dict(
        changed=False,
        docker_host_facts=[]
    )

    DockerHostManager(client, results)
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
