#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: intersight_info
short_description: Gather information about Intersight
description:
- Gathers information about servers in L(Cisco Intersight,https://intersight.com).
- This module was called C(intersight_facts) before Ansible 2.9. The usage did not change.
extends_documentation_fragment: intersight
options:
  server_names:
    description:
    - Server names to retrieve information from.
    - An empty list will return all servers.
    type: list
    required: yes
author:
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.8'
'''

EXAMPLES = r'''
- name: Get info for all servers
  intersight_info:
    api_private_key: ~/Downloads/SecretKey.txt
    api_key_id: 64612d300d0982/64612d300d0b00/64612d300d3650
    server_names:
- debug:
    msg: "server name {{ item.Name }}, moid {{ item.Moid }}"
  loop: "{{ intersight_servers }}"
  when: intersight_servers is defined

- name: Get info for servers by name
  intersight_info:
    api_private_key: ~/Downloads/SecretKey.txt
    api_key_id: 64612d300d0982/64612d300d0b00/64612d300d3650
    server_names:
      - SJC18-L14-UCS1-1
- debug:
    msg: "server moid {{ intersight_servers[0].Moid }}"
  when: intersight_servers[0] is defined
'''

RETURN = r'''
intersight_servers:
  description: A list of Intersight Servers.  See L(Cisco Intersight,https://intersight.com/apidocs) for details.
  returned: always
  type: complex
  contains:
    Name:
      description: The name of the server.
      returned: always
      type: str
      sample: SJC18-L14-UCS1-1
    Moid:
      description: The unique identifier of this Managed Object instance.
      returned: always
      type: str
      sample: 5978bea36ad4b000018d63dc
'''

from ansible.module_utils.remote_management.intersight import IntersightModule, intersight_argument_spec
from ansible.module_utils.basic import AnsibleModule


def get_servers(module, intersight):
    query_list = []
    if module.params['server_names']:
        for server in module.params['server_names']:
            query_list.append("Name eq '%s'" % server)
    query_str = ' or '.join(query_list)
    options = {
        'http_method': 'get',
        'resource_path': '/compute/PhysicalSummaries',
        'query_params': {
            '$filter': query_str,
            '$top': 5000
        }
    }
    response_dict = intersight.call_api(**options)

    return response_dict.get('Results')


def main():
    argument_spec = intersight_argument_spec
    argument_spec.update(
        server_names=dict(type='list', required=True),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )
    if module._name == 'intersight_facts':
        module.deprecate("The 'intersight_facts' module has been renamed to 'intersight_info'", version='2.13')

    intersight = IntersightModule(module)

    # one API call returning all requested servers
    module.exit_json(intersight_servers=get_servers(module, intersight))


if __name__ == '__main__':
    main()
