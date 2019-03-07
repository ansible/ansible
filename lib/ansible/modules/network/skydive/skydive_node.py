#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: skydive_node
version_added: "2.8"
author:
  - "Sumit Jaiswal (@sjaiswal)"
short_description: Module which add nodes to Skydive topology
description:
  - This module handles adding node to the Skydive topology.
requirements:
  - skydive-client
extends_documentation_fragment: skydive
options:
  name:
    description:
      - To define name for the node.
    required: true
  node_type:
    description:
      - To define type for the node.
    required: true
  host:
    description:
      - To define host for the node.
    required: false
  seed:
    description:
      - used to generate the UUID of the node
    default: ""
  metadata:
    description:
      - To define metadata for the node.
    required: false
  state:
    description:
      - State of the Skydive Node. If value is I(present) new node
        will be created else if it is I(absent) it will be deleted.
    default: present
    choices:
      - present
      - update
      - absent
"""

EXAMPLES = """
- name: create tor node
  skydive_node:
    name: TOR
    node_type: fabric
    seed: TOR1
    metadata:
      Model: Cisco 5300
    state: present
    provider:
      endpoint: localhost:8082
      username: admin
      password: admin

- name: update tor node
  skydive_node:
    name: TOR
    node_type: host
    seed: TOR1
    metadata:
      Model: Cisco 3400
    state: update
    provider:
      endpoint: localhost:8082
      username: admin
      password: admin

- name: Delete the tor node
  skydive_node:
    name: TOR
    node_type: host
    seed: TOR1
    metadata:
      Model: Cisco 3400
    state: absent
    provider:
      endpoint: localhost:8082
      username: admin
      password: admin
"""

RETURN = """ # """

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.skydive.api import skydive_node


def main():
    ''' Main entry point for module execution
    '''
    ib_spec = dict(
        name=dict(required=True, ib_req=True),
        node_type=dict(required=True, ib_req=True),
        host=dict(required=False, ib_req=True, default=""),
        seed=dict(required=False, ib_req=True, default=""),
        metadata=dict(required=False, ib_req=True, default=dict())
    )

    argument_spec = dict(
        provider=dict(required=False),
        state=dict(default='present', choices=['present', 'update', 'absent'])
    )

    argument_spec.update(ib_spec)
    argument_spec.update(skydive_node.provider_spec)
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    skydive_obj = skydive_node(module)
    result = skydive_obj.run()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
