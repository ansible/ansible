#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2019, Bram Verschueren <verschueren.bram@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_routers_info
short_description: Retrieve information about one or more OpenStack routers.
version_added: "2.10"
author: "Bram Verschueren (@bverschueren)"
description:
    - Retrieve information about one or more routers from OpenStack.
requirements:
    - "python >= 2.7"
    - "openstacksdk"
options:
   name:
     description:
        - Name or ID of the router
     required: false
     type: str
   filters:
     description:
        - A dictionary of meta data to use for further filtering.  Elements of
          this dictionary may be additional dictionaries.
     required: false
     type: dict
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
     type: str
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
- name: Gather information about routers
  os_routers_info:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
  register: result

- name: Show openstack routers
  debug:
    msg: "{{ result.openstack_routers }}"

- name: Gather information about a router by name
  os_routers_info:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    name: router1
  register: result

- name: Show openstack routers
  debug:
    msg: "{{ result.openstack_routers }}"

- name: Gather information about a router with filter
  os_routers_info:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    filters:
      tenant_id: bc3ea709c96849d6b81f54640400a19f
  register: result

- name: Show openstack routers
  debug:
    msg: "{{ result.openstack_routers }}"
'''

RETURN = '''
openstack_routers:
    description: has all the openstack information about the routers
    returned: always, but can be null
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: str
        name:
            description: Name given to the router.
            returned: success
            type: str
        status:
            description: Router status.
            returned: success
            type: str
        external_gateway_info:
            description: The external gateway information of the router.
            returned: success
            type: dict
        interfaces_info:
            description: List of connected interfaces.
            returned: success
            type: list
        distributed:
            description: Indicates a distributed router.
            returned: success
            type: bool
        ha:
            description: Indicates a highly-available router.
            returned: success
            type: bool
        project_id:
            description: Project id associated with this router.
            returned: success
            type: str
        routes:
            description: The extra routes configuration for L3 router.
            returned: success
            type: list
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None),
        filters=dict(required=False, type='dict', default=None)
    )
    module = AnsibleModule(argument_spec)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        routers = cloud.search_routers(module.params['name'],
                                       module.params['filters'])
        for router in routers:
            interfaces_info = []
            for port in cloud.list_router_interfaces(router):
                if port.device_owner != "network:router_gateway":
                    for ip_spec in port.fixed_ips:
                        int_info = {
                            'port_id': port.id,
                            'ip_address': ip_spec.get('ip_address'),
                            'subnet_id': ip_spec.get('subnet_id')
                        }
                    interfaces_info.append(int_info)
            router['interfaces_info'] = interfaces_info

        module.exit_json(changed=False, openstack_routers=routers)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
