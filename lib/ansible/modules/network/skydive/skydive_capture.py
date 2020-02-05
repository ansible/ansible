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
module: skydive_capture
version_added: "2.8"
author:
  - "Sumit Jaiswal (@sjaiswal)"
short_description: Module which manages flow capture on interfaces
description:
  - This module manages flow capture on interfaces. The Gremlin
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
  query:
    description:
      - It's the complete gremlin query which the users can input,
        I(G.V().Has('Name', 'eth0', 'Type', 'device')), to create
        the capture. And, if the user directly inputs the gremlin
        query then user is not required to input any other module
        parameter as gremlin query takes care of creating the flow
        capture.
    required: false
  interface_name:
    description:
      - To define flow capture interface name.
    required: false
  type:
    description:
      - To define flow capture interface type.
    required: false
  capture_name:
    description:
      - To define flow capture name.
    required: false
    default: ""
  description:
    description:
      - Configures a text string to be associated with the instance
        of this object.
    default: ""
  extra_tcp_metric:
    description:
      - To define flow capture ExtraTCPMetric.
    type: bool
    default: false
  ip_defrag:
    description:
      - To define flow capture IPDefrag.
    type: bool
    default: false
  reassemble_tcp:
    description:
      - To define flow capture ReassembleTCP.
    type: bool
    default: false
  layer_key_mode:
    description:
      - To define flow capture Layer KeyMode.
    type: str
    default: L2
  state:
    description:
      - State of the flow capture. If value is I(present) flow capture
        will be created else if it is I(absent) it will be deleted.
    default: present
    choices:
      - present
      - absent
"""

EXAMPLES = """
- name: start a new flow capture directly from gremlin query
  skydive_capture:
    query: G.V().Has('Name', 'eth0', 'Type', 'device')
    state: present
    provider:
      endpoint: localhost:8082
      username: admin
      password: admin

- name: stop the flow capture directly from gremlin query
  skydive_capture:
    query: G.V().Has('Name', 'eth0', 'Type', 'device')
    state: absent
    provider:
      endpoint: localhost:8082
      username: admin
      password: admin

- name: start a new flow capture from user's input
  skydive_capture:
    interface_name: Node1
    type: myhost
    capture_name: test_capture
    description: test description
    extra_tcp_metric: true
    ip_defrag: true
    reassemble_tcp: true
    state: present
    provider:
      endpoint: localhost:8082
      username: admin
      password: admin

- name: stop the flow capture
  skydive_capture:
    interface_name: Node1
    type: myhost
    capture_name: test_capture
    description: test description
    extra_tcp_metric: true
    ip_defrag: true
    reassemble_tcp: true
    state: absent
    provider:
      endpoint: localhost:8082
      username: admin
      password: admin
"""

RETURN = """ # """

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.skydive.api import skydive_flow_capture


def main():
    ''' Main entry point for module execution
    '''
    ib_spec = dict(
        query=dict(required=False, ib_req=True),
        interface_name=dict(required=False, ib_req=True),
        type=dict(required=False, ib_req=True),
        capture_name=dict(required=False, default='', ib_req=True),
        description=dict(default='', ib_req=True),
        extra_tcp_metric=dict(type='bool', required=False, ib_req=True, default=False),
        ip_defrag=dict(type='bool', required=False, ib_req=True, default=False),
        reassemble_tcp=dict(type='bool', required=False, ib_req=True, default=False),
        layer_key_mode=dict(required=False, ib_req=True, default='L2')
    )

    argument_spec = dict(
        provider=dict(required=False),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ib_spec)
    argument_spec.update(skydive_flow_capture.provider_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    skydive_obj = skydive_flow_capture(module)
    result = skydive_obj.run(ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
