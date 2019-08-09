#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_routers_info
short_description: Retrieve state about one or more OpenStack routerss.
version_added: "2.9"
author: "Julien Girardin (@Zempashi)"
description:
    - Retrieve state about one or more routers from OpenStack.
requirements:
    - "python >= 2.7"
    - "sdk"
options:
   name:
     description:
        - Name or ID of the Router
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
- name: Gather state about previously created routers
  os_routers_info:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
  register: openstack_routers

- name: Show openstack networks
  debug:
    var: openstack_routers

- name: Gather state about a previously created router by name
  os_router_infos:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    name:  router1
  register: openstack_routers

- name: Show openstack networks
  debug:
    var: openstack_routers
'''

RETURN = '''
openstack_routers:
    description: has all the openstack data about the routers
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
        routes:
            description: >-
               Additional route(s) handled by the router.
               Don't list default route, neither implicit routes for subnet
            returned: success
            type: list of dicts
        tenant_id:
            description: Tenant id associated with this router.
            returned: success
            type: str
        external_gateway_info:
            description: Information about external gateway.
            returned: success
            type: dict
        interfaces:
            description: Informatrion about internal interfaces
            returned: success
            type: list of dicts
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None),
        filters=dict(required=False, type='dict', default=None)
    )
    module = AnsibleModule(argument_spec, supports_check_mode=True)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        routers = cloud.search_routers(module.params['name'],
                                       module.params['filters'])
        for router in routers:
            router['interfaces'] = cloud.list_router_interfaces(router, 'internal')
        module.exit_json(changed=False, openstack_routers=routers)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
