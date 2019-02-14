#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_subnets_facts
short_description: Retrieve facts about one or more OpenStack subnets.
version_added: "2.0"
author: "Davide Agnello (@dagnello)"
description:
    - Retrieve facts about one or more subnets from OpenStack.
requirements:
    - "python >= 2.7"
    - "openstacksdk"
options:
   name:
     description:
        - Name or ID of the subnet.
        - Alias 'subnet' added in version 2.8.
     required: false
     aliases: ['subnet']
   filters:
     description:
        - A dictionary of meta data to use for further filtering.  Elements of
          this dictionary may be additional dictionaries.
     required: false
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
- name: Gather facts about previously created subnets
  os_subnets_facts:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject

- name: Show openstack subnets
  debug:
    var: openstack_subnets

- name: Gather facts about a previously created subnet by name
  os_subnets_facts:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    name: subnet1

- name: Show openstack subnets
  debug:
    var: openstack_subnets

- name: Gather facts about a previously created subnet with filter
  # Note: name and filters parameters are not mutually exclusive
  os_subnets_facts:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    filters:
      tenant_id: 55e2ce24b2a245b09f181bf025724cbe

- name: Show openstack subnets
  debug:
    var: openstack_subnets
'''

RETURN = '''
openstack_subnets:
    description: has all the openstack facts about the subnets
    returned: always, but can be null
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: str
        name:
            description: Name given to the subnet.
            returned: success
            type: str
        network_id:
            description: Network ID this subnet belongs in.
            returned: success
            type: str
        cidr:
            description: Subnet's CIDR.
            returned: success
            type: str
        gateway_ip:
            description: Subnet's gateway ip.
            returned: success
            type: str
        enable_dhcp:
            description: DHCP enable flag for this subnet.
            returned: success
            type: bool
        ip_version:
            description: IP version for this subnet.
            returned: success
            type: int
        tenant_id:
            description: Tenant id associated with this subnet.
            returned: success
            type: str
        dns_nameservers:
            description: DNS name servers for this subnet.
            returned: success
            type: list of strings
        allocation_pools:
            description: Allocation pools associated with this subnet.
            returned: success
            type: list of dicts
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None, aliases=['subnet']),
        filters=dict(required=False, type='dict', default=None)
    )
    module = AnsibleModule(argument_spec)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        subnets = cloud.search_subnets(module.params['name'],
                                       module.params['filters'])
        module.exit_json(changed=False, ansible_facts=dict(
            openstack_subnets=subnets))

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
