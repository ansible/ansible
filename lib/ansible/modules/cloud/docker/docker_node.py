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
        type: str
        required: yes
    labels:
        description:
            - User-defined key/value metadata that will be assigned as node attribute.
            - Label operations in this module apply to the docker swarm node specified by I(hostname).
              Use M(docker_swarm) module to add/modify/remove swarm cluster labels.
            - The actual state of labels assigned to the node when module completes its work depends on
              I(labels_state) and I(labels_to_remove) parameters values. See description below.
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
        type: str
        default: 'merge'
        choices:
          - merge
          - replace
    labels_to_remove:
        description:
            - List of labels that will be removed from the node configuration. The list has to contain only label
              names, not their values.
            - If the label provided on the list is not assigned to the node, the entry is ignored.
            - If the label is both on the I(labels_to_remove) and I(labels), then value provided in I(labels) remains
              assigned to the node.
            - If I(labels_state) is C(replace) and I(labels) is not provided or empty then all labels assigned to
              node are removed and I(labels_to_remove) is ignored.
        type: list
    availability:
        description: Node availability to assign. If not provided then node availability remains unchanged.
        choices:
          - active
          - pause
          - drain
        type: str
    role:
        description: Node role to assign. If not provided then node role remains unchanged.
        choices:
          - manager
          - worker
        type: str
extends_documentation_fragment:
  - docker
  - docker.docker_py_1_documentation
requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 2.4.0"
  - Docker API >= 1.25
author:
  - Piotr Wojciechowski (@WojciechowskiPiotr)
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

- name: Remove all labels assigned to node
  docker_node:
    hostname: mynode
    labels_state: replace

- name: Remove selected labels from the node
  docker_node:
    hostname: mynode
    labels_to_remove:
      - key1
      - key2
'''

RETURN = '''
node:
  description: Information about node after 'update' operation
  returned: success
  type: dict

'''

try:
    from docker.errors import APIError
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass

from ansible.module_utils.docker.common import (
    DockerBaseClass,
)

from ansible.module_utils._text import to_native

from ansible.module_utils.docker.swarm import AnsibleDockerSwarmClient


class TaskParameters(DockerBaseClass):
    def __init__(self, client):
        super(TaskParameters, self).__init__()

        # Spec
        self.name = None
        self.labels = None
        self.labels_state = None
        self.labels_to_remove = None

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
            self.client.fail("This node is not part of a swarm.")
            return

        if self.client.check_if_swarm_node_is_down():
            self.client.fail("Can not update the node. The node is down.")

        try:
            node_info = self.client.inspect_node(node_id=self.parameters.hostname)
        except APIError as exc:
            self.client.fail("Failed to get node information for %s" % to_native(exc))

        changed = False
        node_spec = dict(
            Availability=self.parameters.availability,
            Role=self.parameters.role,
            Labels=self.parameters.labels,
        )

        if self.parameters.role is None:
            node_spec['Role'] = node_info['Spec']['Role']
        else:
            if not node_info['Spec']['Role'] == self.parameters.role:
                node_spec['Role'] = self.parameters.role
                changed = True

        if self.parameters.availability is None:
            node_spec['Availability'] = node_info['Spec']['Availability']
        else:
            if not node_info['Spec']['Availability'] == self.parameters.availability:
                node_info['Spec']['Availability'] = self.parameters.availability
                changed = True

        if self.parameters.labels_state == 'replace':
            if self.parameters.labels is None:
                node_spec['Labels'] = {}
                if node_info['Spec']['Labels']:
                    changed = True
            else:
                if (node_info['Spec']['Labels'] or {}) != self.parameters.labels:
                    node_spec['Labels'] = self.parameters.labels
                    changed = True
        elif self.parameters.labels_state == 'merge':
            node_spec['Labels'] = dict(node_info['Spec']['Labels'] or {})
            if self.parameters.labels is not None:
                for key, value in self.parameters.labels.items():
                    if node_spec['Labels'].get(key) != value:
                        node_spec['Labels'][key] = value
                        changed = True

            if self.parameters.labels_to_remove is not None:
                for key in self.parameters.labels_to_remove:
                    if self.parameters.labels is not None:
                        if not self.parameters.labels.get(key):
                            if node_spec['Labels'].get(key):
                                node_spec['Labels'].pop(key)
                                changed = True
                        else:
                            self.client.module.warn(
                                "Label '%s' listed both in 'labels' and 'labels_to_remove'. "
                                "Keeping the assigned label value."
                                % to_native(key))
                    else:
                        if node_spec['Labels'].get(key):
                            node_spec['Labels'].pop(key)
                            changed = True

        if changed is True:
            if not self.check_mode:
                try:
                    self.client.update_node(node_id=node_info['ID'], version=node_info['Version']['Index'],
                                            node_spec=node_spec)
                except APIError as exc:
                    self.client.fail("Failed to update node : %s" % to_native(exc))
            self.results['node'] = self.client.get_node_inspect(node_id=node_info['ID'])
            self.results['changed'] = changed
        else:
            self.results['node'] = node_info
            self.results['changed'] = changed


def main():
    argument_spec = dict(
        hostname=dict(type='str', required=True),
        labels=dict(type='dict'),
        labels_state=dict(type='str', default='merge', choices=['merge', 'replace']),
        labels_to_remove=dict(type='list', elements='str'),
        availability=dict(type='str', choices=['active', 'pause', 'drain']),
        role=dict(type='str', choices=['worker', 'manager']),
    )

    client = AnsibleDockerSwarmClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='2.4.0',
        min_docker_api_version='1.25',
    )

    results = dict(
        changed=False,
    )

    SwarmNodeManager(client, results)
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
