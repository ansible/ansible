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
module: os_loadbalancer
short_description: Add/Delete load balancer from OpenStack Cloud
extends_documentation_fragment: openstack
version_added: "2.7"
author: "Lingxian Kong (@lingxiankong)"
description:
   - Add or Remove load balancer from the OpenStack load-balancer service.
options:
   name:
     description:
        - Name that has to be given to the load balancer
     required: true
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   vip_network:
     description:
        - The name or id of the network for the virtual IP of the load balancer.
          One of vip_network, vip_subnet, or vip_port must be specified.
   vip_subnet:
     description:
        - The name or id of the subnet for the virtual IP of the load balancer.
          One of vip_network, vip_subnet, or vip_port must be specified.
   vip_port:
     description:
        - The name or id of the load balancer virtual IP port. One of
          vip_network, vip_subnet, or vip_port must be specified.
   vip_address:
     description:
        - IP address of the load balancer virtual IP.
   wait:
     description:
        - If the module should wait for the load balancer to be created.
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
    description: Unique UUID.
    returned: success
    type: string
name:
    description: Name given to the load balancer.
    returned: success
    type: string
vip_network_id:
    description: Network ID the load balancer virutal IP port belongs in.
    returned: success
    type: string
vip_subnet_id:
    description: Subnet ID the load balancer virutal IP port belongs in.
    returned: success
    type: string
vip_port_id:
    description: The load balancer virutal IP port ID.
    returned: success
    type: string
vip_address:
    description: The load balancer virutal IP address.
    returned: success
    type: string
provisioning_status:
    description: The provisioning status of the load balancer.
    returned: success
    type: string
operating_status:
    description: The operating status of the load balancer.
    returned: success
    type: string
is_admin_state_up:
    description: The administrative state of the load balancer.
    returned: success
    type: bool
listeners:
    description: The associated listener IDs, if any.
    returned: success
    type: list
pools:
    description: The associated pool IDs, if any.
    returned: success
    type: list
'''

EXAMPLES = '''
# Create a load balancer by specifying the VIP subnet.
- os_loadbalancer:
    auth:
      auth_url: https://identity.example.com
      username: admin
      password: passme
      project_name: admin
    state: present
    name: my_lb
    vip_subnet: my_subnet
    timeout: 150

# Create a load balancer by specifying the VIP network and the IP address.
- os_loadbalancer:
    auth:
      auth_url: https://identity.example.com
      username: admin
      password: passme
      project_name: admin
    state: present
    name: my_lb
    vip_network: my_network
    vip_address: 192.168.0.11
'''

import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, \
    openstack_module_kwargs, openstack_cloud_from_module


def _lb_wait_for_status(module, cloud, lb, status, failures, interval=5):
    """Wait for load balancer to be in a particular provisioning status."""
    timeout = module.params['timeout']

    total_sleep = 0
    if failures is None:
        failures = []

    while total_sleep < timeout:
        lb = cloud.load_balancer.get_load_balancer(lb.id)
        if lb.provisioning_status == status:
            return None
        if lb.provisioning_status in failures:
            module.fail_json(
                msg="Load Balancer %s transitioned to failure state %s" %
                    (lb.id, lb.provisioning_status)
            )

        time.sleep(interval)
        total_sleep += interval

    module.fail_json(
        msg="Timeout waiting for Load Balancer %s to transition to %s" %
            (lb.id, status)
    )


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
        vip_network=dict(required=False),
        vip_subnet=dict(required=False),
        vip_port=dict(required=False),
        vip_address=dict(required=False),
    )
    module_kwargs = openstack_module_kwargs(
        required_one_of=[
            ['vip_network', 'vip_subnet', 'vip_port'],
        ]
    )
    module = AnsibleModule(argument_spec, **module_kwargs)

    sdk, cloud = openstack_cloud_from_module(module)
    vip_network_id = None
    vip_subnet_id = None
    vip_port_id = None

    try:
        changed = False
        lb = cloud.load_balancer.find_load_balancer(
            name_or_id=module.params['name'])

        if module.params['state'] == 'present':
            if not lb:
                if module.params['vip_network']:
                    network = cloud.get_network(module.params['vip_network'])
                    if not network:
                        module.fail_json(
                            msg='network %s is not found' %
                                module.params['vip_network']
                        )
                    vip_network_id = network.id
                if module.params['vip_subnet']:
                    subnet = cloud.get_subnet(module.params['vip_subnet'])
                    if not subnet:
                        module.fail_json(
                            msg='subnet %s is not found' %
                                module.params['vip_subnet']
                        )
                    vip_subnet_id = subnet.id
                if module.params['vip_port']:
                    port = cloud.get_port(module.params['vip_port'])
                    if not port:
                        module.fail_json(
                            msg='port %s is not found' %
                                module.params['vip_port']
                        )
                    vip_port_id = port.id

                lb = cloud.load_balancer.create_load_balancer(
                    name=module.params['name'],
                    vip_network_id=vip_network_id,
                    vip_subnet_id=vip_subnet_id,
                    vip_port_id=vip_port_id,
                    vip_address=module.params['vip_address'],
                )
                changed = True

                if not module.params['wait']:
                    module.exit_json(changed=changed,
                                     loadbalancer=lb.to_dict(), id=lb.id)

            if module.params['wait']:
                _lb_wait_for_status(module, cloud, lb, "ACTIVE", ["ERROR"])

            module.exit_json(changed=changed, loadbalancer=lb.to_dict(),
                             id=lb.id)
        elif module.params['state'] == 'absent':
            if not lb:
                changed = False
            else:
                # Deleting load balancer with `cascade=False` does not make
                # sense because the deletion will always fail if there are
                # sub-resources.
                cloud.load_balancer.delete_load_balancer(lb, cascade=True)
                changed = True

            module.exit_json(changed=changed)
    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == "__main__":
    main()
