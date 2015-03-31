#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
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


try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_floating_ip
version_added: "2.0"
short_description: Add/Remove floating IP from an instance
extends_documentation_fragment: openstack
description:
   - Add or Remove a floating IP to an instance
options:
   server:
     description:
        - The name or ID of the instance to which the IP address
          should be assigned.
     required: true
   network_name:
     description:
        - Name of the network from which IP has to be assigned to VM.
          Please make sure the network is an external network.
        - Required if ip_address is not given.
     required: true
     default: None
   internal_network_name:
     description:
        - Name of the network of the port to associate with the floating ip.
          Necessary when VM multiple networks.
     required: false
     default: None
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     required: false
     default: present
requirements: ["shade"]
'''

EXAMPLES = '''
# Assign a floating ip to the instance from an external network
- os_floating_ip:
     cloud: mordred
     state: present
     server: vm1
     network_name: external_network
     internal_network_name: internal_network
'''


def _get_server_state(module, cloud):
    info = None
    server = cloud.get_server(module.params['server'])
    if server:
        info = server._info
        status = info['status']
        if status != 'ACTIVE' and module.params['state'] == 'present':
            module.fail_json(
                msg="The VM is available but not Active. State: %s" % status
            )
    return info, server


def _get_port_info(neutron, module, instance_id, internal_network_name=None):
    subnet_id = None
    if internal_network_name:
        kwargs = {'name': internal_network_name}
        networks = neutron.list_networks(**kwargs)
        network_id = networks['networks'][0]['id']
        kwargs = {
            'network_id': network_id,
            'ip_version': 4
        }
        subnets = neutron.list_subnets(**kwargs)
        subnet_id = subnets['subnets'][0]['id']

    kwargs = {
        'device_id': instance_id,
    }
    try:
        ports = neutron.list_ports(**kwargs)
    except Exception, e:
        module.fail_json(msg="Error in listing ports: %s" % e.message)

    if subnet_id:
        port = next(port for port in ports['ports'] if port['fixed_ips'][0]['subnet_id'] == subnet_id)
        port_id = port['id']
        fixed_ip_address = port['fixed_ips'][0]['ip_address']
    else:
        port_id = ports['ports'][0]['id']
        fixed_ip_address = ports['ports'][0]['fixed_ips'][0]['ip_address']

    if not ports['ports']:
        return None, None
    return fixed_ip_address, port_id


def _get_floating_ip(neutron, module, fixed_ip_address):
    kwargs = {
        'fixed_ip_address': fixed_ip_address
    }
    try:
        ips = neutron.list_floatingips(**kwargs)
    except Exception, e:
        module.fail_json(
            msg="Error in fetching the floatingips's %s" % e.message
        )

    if not ips['floatingips']:
        return None, None

    return (ips['floatingips'][0]['id'],
            ips['floatingips'][0]['floating_ip_address'])


def _create_and_associate_floating_ip(neutron, module, port_id,
                                      net_id, fixed_ip):
    kwargs = {
        'port_id': port_id,
        'floating_network_id': net_id,
        'fixed_ip_address': fixed_ip
    }

    try:
        result = neutron.create_floatingip({'floatingip': kwargs})
    except Exception, e:
        module.fail_json(
            msg="Error in updating the floating ip address: %s" % e.message
        )

    module.exit_json(
        changed=True,
        result=result,
        public_ip=result['floatingip']['floating_ip_address']
    )


def _get_public_net_id(neutron, module):
    kwargs = {
        'name': module.params['network_name'],
    }
    try:
        networks = neutron.list_networks(**kwargs)
    except Exception, e:
        module.fail_json("Error in listing neutron networks: %s" % e.message)
    if not networks['networks']:
        return None
    return networks['networks'][0]['id']


def _update_floating_ip(neutron, module, port_id, floating_ip_id):
    kwargs = {
        'port_id': port_id
    }
    try:
        result = neutron.update_floatingip(floating_ip_id,
                                           {'floatingip': kwargs})
    except Exception, e:
        module.fail_json(
            msg="Error in updating the floating ip address: %s" % e.message
        )
    module.exit_json(changed=True, result=result)


def main():
    argument_spec = openstack_full_argument_spec(
        server                = dict(required=True),
        network_name          = dict(required=True),
        internal_network_name = dict(default=None),
        state                 = dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']
    internal_network_name = module.params['internal_network_name']

    try:
        cloud = shade.openstack_cloud(**module.params)
        neutron = cloud.neutron_client

        server_info, server_obj = _get_server_state(module, cloud)
        if not server_info:
            module.fail_json(msg="The server provided cannot be found")

        fixed_ip, port_id = _get_port_info(
            neutron, module, server_info['id'], internal_network_name)
        if not port_id:
            module.fail_json(msg="Cannot find a port for this instance,"
                                 " maybe fixed ip is not assigned")

        floating_id, floating_ip = _get_floating_ip(neutron, module, fixed_ip)

        if state == 'present':
            if floating_ip:
                # This server already has a floating IP assigned
                module.exit_json(changed=False, public_ip=floating_ip)

            pub_net_id = _get_public_net_id(neutron, module)
            if not pub_net_id:
                module.fail_json(
                    msg="Cannot find the public network specified"
                )
            _create_and_associate_floating_ip(neutron, module, port_id,
                                              pub_net_id, fixed_ip)

        elif state == 'absent':
            if floating_ip:
                _update_floating_ip(neutron, module, None, floating_id)
            module.exit_json(changed=False)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()
