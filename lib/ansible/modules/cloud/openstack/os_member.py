#!/usr/bin/python

# Copyright (c) 2018 Catalyst Cloud Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: os_member
short_description: Add/Delete a member for a pool in load balancer from OpenStack Cloud
extends_documentation_fragment: openstack
version_added: "2.7"
author: "Lingxian Kong (@lingxiankong)"
description:
   - Add or Remove a member for a pool from the OpenStack load-balancer service.
options:
   name:
     description:
        - Name that has to be given to the member
     required: true
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   pool:
     description:
        - The name or id of the pool that this member belongs to.
     required: true
   protocol_port:
     description:
        - The protocol port number for the member.
     default: 80
   address:
     description:
        - The IP address of the member.
   subnet_id:
     description:
        - The subnet ID the member service is accessible from.
   wait:
     description:
        - If the module should wait for the load balancer to be ACTIVE.
     type: bool
     default: 'yes'
   timeout:
     description:
        - The amount of time the module should wait for the load balancer to get
          into ACTIVE state.
     default: 180
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
requirements: ["openstacksdk"]
'''

RETURN = '''
id:
    description: The member UUID.
    returned: On success when I(state) is 'present'
    type: str
    sample: "39007a7e-ee4f-4d13-8283-b4da2e037c69"
member:
    description: Dictionary describing the member.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: Unique UUID.
            type: str
            sample: "39007a7e-ee4f-4d13-8283-b4da2e037c69"
        name:
            description: Name given to the member.
            type: str
            sample: "test"
        description:
            description: The member description.
            type: str
            sample: "description"
        provisioning_status:
            description: The provisioning status of the member.
            type: str
            sample: "ACTIVE"
        operating_status:
            description: The operating status of the member.
            type: str
            sample: "ONLINE"
        is_admin_state_up:
            description: The administrative state of the member.
            type: bool
            sample: true
        protocol_port:
            description: The protocol port number for the member.
            type: int
            sample: 80
        subnet_id:
            description: The subnet ID the member service is accessible from.
            type: str
            sample: "489247fa-9c25-11e8-9679-00224d6b7bc1"
        address:
            description: The IP address of the backend member server.
            type: str
            sample: "192.168.2.10"
'''

EXAMPLES = '''
# Create a member, wait for the member to be created.
- os_member:
    cloud: mycloud
    endpoint_type: admin
    state: present
    name: test-member
    pool: test-pool
    address: 192.168.10.3
    protocol_port: 8080

# Delete a listener
- os_member:
    cloud: mycloud
    endpoint_type: admin
    state: absent
    name: test-member
    pool: test-pool
'''

import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, \
    openstack_module_kwargs, openstack_cloud_from_module


def _wait_for_member_status(module, cloud, pool_id, member_id, status,
                            failures, interval=5):
    timeout = module.params['timeout']

    total_sleep = 0
    if failures is None:
        failures = []

    while total_sleep < timeout:
        member = cloud.load_balancer.get_member(member_id, pool_id)
        provisioning_status = member.provisioning_status
        if provisioning_status == status:
            return member
        if provisioning_status in failures:
            module.fail_json(
                msg="Member %s transitioned to failure state %s" %
                    (member_id, provisioning_status)
            )

        time.sleep(interval)
        total_sleep += interval

    module.fail_json(
        msg="Timeout waiting for member %s to transition to %s" %
            (member_id, status)
    )


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
        pool=dict(required=True),
        address=dict(default=None),
        protocol_port=dict(default=80, type='int'),
        subnet_id=dict(default=None),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)
    sdk, cloud = openstack_cloud_from_module(module)
    name = module.params['name']
    pool = module.params['pool']

    try:
        changed = False

        pool_ret = cloud.load_balancer.find_pool(name_or_id=pool)
        if not pool_ret:
            module.fail_json(msg='pool %s is not found' % pool)

        pool_id = pool_ret.id
        member = cloud.load_balancer.find_member(name, pool_id)

        if module.params['state'] == 'present':
            if not member:
                member = cloud.load_balancer.create_member(
                    pool_ret,
                    address=module.params['address'],
                    name=name,
                    protocol_port=module.params['protocol_port'],
                    subnet_id=module.params['subnet_id']
                )
                changed = True

                if not module.params['wait']:
                    module.exit_json(changed=changed,
                                     member=member.to_dict(),
                                     id=member.id)

            if module.params['wait']:
                member = _wait_for_member_status(module, cloud, pool_id,
                                                 member.id, "ACTIVE",
                                                 ["ERROR"])

            module.exit_json(changed=changed, member=member.to_dict(),
                             id=member.id)

        elif module.params['state'] == 'absent':
            if member:
                cloud.load_balancer.delete_member(member, pool_ret)
                changed = True

            module.exit_json(changed=changed)
    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == "__main__":
    main()
