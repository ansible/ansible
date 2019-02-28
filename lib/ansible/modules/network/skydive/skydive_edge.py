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
module: skydive_edge
version_added: "2.8"
author:
  - "Sumit Jaiswal (@sjaiswal)"
short_description: Module to add edges to Skydive topology
description:
  - This module handles adding node to the Skydive topology. The Gremlin
    expression is continuously evaluated which means that it is
    possible to define a capture on nodes that do not exist yet.
  - It is useful when you want to start a capture on all OpenvSwitch
    whatever the number of Skydive agents you will start.
  - While starting the capture, user can specify the capture name,
    capture description and capture type optionally.
requirements:
  - skydive-client
extends_documentation_fragment: skydive
options:
  name:
    description:
      - To define name for the node.
    required: true
  relation_type:
    description:
      - To define relation type of the node I(ownership, layer2, layer3).
    required: true
  node1:
    description:
      - To defined the first node of the link, it can be either an ID or
        a gremlin expression
    required: true
  node2:
    description:
      - To defined the second node of the link, it can be either an ID or
        a gremlin expression
    required: true
  host:
    description:
      - To define the host for the node.
    required: false
  state:
    description:
      - State of the Skydive Node. If value is I(present) new node
        will be created else if it is I(absent) it will be deleted.
    default: present
    choices:
      - present
      - absent
"""

EXAMPLES = """
- name: create tor
  skydive_node:
    name: 'TOR'
    type: "fabric"
    metadata:
      Model: Cisco xxxx
  register: tor_result

- name: create port 1
  skydive_node:
    name: 'PORT1'
    type: 'fabric'
  register: port1_result

- name: create port 2
  skydive_node:
    name: 'PORT2'
    type: 'fabric'
  register: port2_result

- name: link node tor and port 1
  skydive_edge:
    parent_node: "{{ tor_result.UUID }}"
    child_node: "{{ port1_result.UUID }}"
    relation_type: ownership
    state: present

- name: link tor and port 2
  skydive_edge:
    parent_node: "{{ tor_result.UUID }}"
    child_node: "{{ port2_result.UUID }}"
    relation_type: ownership
    state: present

- name: update link node tor and eth0
  skydive_edge:
    parent_node: "{{ port1_result.UUID }}"
    child_node: G.V().Has('Name', 'tun0')
    relation_type: layer2
    state: upadte

- name: Unlink tor and port 2
  skydive_edge:
    parent_node: "{{ tor_result.UUID }}"
    child_node: "{{ port2_result.UUID }}"
    relation_type: ownership
    state: absent
"""

RETURN = """ # """

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.skydive.api import skydive_edge


def main():
    ''' Main entry point for module execution
    '''
    ib_spec = dict(
        relation_type=dict(type='str', required=True),
        parent_node=dict(type='str', required=True),
        child_node=dict(type='str', required=True),
        host=dict(type='str', default=""),
        metadata=dict(type='dict', default=dict())
    )

    argument_spec = dict(
        provider=dict(required=False),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ib_spec)
    argument_spec.update(skydive_edge.provider_spec)
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    skydive_obj = skydive_edge(module)
    result = skydive_obj.run()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
