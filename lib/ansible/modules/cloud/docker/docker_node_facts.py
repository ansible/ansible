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
module: docker_node_facts

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
    required: false
    type: str
  self:
    description:
      - If C(true), queries the node (i.e. the docker daemon) the module communicates with.
      - If C(true) then I(name) is ignored.
      - If C(false) then query depends on I(name) presence and value.
    required: false
    type: bool
    default: false
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
    - "Docker API >= 1.24"
'''

EXAMPLES = '''
- name: Get info on all nodes
  docker_node_facts:
  register: result

- name: Get info on node
  docker_node_facts:
    name: mynode
  register: result

- name: Get info on list of nodes
  docker_node_facts:
    name:
      - mynode1
      - mynode2
  register: result

- name: Get info on host if it is Swarm Manager
  docker_node_facts:
    self: true
  register: result
'''

RETURN = '''
nodes_facts:
    description:
      - Facts representing the current state of the nodes. Matches the C(docker node inspect) output.
      - Will be C(none) if node does not exist.
      - Will contain multiple entries if more than one node provided in I(name).
      - If I(name) contains list of nodes, the output will contain information only about registered nodes.
    returned: always
    type: list
'''

from ansible.module_utils.docker_swarm import AnsibleDockerSwarmClient

try:
    from docker.errors import APIError, NotFound
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass


def get_node_facts(client):

    results = []

    if client.module.params['self'] is True:
        try:
            self_node_id = client.get_swarm_node_id()
        except APIError:
            return None
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
        self=dict(type='bool', default='False'),
    )

    client = AnsibleDockerSwarmClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='1.10.0',
        min_docker_api_version='1.24',
    )

    client.fail_task_if_not_swarm_manager()

    node = get_node_facts(client)

    client.module.exit_json(
        changed=False,
        nodes_facts=node,
    )


if __name__ == '__main__':
    main()
