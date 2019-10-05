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
module: docker_swarm_info

short_description: Retrieves facts about Docker Swarm cluster.

description:
  - Retrieves facts about a Docker Swarm.
  - Returns lists of swarm objects names for the services - nodes, services, tasks.
  - The output differs depending on API version available on docker host.
  - Must be run on Swarm Manager node; otherwise module fails with error message.
    It does return boolean flags in on both error and success which indicate whether
    the docker daemon can be communicated with, whether it is in Swarm mode, and
    whether it is a Swarm Manager node.

version_added: "2.8"

author:
    - Piotr Wojciechowski (@WojciechowskiPiotr)

options:
  nodes:
    description:
      - Whether to list swarm nodes.
    type: bool
    default: no
  nodes_filters:
    description:
      - A dictionary of filter values used for selecting nodes to list.
      - "For example, C(name: mynode)."
      - See L(the docker documentation,https://docs.docker.com/engine/reference/commandline/node_ls/#filtering)
        for more information on possible filters.
    type: dict
  services:
    description:
      - Whether to list swarm services.
    type: bool
    default: no
  services_filters:
    description:
      - A dictionary of filter values used for selecting services to list.
      - "For example, C(name: myservice)."
      - See L(the docker documentation,https://docs.docker.com/engine/reference/commandline/service_ls/#filtering)
        for more information on possible filters.
    type: dict
  tasks:
    description:
      - Whether to list containers.
    type: bool
    default: no
  tasks_filters:
    description:
      - A dictionary of filter values used for selecting tasks to list.
      - "For example, C(node: mynode-1)."
      - See L(the docker documentation,https://docs.docker.com/engine/reference/commandline/service_ps/#filtering)
        for more information on possible filters.
    type: dict
  unlock_key:
    description:
      - Whether to retrieve the swarm unlock key.
    type: bool
    default: no
  verbose_output:
    description:
      - When set to C(yes) and I(nodes), I(services) or I(tasks) is set to C(yes), then the module output will
        contain verbose information about objects matching the full output of API method.
      - For details see the documentation of your version of Docker API at U(https://docs.docker.com/engine/api/).
      - The verbose output in this module contains only subset of information returned by I(_info) module
        for each type of the objects.
    type: bool
    default: no
extends_documentation_fragment:
  - docker
  - docker.docker_py_1_documentation

requirements:
    - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 1.10.0 (use L(docker-py,https://pypi.org/project/docker-py/) for Python 2.6)"
    - "Docker API >= 1.24"
'''

EXAMPLES = '''
- name: Get info on Docker Swarm
  docker_swarm_info:
  ignore_errors: yes
  register: result

- name: Inform about basic flags
  debug:
    msg: |
      Was able to talk to docker daemon: {{ result.can_talk_to_docker }}
      Docker in Swarm mode: {{ result.docker_swarm_active }}
      This is a Manager node: {{ result.docker_swarm_manager }}

- block:

- name: Get info on Docker Swarm and list of registered nodes
  docker_swarm_info:
    nodes: yes
  register: result

- name: Get info on Docker Swarm and extended list of registered nodes
  docker_swarm_info:
    nodes: yes
    verbose_output: yes
  register: result

- name: Get info on Docker Swarm and filtered list of registered nodes
  docker_swarm_info:
    nodes: yes
    nodes_filter:
      name: mynode
  register: result

- debug:
    var: result.swarm_facts

- name: Get the swarm unlock key
  docker_swarm_info:
    unlock_key: yes
  register: result

- debug:
    var: result.swarm_unlock_key

'''

RETURN = '''
can_talk_to_docker:
    description:
      - Will be C(true) if the module can talk to the docker daemon.
    returned: both on success and on error
    type: bool
docker_swarm_active:
    description:
      - Will be C(true) if the module can talk to the docker daemon,
        and the docker daemon is in Swarm mode.
    returned: both on success and on error
    type: bool
docker_swarm_manager:
    description:
      - Will be C(true) if the module can talk to the docker daemon,
        the docker daemon is in Swarm mode, and the current node is
        a manager node.
      - Only if this one is C(true), the module will not fail.
    returned: both on success and on error
    type: bool
swarm_facts:
    description:
      - Facts representing the basic state of the docker Swarm cluster.
      - Contains tokens to connect to the Swarm
    returned: always
    type: dict
swarm_unlock_key:
    description:
      - Contains the key needed to unlock the swarm.
    returned: When I(unlock_key) is C(true).
    type: str
nodes:
    description:
      - List of dict objects containing the basic information about each volume.
        Keys matches the C(docker node ls) output unless I(verbose_output=yes).
        See description for I(verbose_output).
    returned: When I(nodes) is C(yes)
    type: list
services:
    description:
      - List of dict objects containing the basic information about each volume.
        Keys matches the C(docker service ls) output unless I(verbose_output=yes).
        See description for I(verbose_output).
    returned: When I(services) is C(yes)
    type: list
tasks:
    description:
      - List of dict objects containing the basic information about each volume.
        Keys matches the C(docker service ps) output unless I(verbose_output=yes).
        See description for I(verbose_output).
    returned: When I(tasks) is C(yes)
    type: list

'''

import traceback

try:
    from docker.errors import DockerException, APIError
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils._text import to_native

from ansible.module_utils.docker.swarm import AnsibleDockerSwarmClient
from ansible.module_utils.docker.common import (
    DockerBaseClass,
    clean_dict_booleans_for_docker_api,
    RequestException,
)


class DockerSwarmManager(DockerBaseClass):

    def __init__(self, client, results):

        super(DockerSwarmManager, self).__init__()

        self.client = client
        self.results = results
        self.verbose_output = self.client.module.params['verbose_output']

        listed_objects = ['tasks', 'services', 'nodes']

        self.client.fail_task_if_not_swarm_manager()

        self.results['swarm_facts'] = self.get_docker_swarm_facts()

        for docker_object in listed_objects:
            if self.client.module.params[docker_object]:
                returned_name = docker_object
                filter_name = docker_object + "_filters"
                filters = clean_dict_booleans_for_docker_api(client.module.params.get(filter_name))
                self.results[returned_name] = self.get_docker_items_list(docker_object, filters)
        if self.client.module.params['unlock_key']:
            self.results['swarm_unlock_key'] = self.get_docker_swarm_unlock_key()

    def get_docker_swarm_facts(self):
        try:
            return self.client.inspect_swarm()
        except APIError as exc:
            self.client.fail("Error inspecting docker swarm: %s" % to_native(exc))

    def get_docker_items_list(self, docker_object=None, filters=None):
        items = None
        items_list = []

        try:
            if docker_object == 'nodes':
                items = self.client.nodes(filters=filters)
            elif docker_object == 'tasks':
                items = self.client.tasks(filters=filters)
            elif docker_object == 'services':
                items = self.client.services(filters=filters)
        except APIError as exc:
            self.client.fail("Error inspecting docker swarm for object '%s': %s" %
                             (docker_object, to_native(exc)))

        if self.verbose_output:
            return items

        for item in items:
            item_record = dict()

            if docker_object == 'nodes':
                item_record = self.get_essential_facts_nodes(item)
            elif docker_object == 'tasks':
                item_record = self.get_essential_facts_tasks(item)
            elif docker_object == 'services':
                item_record = self.get_essential_facts_services(item)
                if item_record['Mode'] == 'Global':
                    item_record['Replicas'] = len(items)
            items_list.append(item_record)

        return items_list

    @staticmethod
    def get_essential_facts_nodes(item):
        object_essentials = dict()

        object_essentials['ID'] = item.get('ID')
        object_essentials['Hostname'] = item['Description']['Hostname']
        object_essentials['Status'] = item['Status']['State']
        object_essentials['Availability'] = item['Spec']['Availability']
        if 'ManagerStatus' in item:
            object_essentials['ManagerStatus'] = item['ManagerStatus']['Reachability']
            if 'Leader' in item['ManagerStatus'] and item['ManagerStatus']['Leader'] is True:
                object_essentials['ManagerStatus'] = "Leader"
        else:
            object_essentials['ManagerStatus'] = None
        object_essentials['EngineVersion'] = item['Description']['Engine']['EngineVersion']

        return object_essentials

    def get_essential_facts_tasks(self, item):
        object_essentials = dict()

        object_essentials['ID'] = item['ID']
        # Returning container ID to not trigger another connection to host
        # Container ID is sufficient to get extended info in other tasks
        object_essentials['ContainerID'] = item['Status']['ContainerStatus']['ContainerID']
        object_essentials['Image'] = item['Spec']['ContainerSpec']['Image']
        object_essentials['Node'] = self.client.get_node_name_by_id(item['NodeID'])
        object_essentials['DesiredState'] = item['DesiredState']
        object_essentials['CurrentState'] = item['Status']['State']
        if 'Err' in item['Status']:
            object_essentials['Error'] = item['Status']['Err']
        else:
            object_essentials['Error'] = None

        return object_essentials

    @staticmethod
    def get_essential_facts_services(item):
        object_essentials = dict()

        object_essentials['ID'] = item['ID']
        object_essentials['Name'] = item['Spec']['Name']
        if 'Replicated' in item['Spec']['Mode']:
            object_essentials['Mode'] = "Replicated"
            object_essentials['Replicas'] = item['Spec']['Mode']['Replicated']['Replicas']
        elif 'Global' in item['Spec']['Mode']:
            object_essentials['Mode'] = "Global"
            # Number of replicas have to be updated in calling method or may be left as None
            object_essentials['Replicas'] = None
        object_essentials['Image'] = item['Spec']['TaskTemplate']['ContainerSpec']['Image']
        if 'Ports' in item['Spec']['EndpointSpec']:
            object_essentials['Ports'] = item['Spec']['EndpointSpec']['Ports']
        else:
            object_essentials['Ports'] = []

        return object_essentials

    def get_docker_swarm_unlock_key(self):
        unlock_key = self.client.get_unlock_key() or {}
        return unlock_key.get('UnlockKey') or None


def main():
    argument_spec = dict(
        nodes=dict(type='bool', default=False),
        nodes_filters=dict(type='dict'),
        tasks=dict(type='bool', default=False),
        tasks_filters=dict(type='dict'),
        services=dict(type='bool', default=False),
        services_filters=dict(type='dict'),
        unlock_key=dict(type='bool', default=False),
        verbose_output=dict(type='bool', default=False),
    )
    option_minimal_versions = dict(
        unlock_key=dict(docker_py_version='2.7.0', docker_api_version='1.25'),
    )

    client = AnsibleDockerSwarmClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='1.10.0',
        min_docker_api_version='1.24',
        option_minimal_versions=option_minimal_versions,
        fail_results=dict(
            can_talk_to_docker=False,
            docker_swarm_active=False,
            docker_swarm_manager=False,
        ),
    )
    client.fail_results['can_talk_to_docker'] = True
    client.fail_results['docker_swarm_active'] = client.check_if_swarm_node()
    client.fail_results['docker_swarm_manager'] = client.check_if_swarm_manager()

    try:
        results = dict(
            changed=False,
        )

        DockerSwarmManager(client, results)
        results.update(client.fail_results)
        client.module.exit_json(**results)
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
