#!/usr/bin/python

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_network
short_description: Creates/removes networks from OpenStack
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Monty Taylor (@emonty)"
description:
   - Add or remove network from OpenStack.
options:
   name:
     description:
        - Name to be assigned to the network.
     required: true
   shared:
     description:
        - Whether this network is shared or not.
     type: bool
     default: 'no'
   admin_state_up:
     description:
        - Whether the state should be marked as up or down.
     type: bool
     default: 'yes'
   external:
     description:
        - Whether this network is externally accessible.
     type: bool
     default: 'no'
   state:
     description:
        - Indicate desired state of the resource.
     choices: ['present', 'absent']
     default: present
   provider_physical_network:
     description:
        - The physical network where this network object is implemented.
     version_added: "2.1"
   provider_network_type:
     description:
        - The type of physical network that maps to this network resource.
     version_added: "2.1"
   provider_segmentation_id:
     description:
        - An isolated segment on the physical network. The I(network_type)
          attribute defines the segmentation model. For example, if the
          I(network_type) value is vlan, this ID is a vlan identifier. If
          the I(network_type) value is gre, this ID is a gre key.
     version_added: "2.1"
   project:
     description:
        - Project name or ID containing the network (name admin-only)
     version_added: "2.1"
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
   port_security_enabled:
     description:
        -  Whether port security is enabled on the network or not.
           Network will use OpenStack defaults if this option is
           not utilised.
     type: bool
     version_added: "2.8"
requirements:
     - "openstacksdk"
'''

EXAMPLES = '''
# Create an externally accessible network named 'ext_network'.
- os_network:
    cloud: mycloud
    state: present
    name: ext_network
    external: true
'''

RETURN = '''
network:
    description: Dictionary describing the network.
    returned: On success when I(state) is 'present'.
    type: complex
    contains:
        id:
            description: Network ID.
            type: str
            sample: "4bb4f9a5-3bd2-4562-bf6a-d17a6341bb56"
        name:
            description: Network name.
            type: str
            sample: "ext_network"
        shared:
            description: Indicates whether this network is shared across all tenants.
            type: bool
            sample: false
        status:
            description: Network status.
            type: str
            sample: "ACTIVE"
        mtu:
            description: The MTU of a network resource.
            type: int
            sample: 0
        admin_state_up:
            description: The administrative state of the network.
            type: bool
            sample: true
        port_security_enabled:
            description: The port security status
            type: bool
            sample: true
        router:external:
            description: Indicates whether this network is externally accessible.
            type: bool
            sample: true
        tenant_id:
            description: The tenant ID.
            type: str
            sample: "06820f94b9f54b119636be2728d216fc"
        subnets:
            description: The associated subnets.
            type: list
            sample: []
        "provider:physical_network":
            description: The physical network where this network object is implemented.
            type: str
            sample: my_vlan_net
        "provider:network_type":
            description: The type of physical network that maps to this network resource.
            type: str
            sample: vlan
        "provider:segmentation_id":
            description: An isolated segment on the physical network.
            type: str
            sample: 101
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        shared=dict(default=False, type='bool'),
        admin_state_up=dict(default=True, type='bool'),
        external=dict(default=False, type='bool'),
        provider_physical_network=dict(required=False),
        provider_network_type=dict(required=False),
        provider_segmentation_id=dict(required=False, type='int'),
        state=dict(default='present', choices=['absent', 'present']),
        project=dict(default=None),
        port_security_enabled=dict(type='bool')
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    state = module.params['state']
    name = module.params['name']
    shared = module.params['shared']
    admin_state_up = module.params['admin_state_up']
    external = module.params['external']
    provider_physical_network = module.params['provider_physical_network']
    provider_network_type = module.params['provider_network_type']
    provider_segmentation_id = module.params['provider_segmentation_id']
    project = module.params.get('project')
    port_security_enabled = module.params.get('port_security_enabled')

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if project is not None:
            proj = cloud.get_project(project)
            if proj is None:
                module.fail_json(msg='Project %s could not be found' % project)
            project_id = proj['id']
            filters = {'tenant_id': project_id}
        else:
            project_id = None
            filters = None
        net = cloud.get_network(name, filters=filters)

        if state == 'present':
            if not net:
                provider = {}
                if provider_physical_network:
                    provider['physical_network'] = provider_physical_network
                if provider_network_type:
                    provider['network_type'] = provider_network_type
                if provider_segmentation_id:
                    provider['segmentation_id'] = provider_segmentation_id

                if project_id is not None:
                    net = cloud.create_network(name, shared, admin_state_up,
                                               external, provider, project_id,
                                               port_security_enabled=port_security_enabled)
                else:
                    net = cloud.create_network(name, shared, admin_state_up,
                                               external, provider,
                                               port_security_enabled=port_security_enabled)
                changed = True
            else:
                changed = False
            module.exit_json(changed=changed, network=net, id=net['id'])

        elif state == 'absent':
            if not net:
                module.exit_json(changed=False)
            else:
                cloud.delete_network(name)
                module.exit_json(changed=True)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
