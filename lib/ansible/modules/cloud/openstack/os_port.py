#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
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
     required: false
     default: None
   fixed_ips:
     description:
        - Desired IP and/or subnet for this port.  Subnet is referenced by
          subnet_id and IP is referenced by ip_address.
     required: false
     default: None
   admin_state_up:
     description:
        - Sets admin state.
     required: false
     default: None
   mac_address:
     description:
        - MAC address of this port.
     required: false
     default: None
   security_groups:
     description:
        - Security group(s) ID(s) or name(s) associated with the port (comma
          separated string or YAML list)
     required: false
     default: None
   no_security_groups:
     description:
        - Do not associate a security group with this port.
     required: false
     default: False
   allowed_address_pairs:
     description:
        - "Allowed address pairs list.  Allowed address pairs are supported with
          dictionary structure.
          e.g.  allowed_address_pairs:
                  - ip_address: 10.1.0.12
                    mac_address: ab:cd:ef:12:34:56
                  - ip_address: ..."
     required: false
     default: None
   extra_dhcp_opts:
     description:
        - "Extra dhcp options to be assigned to this port.  Extra options are
          supported with dictionary structure.
          e.g.  extra_dhcp_opts:
                  - opt_name: opt name1
                    opt_value: value1
                  - opt_name: ..."
     required: false
     default: None
   device_owner:
     description:
        - The ID of the entity that uses this port.
     required: false
     default: None
   device_id:
     description:
        - Device ID of device using this port.
     required: false
     default: None
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
'''

EXAMPLES = '''
# Create a port
- os_port:
    state: present
    auth:
      auth_url: https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0/
      username: admin
      password: admin
      project_name: admin
    name: port1
    network: foo

# Create a port with a static IP
- os_port:
    state: present
    auth:
      auth_url: https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0/
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
      auth_url: https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0/
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
      auth_url: https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0/d
      username: admin
      password: admin
      project_name: admin
    name: port1
    security_groups: 1496e8c7-4918-482a-9172-f4f00fc4a3a5,057d4bdf-6d4d-472...

# Update the existing 'port1' port with multiple security groups (version 2)
- os_port:
    state: present
    auth:
      auth_url: https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0/d
      username: admin
      password: admin
      project_name: admin
    name: port1
    security_groups:
      - 1496e8c7-4918-482a-9172-f4f00fc4a3a5
      - 057d4bdf-6d4d-472...
'''

RETURN = '''
id:
    description: Unique UUID.
    returned: success
    type: string
name:
    description: Name given to the port.
    returned: success
    type: string
network_id:
    description: Network ID this port belongs in.
    returned: success
    type: string
security_groups:
    description: Security group(s) associated with this port.
    returned: success
    type: list
status:
    description: Port's status.
    returned: success
    type: string
fixed_ips:
    description: Fixed ip(s) associated with this port.
    returned: success
    type: list
tenant_id:
    description: Tenant id associated with this port.
    returned: success
    type: string
allowed_address_pairs:
    description: Allowed address pairs with this port.
    returned: success
    type: list
admin_state_up:
    description: Admin state up flag for this port.
    returned: success
    type: bool
'''

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


def _needs_update(module, port, cloud):
    """Check for differences in the updatable values.

    NOTE: We don't currently allow name updates.
    """
    compare_simple = ['admin_state_up',
                      'mac_address',
                      'device_owner',
                      'device_id']
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
                           'device_id']
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
    )

    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[
            ['no_security_groups', 'security_groups'],
        ]
    )

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')
    name = module.params['name']
    state = module.params['state']

    try:
        cloud = shade.openstack_cloud(**module.params)
        if module.params['security_groups']:
            # translate security_groups to UUID's if names where provided
            module.params['security_groups'] = [
                get_security_group_id(module, cloud, v)
                for v in module.params['security_groups']
            ]

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

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
