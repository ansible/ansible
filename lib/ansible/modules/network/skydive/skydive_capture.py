#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Ansible by Red Hat, inc
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
  - It useful when you want to start a capture on all OpenvSwitch
    whatever the number of Skydive agents you will start.
  - While starting the capture, user can specify the capture name,
    capture description and capture type optionally.
requirements:
  - skydive-client
extends_documentation_fragment: skydive
options:
  name:
    description:
      - To define flow capture name
    required: true
  capture_type:
    description:
      - To define flow capture type
    required: false
  description:
    description:
      - Configures a text string to be associated with the instance
        of this object.
  extra_tcp_metric:
    description:
      - To define flow capture ExtraTCPMetric
    type: bool
    default: false
  ip_defrag:
    description:
      - To define flow capture IPDefrag
    type: bool
    default: false
  reassemble_tcp:
    description:
      - To define flow capture ReassembleTCP
    type: bool
    default: false
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
- name: add a new new node with connected link
  skydive_capture:
    name: Node1
    capture_type: myhost
    description: test description
    extra_tcp_metric: true
    ip_defrag: true
    reassemble_tcp: true
    state: present
- name: remove node
  skydive_capture:
    name: Node1
    capture_type: myhost
    extra_tcp_metric: true
    ip_defrag: true
    reassemble_tcp: true
    state: absent
"""

RETURN = """ # """

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.skydive.skydive import skydive_flow_topology


def main():
    ''' Main entry point for module execution
    '''
    ib_spec = dict(
        name=dict(required=True, ib_req=True),
        capture_type=dict(required=False, ib_req=True),
        description=dict(),
        extra_tcp_metric=dict(type='bool', required=False, ib_req=True, default=False),
        ip_defrag=dict(type='bool', required=False, ib_req=True, default=False),
        reassemble_tcp=dict(type='bool', required=False, ib_req=True, default=False)
    )

    argument_spec = dict(
        provider=dict(required=True),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ib_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    skydive_obj = skydive_flow_topology(module)
    result = skydive_obj.run(ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
