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
module: docker_node
short_description: Manage Docker Swarm node
version_added: "2.8"
description:
    - Manages the Docker nodes via Swarm Manager
    - Change node role
    - Change node availability
    - List Swarm nodes
options:
    force:
        description:
            - Use with state C(present) to force creating a new Swarm, even if already part of one.
            - Use with state C(absent) to Leave the swarm even if this node is a manager.
        type: bool
        default: 'no'
    state:
        description:
            - Set to C(list) to display swarm nodes names lists.
            - Set to C(update) to update node labels, availability and role
        required: true
        default: list
        choices:
          - list
          - update
    name:
        description:
            - Swarm name of the node.
            - Used with I(state=update).
    labels:
        description:
            - User-defined key/value metadata.
    availability:
        description: Node availability status to assign
        choices:
          - active
          - pause
          - drain
    role:
        description: Node role to assign
        choices:
          - manager
          - worker
extends_documentation_fragment:
    - docker
requirements:
    - python >= 2.7
    - "docker >= 2.6.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       Version 2.1.0 or newer is only available with the C(docker) module."
    - Docker API >= 1.25
author:
  - Piotr Wojciechowski (@wojciechowskipiotr)
  - Thierry Bouvet (@tbouvet)

'''

EXAMPLES = '''
- name: List names of registered swarm nodes
  docker_node:
    state: list

- name: Set node role
  docker_node:
    state: update
    name: mynode
    role: manager

- name: Set node availability
  docker_node:
    state: update
    name: mynode
    availability: drain
'''

RETURN = '''
node_facts:
  description: Information about node after 'update' operation
  returned: success
  type: dict
nodes:
  description: List nodes names of swarm cluster.
  returned: success
  type: list
  example: "[ 'node-1', 'node-2', 'node-3']"
actions:
  description: Provides the actions done on the swarm.
  returned: when action failed.
  type: list
  example: "['This cluster is already a swarm cluster']"

'''

import json

try:
    from docker.errors import APIError
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils.docker_common import (
    AnsibleDockerClient,
    DockerBaseClass,
)

from ansible.module_utils._text import to_native


class TaskParameters(DockerBaseClass):
    def __init__(self, client):
        super(TaskParameters, self).__init__()

        self.state = None

        # Spec
        self.name = None
        self.labels = None

        # Node
        self.availability = None
        self.role = None

        for key, value in client.module.params.items():
            setattr(self, key, value)


class SwarmNodeManager(DockerBaseClass):

    def __init__(self, client, results):

        super(SwarmNodeManager, self).__init__()

        self.client = client
        self.results = results
        self.check_mode = self.client.check_mode

        self.parameters = TaskParameters(client)

    def __call__(self):
        choice_map = {
            "list": self.node_list,
            "update": self.node_update,
        }

        choice_map.get(self.parameters.state)()

    def __isSwarmManager(self):
        try:
            data = self.client.inspect_swarm()
            json_str = json.dumps(data, ensure_ascii=False)
            self.swarm_info = json.loads(json_str)
            return True
        except APIError:
            return False

    def __isSwarmNode(self):
        info = self.client.info()
        self.results['__isSwarmNode'] = info
        if info:
            json_str = json.dumps(info, ensure_ascii=False)
            self.swarm_info = json.loads(json_str)
            if self.swarm_info['Swarm']['NodeID']:
                return True
        return False

    def __isSwarmNodeByID(self, node_id=None):
        if node_id is None:
            return self.__isSwarmNode()

        try:
            node_info = self.__get_node_info()
        except APIError:
            return

        if node_info['ID'] is not None:
            return True
        return False

    def __isSwarmNodeDown(self):
        node_info = self.__get_node_info()
        if node_info['Status']['State'] == 'down':
            return True
        return False

    def __get_node_info(self):
        try:
            node_info = self.client.inspect_node(node_id=self.parameters.name)
        except APIError as exc:
            raise exc
        json_str = json.dumps(node_info, ensure_ascii=False)
        node_info = json.loads(json_str)
        return node_info

    def node_update(self):
        if not(self.__isSwarmManager()):
            self.client.fail(msg="This node is not a manager.")

        if not(self.__isSwarmNodeByID(node_id=self.parameters.name)):
            self.results['actions'].append("This node is not part of a swarm.")
            return

        try:
            status_down = self.__isSwarmNodeDown()
        except APIError:
            return

        if status_down:
            self.client.fail(msg="Can not update the node. The status node is down.")

        try:
            node_info = self.client.inspect_node(node_id=self.parameters.name)
        except APIError as exc:
            self.client.fail(msg="Failed to get node information for %s" % to_native(exc))

        if self.parameters.role is None:
            self.parameters.role = node_info['Spec']['Role']

        if self.parameters.availability is None:
            self.parameters.availability = node_info['Spec']['Availability']

        node_spec = dict(
            Availability=self.parameters.availability,
            Role=self.parameters.role,
        )

        try:
            self.client.update_node(node_id=node_info['ID'], version=node_info['Version']['Index'], node_spec=node_spec)
        except APIError as exc:
            self.client.fail(msg="Failed to update node : %s" % to_native(exc))

        self.results['node_facts'] = self.__get_node_info()
        self.results['actions'].append("Node updated")
        self.results['changed'] = True

    def node_list(self):
        if not(self.__isSwarmManager()):
            self.client.fail(msg="This node is not a manager.")

        try:
            nodes = self.client.nodes()
        except APIError as exc:
            self.client.fail(msg="Failed to get nodes list : %s" % to_native(exc))

        swarm_nodes = []

        for node in nodes:
            swarm_nodes.append(node['Description']['Hostname'])

        self.results['nodes'] = swarm_nodes
        self.results['changed'] = False


def main():
    argument_spec = dict(
        state=dict(type='str', choices=['list', 'update'], default='list'),
        force=dict(type='bool', default=False),
        name=dict(type='str'),
        labels=dict(type='dict'),
        availability=dict(type='str', choices=['active', 'pause', 'drain']),
        role=dict(type='str', choices=['worker', 'manager']),
    )

    required_if = [
        ('state', 'update', ['name']),
    ]

    option_minimal_versions = dict(
        signing_ca_cert=dict(docker_api_version='1.30'),
        signing_ca_key=dict(docker_api_version='1.30'),
        ca_force_rotate=dict(docker_api_version='1.30'),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        min_docker_version='2.6.0',
        min_docker_api_version='1.25',
        option_minimal_versions=option_minimal_versions,
    )

    results = dict(
        changed=False,
        result='',
        actions=[],
    )

    SwarmNodeManager(client, results)()
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
