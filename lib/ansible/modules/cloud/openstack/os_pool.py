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
module: os_pool
short_description: Add/Delete a pool in the load balancing service from OpenStack Cloud
extends_documentation_fragment: openstack
version_added: "2.7"
author: "Lingxian Kong (@lingxiankong)"
description:
   - Add or Remove a pool from the OpenStack load-balancer service.
options:
   name:
     description:
        - Name that has to be given to the pool
     required: true
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   loadbalancer:
     description:
        - The name or id of the load balancer that this pool belongs to.
          Either loadbalancer or listener must be specified for pool creation.
   listener:
     description:
        - The name or id of the listener that this pool belongs to.
          Either loadbalancer or listener must be specified for pool creation.
   protocol:
     description:
        - The protocol for the pool.
     choices: [HTTP, HTTPS, PROXY, TCP, UDP]
     default: HTTP
   lb_algorithm:
     description:
        - The load balancing algorithm for the pool.
     choices: [LEAST_CONNECTIONS, ROUND_ROBIN, SOURCE_IP]
     default: ROUND_ROBIN
   wait:
     description:
        - If the module should wait for the pool to be ACTIVE.
     type: bool
     default: 'yes'
   timeout:
     description:
        - The amount of time the module should wait for the pool to get
          into ACTIVE state.
     default: 180
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
requirements: ["openstacksdk"]
'''

RETURN = '''
id:
    description: The pool UUID.
    returned: On success when I(state) is 'present'
    type: str
    sample: "39007a7e-ee4f-4d13-8283-b4da2e037c69"
listener:
    description: Dictionary describing the pool.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: Unique UUID.
            type: str
            sample: "39007a7e-ee4f-4d13-8283-b4da2e037c69"
        name:
            description: Name given to the pool.
            type: str
            sample: "test"
        description:
            description: The pool description.
            type: str
            sample: "description"
        loadbalancers:
            description: A list of load balancer IDs.
            type: list
            sample: [{"id": "b32eef7e-d2a6-4ea4-a301-60a873f89b3b"}]
        listeners:
            description: A list of listener IDs.
            type: list
            sample: [{"id": "b32eef7e-d2a6-4ea4-a301-60a873f89b3b"}]
        members:
            description: A list of member IDs.
            type: list
            sample: [{"id": "b32eef7e-d2a6-4ea4-a301-60a873f89b3b"}]
        loadbalancer_id:
            description: The load balancer ID the pool belongs to. This field is set when the pool doesn't belong to any listener in the load balancer.
            type: str
            sample: "7c4be3f8-9c2f-11e8-83b3-44a8422643a4"
        listener_id:
            description: The listener ID the pool belongs to.
            type: str
            sample: "956aa716-9c2f-11e8-83b3-44a8422643a4"
        provisioning_status:
            description: The provisioning status of the pool.
            type: str
            sample: "ACTIVE"
        operating_status:
            description: The operating status of the pool.
            type: str
            sample: "ONLINE"
        is_admin_state_up:
            description: The administrative state of the pool.
            type: bool
            sample: true
        protocol:
            description: The protocol for the pool.
            type: str
            sample: "HTTP"
        lb_algorithm:
            description: The load balancing algorithm for the pool.
            type: str
            sample: "ROUND_ROBIN"
'''

EXAMPLES = '''
# Create a pool, wait for the pool to be active.
- os_pool:
    cloud: mycloud
    endpoint_type: admin
    state: present
    name: test-pool
    loadbalancer: test-loadbalancer
    protocol: HTTP
    lb_algorithm: ROUND_ROBIN

# Delete a pool
- os_pool:
    cloud: mycloud
    endpoint_type: admin
    state: absent
    name: test-pool
'''

import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, \
    openstack_module_kwargs, openstack_cloud_from_module


def _wait_for_pool_status(module, cloud, pool_id, status, failures,
                          interval=5):
    timeout = module.params['timeout']

    total_sleep = 0
    if failures is None:
        failures = []

    while total_sleep < timeout:
        pool = cloud.load_balancer.get_pool(pool_id)
        provisioning_status = pool.provisioning_status
        if provisioning_status == status:
            return pool
        if provisioning_status in failures:
            module.fail_json(
                msg="pool %s transitioned to failure state %s" %
                    (pool_id, provisioning_status)
            )

        time.sleep(interval)
        total_sleep += interval

    module.fail_json(
        msg="timeout waiting for pool %s to transition to %s" %
            (pool_id, status)
    )


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
        loadbalancer=dict(default=None),
        listener=dict(default=None),
        protocol=dict(default='HTTP',
                      choices=['HTTP', 'HTTPS', 'TCP', 'UDP', 'PROXY']),
        lb_algorithm=dict(
            default='ROUND_ROBIN',
            choices=['ROUND_ROBIN', 'LEAST_CONNECTIONS', 'SOURCE_IP']
        )
    )
    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[['loadbalancer', 'listener']]
    )
    module = AnsibleModule(argument_spec, **module_kwargs)
    sdk, cloud = openstack_cloud_from_module(module)

    loadbalancer = module.params['loadbalancer']
    listener = module.params['listener']

    try:
        changed = False
        pool = cloud.load_balancer.find_pool(name_or_id=module.params['name'])

        if module.params['state'] == 'present':
            if not pool:
                loadbalancer_id = None
                if not (loadbalancer or listener):
                    module.fail_json(
                        msg="either loadbalancer or listener must be provided"
                    )

                if loadbalancer:
                    lb = cloud.load_balancer.find_load_balancer(loadbalancer)
                    if not lb:
                        module.fail_json(msg='load balancer %s is not '
                                             'found' % loadbalancer)
                    loadbalancer_id = lb.id

                listener_id = None
                if listener:
                    listener_ret = cloud.load_balancer.find_listener(listener)
                    if not listener_ret:
                        module.fail_json(msg='listener %s is not found'
                                             % listener)
                    listener_id = listener_ret.id

                pool = cloud.load_balancer.create_pool(
                    name=module.params['name'],
                    loadbalancer_id=loadbalancer_id,
                    listener_id=listener_id,
                    protocol=module.params['protocol'],
                    lb_algorithm=module.params['lb_algorithm']
                )
                changed = True

                if not module.params['wait']:
                    module.exit_json(changed=changed,
                                     pool=pool.to_dict(),
                                     id=pool.id)

            if module.params['wait']:
                pool = _wait_for_pool_status(module, cloud, pool.id, "ACTIVE",
                                             ["ERROR"])

            module.exit_json(changed=changed, pool=pool.to_dict(),
                             id=pool.id)

        elif module.params['state'] == 'absent':
            if pool:
                cloud.load_balancer.delete_pool(pool)
                changed = True

            module.exit_json(changed=changed)
    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == "__main__":
    main()
