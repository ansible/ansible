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
    - Change or remove node labels
options:
    state:
        description:
            - Set to C(update) to update node labels, availability and role
        required: true
        choices:
          - update
    name:
        description:
            - Swarm name of the node.
            - Used with I(state=update).
    labels:
        description: User-defined key/value metadata.
    labels_state:
        description:
            - Defines the operation on the lables assigned to node.
            - Set to C(merge) to merge provided labels with already assigned ones. It will update existing keys.
              The I(labels) must be specified.
            - Set to C(replace) to replace assigned labels with provided ones. The I(labels) must be specified.
            - Set to C(remove) to remove all labels assigned to node.
        choices:
          - merge
          - replace
          - remove
        default: 'merge'
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
    - "The docker server >= 1.10.0"
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

- name: Replace node labels with new labels
  docker_node:
    state: update
    name: mynode
    labels:
      key: value
    labels_state: replace

- name: Merge node labels and new labels
  docker_node:
    state: update
    name: mynode
    labels:
      key: value

- name: Merge node labels and new labels
  docker_node:
    state: update
    name: mynode
    labels:
      key: value
    labels_state: merge

- name: Remove node labels
  docker_node:
    state: update
    name: mynode
    labels_state: remove
'''

RETURN = '''
node_facts:
  description: Information about node after 'update' operation
  returned: success
  type: dict
actions:
  description: Provides the actions done on the swarm.
  returned: when action failed.
  type: list
  example: "['This cluster is already a swarm cluster']"

'''

try:
    from docker.errors import APIError
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils.docker_common import (
    DockerBaseClass,
)

from ansible.module_utils._text import to_native

from ansible.module_utils.docker_swarm import AnsibleDockerSwarmClient


class TaskParameters(DockerBaseClass):
    def __init__(self, client):
        super(TaskParameters, self).__init__()

        self.state = None

        # Spec
        self.name = None
        self.labels = None
        self.labels_state = None

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
            "update": self.node_update,
        }

        choice_map.get(self.parameters.state)()

    def node_update(self):
        if not (self.client.check_if_swarm_manager()):
            self.client.fail(msg="This node is not a manager.")

        if not (self.client.check_if_swarm_node(node_id=self.parameters.name)):
            self.results['actions'].append("This node is not part of a swarm.")
            return

        try:
            status_down = self.client.check_if_swarm_node_is_down()
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

        if self.parameters.labels is None:
            self.parameters.labels = node_info['Spec']['Labels']
        else:
            if self.parameters.labels_state == 'remove':
                self.parameters.labels = {}
            if self.parameters.labels_state == 'replace':
                pass
            if self.parameters.labels_state == 'merge':
                for next_key in node_info['Spec']['Labels']:
                    if next_key not in self.parameters.labels:
                        self.parameters.labels.update({next_key: node_info['Spec']['Labels'][next_key]})

        node_spec = dict(
            Availability=self.parameters.availability,
            Role=self.parameters.role,
            Labels=self.parameters.labels,
        )

        try:
            self.client.update_node(node_id=node_info['ID'], version=node_info['Version']['Index'],
                                    node_spec=node_spec)
        except APIError as exc:
            self.client.fail(msg="Failed to update node : %s" % to_native(exc))
        self.results['node_facts'] = self.client.get_node_inspect(node_id=node_info['ID'])
        self.results['actions'].append("Node updated")
        self.results['changed'] = True


def main():
    argument_spec = dict(
        state=dict(type='str', choices=['update'], required=True),
        name=dict(type='str'),
        labels=dict(type='dict'),
        labels_state=dict(type='str', choices=['merge', 'replace', 'remove'], default='merge'),
        availability=dict(type='str', choices=['active', 'pause', 'drain']),
        role=dict(type='str', choices=['worker', 'manager']),
    )

    required_if = [
        ('state', 'update', ['name']),
        ('labels_state', 'merge', ['name', 'labels']),
        ('labels_state', 'replace', ['name', 'labels']),
    ]

    option_minimal_versions = dict(
        signing_ca_cert=dict(docker_api_version='1.30'),
        signing_ca_key=dict(docker_api_version='1.30'),
        ca_force_rotate=dict(docker_api_version='1.30'),
    )

    client = AnsibleDockerSwarmClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        min_docker_version='1.10.0',
        min_docker_api_version='1.24',
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
