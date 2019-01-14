#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: skydive_add_node
version_added: "2.8"
author:
  - "Sumit Jaiswal (@sjaiswal)"
short_description: Module helps in adding nodes connected with a link
description:
  - Using this module user can subcribe to the graph event bus of
    Skydive being able to see all the modifications of the topology.
options:
  nodename:
    description:
      - node name with which new node need to be created.
    required: true
    aliases:
      - nodename
  hostname:
    description:
      - host name under which new node will be created
    required: true
    aliases:
      - hostname
  metadata:
    description:
      - Dictionary having Node name and flow type
    required: true
    aliases:
      - metadata
  state:
    description:
      - To configure Node and link new node.
    default: present
    choices:
      - present
      - absent
"""

EXAMPLES = """
- name: add a new new node with connected link
  skydive_add_node:
    nodename: Node1
    hostname: myhost
    metadata:
      name: The node 1
      type: device
    state: present
- name: remove node
  skydive_add_node:
    nodename: Node1
    hostname: myhost
    metadata:
      name: The node 1
      type: device
    state: absent
"""

RETURN = """ # """

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.skydive.skydive import skydive_graph_engine


def main():
    ''' Main entry point for module execution
    '''
    ib_spec = dict(
        nodename=dict(required=True, ib_req=True),
        hostname=dict(required=True, ib_req=True),
        metadata=dict(required=True, ib_req=True)
    )

    argument_spec = dict(
        provider=dict(required=True),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ib_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    skydive_obj = skydive_graph_engine()
    result = skydive_obj.run(ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
