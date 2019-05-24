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
module: os_port
short_description: Add/Update/Delete ports from an OpenStack cloud.
extends_documentation_fragment: openstack
author: "Davide Agnello (@dagnello)"
version_added: "2.0"
description:
   - Add, Update or Remove ports from an OpenStack cloud. A I(state) of
     'present' will ensure the port is created or updated if required.
options:
   network:
     description:
        - Network ID or name this port belongs to.
     required: true
   name:
     description:
        - Name that has to be given to the port.
   fixed_ips:
     description:
        - Desired IP and/or subnet for this port.  Subnet is referenced by
          subnet_id and IP is referenced by ip_address.
   admin_state_up:
     description:
        - Sets admin state.
     type: bool
   mac_address:
     description:
        - MAC address of this port.
   security_groups:
     description:
        - Security group(s) ID(s) or name(s) associated with the port (comma
          separated string or YAML list)
   no_security_groups:
     description:
        - Do not associate a security group with this port.
     type: bool
     default: 'no'
   allowed_address_pairs:
     description:
        - "Allowed address pairs list.  Allowed address pairs are supported with
          dictionary structure.
          e.g.  allowed_address_pairs:
                  - ip_address: 10.1.0.12
                    mac_address: ab:cd:ef:12:34:56
                  - ip_address: ..."
   extra_dhcp_opts:
     description:
        - "Extra dhcp options to be assigned to this port.  Extra options are
          supported with dictionary structure.
          e.g.  extra_dhcp_opts:
                  - opt_name: opt name1
                    opt_value: value1
                  - opt_name: ..."
   device_owner:
     description:
        - The ID of the entity that uses this port.
   device_id:
     description:
        - Device ID of device using this port.
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
   vnic_type:
     description:
       - The type of the port that should be created
     choices: [normal, direct, direct-physical, macvtap, baremetal, virtio-forwarder]
     version_added: "2.8"
   port_security_enabled:
     description:
       - Whether to enable or disable the port security on the network.
     type: bool
     version_added: "2.8"
'''

EXAMPLES = '''
# Create a port
- os_port:
    state: present
    auth:
      auth_url: https://identity.example.com
      username: admin
      password: admin
      project_name: admin
    name: port1
    network: foo

# Create a port with a static IP
- os_port:
    state: present
    auth:
      auth_url: https://identity.example.com
      username: admin
      password: admin
      project_name: admin
    name: port1
    network: foo
    fixed_ips:
      - ip_address: 10.1.0.21

# Create a port with No security groups
- os_port:
    state: present
    auth:
      auth_url: https://identity.example.com
      username: admin
      password: admin
      project_name: admin
    name: port1
    network: foo
    no_security_groups: True

# Update the existing 'port1' port with multiple security groups (version 1)
- os_port:
    state: present
    auth:
      auth_url: https://identity.example.com
      username: admin
      password: admin
      project_name: admin
    name: port1
    security_groups: 1496e8c7-4918-482a-9172-f4f00fc4a3a5,057d4bdf-6d4d-472...

# Update the existing 'port1' port with multiple security groups (version 2)
- os_port:
    state: present
    auth:
      auth_url: https://identity.example.com
      username: admin
      password: admin
      project_name: admin
    name: port1
    security_groups:
      - 1496e8c7-4918-482a-9172-f4f00fc4a3a5
      - 057d4bdf-6d4d-472...

# Create port of type 'direct'
- os_port:
    state: present
    auth:
      auth_url: https://identity.example.com
      username: admin
      password: admin
      project_name: admin
    name: port1
    vnic_type: direct
'''

RETURN = '''
id:
    description: Unique UUID.
    returned: success
    type: str
name:
    description: Name given to the port.
    returned: success
    type: str
network_id:
    description: Network ID this port belongs in.
    returned: success
    type: str
security_groups:
    description: Security group(s) associated with this port.
    returned: success
    type: list
status:
    description: Port's status.
    returned: success
    type: str
fixed_ips:
    description: Fixed ip(s) associated with this port.
    returned: success
    type: list
tenant_id:
    description: Tenant id associated with this port.
    returned: success
    type: str
allowed_address_pairs:
    description: Allowed address pairs with this port.
    returned: success
    type: list
admin_state_up:
    description: Admin state up flag for this port.
    returned: success
    type: bool
vnic_type:
    description: Type of the created port
    returned: success
    type: str
port_security_enabled:
    description: Port security state on the network.
    returned: success
    type: bool
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _needs_update(module, port, cloud):
    """Check for differences in the updatable values.

    NOTE: We don't currently allow name updates.
    """
    compare_simple = ['admin_state_up',
                      'mac_address',
                      'device_owner',
                      'device_id',
                      'binding:vnic_type',
                      'port_security_enabled']
    compare_dict = ['allowed_address_pairs',
                    'extra_dhcp_opts']
    compare_list = ['security_groups']

    for key in compare_simple:
        if module.params[key] is not None and module.params[key] != port[key]:
            return True
    for key in compare_dict:
        if module.params[key] is not None and module.params[key] != port[key]:
            return True
    for key in compare_list:
        if module.params[key] is not None and (set(module.params[key]) !=
                                               set(port[key])):
            return True

    # NOTE: if port was created or updated with 'no_security_groups=True',
    # subsequent updates without 'no_security_groups' flag or
    # 'no_security_groups=False' and no specified 'security_groups', will not
    # result in an update to the port where the default security group is
    # applied.
    if module.params['no_security_groups'] and port['security_groups'] != []:
        return True

    if module.params['fixed_ips'] is not None:
        for item in module.params['fixed_ips']:
            if 'ip_address' in item:
                # if ip_address in request does not match any in existing port,
                # update is required.
                if not any(match['ip_address'] == item['ip_address']
                           for match in port['fixed_ips']):
                    return True
            if 'subnet_id' in item:
                return True
        for item in port['fixed_ips']:
            # if ip_address in existing port does not match any in request,
            # update is required.
            if not any(match.get('ip_address') == item['ip_address']
                       for match in module.params['fixed_ips']):
                return True

    return False


def _system_state_change(module, port, cloud):
    state = module.params['state']
    if state == 'present':
        if not port:
            return True
        return _needs_update(module, port, cloud)
    if state == 'absent' and port:
        return True
    return False


def _compose_port_args(module, cloud):
    port_kwargs = {}
    optional_parameters = ['name',
                           'fixed_ips',
                           'admin_state_up',
                           'mac_address',
                           'security_groups',
                           'allowed_address_pairs',
                           'extra_dhcp_opts',
                           'device_owner',
                           'device_id',
                           'binding:vnic_type',
                           'port_security_enabled']
    for optional_param in optional_parameters:
        if module.params[optional_param] is not None:
            port_kwargs[optional_param] = module.params[optional_param]

    if module.params['no_security_groups']:
        port_kwargs['security_groups'] = []

    return port_kwargs


def get_security_group_id(module, cloud, security_group_name_or_id):
    security_group = cloud.get_security_group(security_group_name_or_id)
    if not security_group:
        module.fail_json(msg="Security group: %s, was not found"
                             % security_group_name_or_id)
    return security_group['id']


def main():
    argument_spec = openstack_full_argument_spec(
        network=dict(required=False),
        name=dict(required=False),
        fixed_ips=dict(type='list', default=None),
        admin_state_up=dict(type='bool', default=None),
        mac_address=dict(default=None),
        security_groups=dict(default=None, type='list'),
        no_security_groups=dict(default=False, type='bool'),
        allowed_address_pairs=dict(type='list', default=None),
        extra_dhcp_opts=dict(type='list', default=None),
        device_owner=dict(default=None),
        device_id=dict(default=None),
        state=dict(default='present', choices=['absent', 'present']),
        vnic_type=dict(default=None,
                       choices=['normal', 'direct', 'direct-physical',
                                'macvtap', 'baremetal', 'virtio-forwarder']),
        port_security_enabled=dict(default=None, type='bool')
    )

    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[
            ['no_security_groups', 'security_groups'],
        ]
    )

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    name = module.params['name']
    state = module.params['state']

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if module.params['security_groups']:
            # translate security_groups to UUID's if names where provided
            module.params['security_groups'] = [
                get_security_group_id(module, cloud, v)
                for v in module.params['security_groups']
            ]

        # Neutron API accept 'binding:vnic_type' as an argument
        # for the port type.
        module.params['binding:vnic_type'] = module.params['vnic_type']
        module.params.pop('vnic_type', None)

        port = None
        network_id = None
        if name:
            port = cloud.get_port(name)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, port, cloud))

        changed = False
        if state == 'present':
            if not port:
                network = module.params['network']
                if not network:
                    module.fail_json(
                        msg="Parameter 'network' is required in Port Create"
                    )
                port_kwargs = _compose_port_args(module, cloud)
                network_object = cloud.get_network(network)

                if network_object:
                    network_id = network_object['id']
                else:
                    module.fail_json(
                        msg="Specified network was not found."
                    )

                port = cloud.create_port(network_id, **port_kwargs)
                changed = True
            else:
                if _needs_update(module, port, cloud):
                    port_kwargs = _compose_port_args(module, cloud)
                    port = cloud.update_port(port['id'], **port_kwargs)
                    changed = True
            module.exit_json(changed=changed, id=port['id'], port=port)

        if state == 'absent':
            if port:
                cloud.delete_port(port['id'])
                changed = True
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
