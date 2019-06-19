#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage CheckPoint Firewall (c) 2019
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: cp_get_facts
short_description: Retrieve and Show existing objects on Checkpoint over Web Services API
description:
  - Checkpoint facts module to handle all available api's show tasks. All operations are performed over Web
    Services API.
version_added: "2.9"
author: "Sumit Jaiswal (@justjais)"
options:
  command:
    description:
      - Actual command to send to the remote checkpoint device over the
        configured provider. The resulting output from the command
        is returned based on the list of filters if provided. Note, the
        show command should be exactly same as used in Checkpoint APIs.
    type: str
    required: true
  filters:
    description:
      - List of filter conditions to evaluate against the output of the
        command. Note, the filter key should be exactly the same used
        in checkpoint APIs.
    type: list
"""

EXAMPLES = """
- name: Show Hosts
  cp_get_facts:
    command: show-hosts

- name: Show Network
  cp_get_facts:
    command: show-network
    filters:
    - uid: a0bbbc99-adef-4ef8-bb6d-defdefdefdef

- name: Show Access rule
  cp_get_facts:
    command : show-access-rule
    filters:
    - uid: 41e821a0-3720-11e3-aa6e-0800200c9fde

- name: Show Access selection
  cp_get_facts:
    command : show-access-section
    filters:
    - name: test_access
      layer: layer 2

- name: Show Nat rule
  cp_get_facts:
    command : show-nat-rule
    filters:
    - rule-number: test_rule_number
      package: test_package
"""

RETURN = """
cp_get_facts:
  description: The checkpoint command object facts.
  eturned: always.
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import show_api_call


def expand_api_object_n_payload(module):
    api_object = module.params.get('command')
    payload = dict()
    for each in module.params.get('filters'):
        payload.update(each)
    return api_object, payload


def main():

    argument_spec = dict(
        command=dict(type='str', required=True),
        filters=dict(type='list')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    api_call_object, payload = expand_api_object_n_payload(module)
    if payload:
        module.params['filters'] = payload

    result = show_api_call(module, api_call_object)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
