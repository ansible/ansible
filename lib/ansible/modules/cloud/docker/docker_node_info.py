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
module: docker_node_info

short_description: Retrieves facts about docker swarm node from Swarm Manager

description:
  - Retrieves facts about a docker node.
  - Essentially returns the output of C(docker node inspect <name>).
  - Must be executed on a host running as Swarm Manager, otherwise the module will fail.

version_added: "2.8"

options:
  name:
    description:
      - The name of the node to inspect.
      - The list of nodes names to inspect.
      - If empty then return information of all nodes in Swarm cluster.
      - When identifying the node use either the hostname of the node (as registered in Swarm) or node ID.
      - If I(self) is C(true) then this parameter is ignored.
    type: list
  self:
    description:
      - If C(true), queries the node (i.e. the docker daemon) the module communicates with.
      - If C(true) then I(name) is ignored.
      - If C(false) then query depends on I(name) presence and value.
    type: bool
    default: no
extends_documentation_fragment:
  - docker
  - docker.docker_py_1_documentation

author:
  - Piotr Wojciechowski (@wojciechowskipiotr)

requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 2.4.0"
  - "Docker API >= 1.24"
'''

EXAMPLES = '''
- name: Get info on all nodes
  docker_node_info:
  register: result

- name: Get info on node
  docker_node_info:
    name: mynode
  register: result

- name: Get info on list of nodes
  docker_node_info:
    name:
      - mynode1
      - mynode2
  register: result

- name: Get info on host if it is Swarm Manager
  docker_node_info:
    self: true
  register: result
'''

RETURN = '''
nodes:
    description:
      - Facts representing the current state of the nodes. Matches the C(docker node inspect) output.
      - Can contain multiple entries if more than one node provided in I(name), or I(name) is not provided.
      - If I(name) contains a list of nodes, the output will provide information on all nodes registered
        at the swarm, including nodes that left the swarm but haven't been removed from the cluster on swarm
        managers and nodes that are unreachable.
    returned: always
    type: list
'''

import traceback

from ansible.module_utils.docker.common import (
    RequestException,
)
from ansible.module_utils.docker.swarm import AnsibleDockerSwarmClient

try:
    from docker.errors import DockerException
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass


def get_node_facts(client):

    results = []

    if client.module.params['self'] is True:
        self_node_id = client.get_swarm_node_id()
        node_info = client.get_node_inspect(node_id=self_node_id)
        results.append(node_info)
        return results

    if client.module.params['name'] is None:
        node_info = client.get_all_nodes_inspect()
        return node_info

    nodes = client.module.params['name']
    if not isinstance(nodes, list):
        nodes = [nodes]

    for next_node_name in nodes:
        next_node_info = client.get_node_inspect(node_id=next_node_name, skip_missing=True)
        if next_node_info:
            results.append(next_node_info)
    return results


def main():
    argument_spec = dict(
        name=dict(type='list', elements='str'),
        self=dict(type='bool', default=False),
    )

    client = AnsibleDockerSwarmClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='2.4.0',
        min_docker_api_version='1.24',
    )

    client.fail_task_if_not_swarm_manager()

    try:
        nodes = get_node_facts(client)

        client.module.exit_json(
            changed=False,
            nodes=nodes,
        )
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
