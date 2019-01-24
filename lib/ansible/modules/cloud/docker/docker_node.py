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
    - Manages the Docker nodes via Swarm Manager.
    - This module allows to change the node's role, its availability, and to modify, add or remove node labels.
options:
    hostname:
        description:
            - The hostname or ID of node as registered in Swarm.
            - If more than one node is registered using the same hostname the ID must be used,
              otherwise module will fail.
        required: true
        type: str
    labels:
        description: User-defined key/value metadata. If not provided then labels assigned to node remains unchanged.
        type: dict
    labels_state:
        description:
            - It defines the operation on the labels assigned to node and labels specified in I(labels) option.
            - Set to C(merge) to combine labels provided in I(labels) with those already assigned to the node.
              If no labels are assigned then it will add listed labels. For labels that are already assigned
              to the node, it will update their values. The labels not specified in I(labels) will remain unchanged. 
              If I(labels) is empty then no changes will be made.
            - Set to C(replace) to replace all assigned labels with provided ones. If I(labels) is empty then
              all labels assigned to the node will be removed.
        choices:
          - merge
          - replace
        default: 'merge'
        required: false
        type: str
    labels_to_remove:
        description:
            - List of labels that will be removed from the node configuration. If label specified on the list is 
              not assigned to the node then no action will be performed. The remaining labels assigned to the
              node remains unchanged. The list have to contain only label names, not their values.
        required: false
        type: list
    availability:
        description: Node availability to assign. If not provided then node availability remains unchanged.
        choices:
          - active
          - pause
          - drain
        required: false
        type: str
    role:
        description: Node role to assign. If not provided then node role remains unchanged.
        choices:
          - manager
          - worker
        required: false
        type: str
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
    - Docker API >= 1.25
author:
  - Piotr Wojciechowski (@wojciechowskipiotr)
  - Thierry Bouvet (@tbouvet)

'''

EXAMPLES = '''
- name: Set node role
  docker_node:
    hostname: mynode
    role: manager

- name: Set node availability
  docker_node:
    hostname: mynode
    availability: drain

- name: Replace node labels with new labels
  docker_node:
    hostname: mynode
    labels:
      key: value
    labels_state: replace

- name: Merge node labels and new labels
  docker_node:
    hostname: mynode
    labels:
      key: value

- name: Merge node labels and new labels
  docker_node:
    hostname: mynode
    labels:
      key: value
    labels_state: merge

- name: Remove all labels assigned to node
  docker_node:
    hostname: mynode
    labels:
    labels_state: replace

- name: Remove node labels
  docker_node:
    hostname: mynode
    labels_state: remove
'''

RETURN = '''
node_facts:
  description: Information about node after 'update' operation
  returned: success
  type: dict

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

        self.client.fail_task_if_not_swarm_manager()

        self.parameters = TaskParameters(client)

        self.node_update()

    def node_update(self):
        if not (self.client.check_if_swarm_node(node_id=self.parameters.hostname)):
            self.client.fail(msg="This node is not part of a swarm.")
            return

        if self.client.check_if_swarm_node_is_down():
            self.client.fail(msg="Can not update the node. The status node is down.")

        try:
            node_info = self.client.inspect_node(node_id=self.parameters.hostname)
        except APIError as exc:
            self.client.fail(msg="Failed to get node information for %s" % to_native(exc))

        changed = False
        node_spec = dict(
            Availability=self.parameters.availability,
            Role=self.parameters.role,
            Labels=self.parameters.labels,
        )

        if self.parameters.role is None:
            node_spec['Role'] = node_info['Spec']['Role']

        if self.parameters.availability is None:
            node_spec['Availability'] = node_info['Spec']['Availability']

        if self.parameters.labels_state == 'replace':
            node_spec['Labels'] = self.parameters.labels
            changed = True

        if self.parameters.labels_state == 'remove':
            node_spec['Labels'] = node_info['Spec']['Labels']

            if self.parameters.labels is None and not node_info['Spec']['Labels']:
                node_spec['Labels'] = None
                changed = True
            elif self.parameters.labels is not None and node_info['Spec']['Labels'] is not None:
                for key in self.parameters.labels:
                    if key in node_info['Spec']['Labels']:
                        node_spec['Labels'].pop(key)
                        changed = True

        if self.parameters.labels_state == 'merge':
            node_spec['Labels'] = node_info['Spec']['Labels']

            for next_key in self.parameters.labels:
                if next_key in node_info['Spec']['Labels']:
                    if self.parameters.labels.get(next_key) == node_info['Spec']['Labels'][next_key]:
                        pass
                    else:
                        node_spec['Labels'][next_key] = self.parameters.labels.get(next_key)
                        changed = True
                else:
                    node_spec['Labels'][next_key] = self.parameters.labels.get(next_key)
                    changed = True

        if changed is True:
            try:
                self.client.update_node(node_id=node_info['ID'], version=node_info['Version']['Index'],
                                        node_spec=node_spec)
            except APIError as exc:
                self.client.fail(msg="Failed to update node : %s" % to_native(exc))
            self.results['node_facts'] = self.client.get_node_inspect(node_id=node_info['ID'])
            self.results['changed'] = changed
        else:
            self.results['node_facts'] = node_info
            self.results['changed'] = changed


def main():
    argument_spec = dict(
        hostname=dict(type='str', required=True),
        labels=dict(type='dict'),
        labels_state=dict(type='str', choices=['merge', 'replace', 'remove'], default='merge'),
        labels_to_remove=dict(type='list', elements='str'),
        availability=dict(type='str', choices=['active', 'pause', 'drain']),
        role=dict(type='str', choices=['worker', 'manager']),
    )

    required_if = [
        ('labels_state', 'merge', ['hostname', 'labels']),
        ('labels_state', 'replace', ['hostname', 'labels']),
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
    )

    SwarmNodeManager(client, results)
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
