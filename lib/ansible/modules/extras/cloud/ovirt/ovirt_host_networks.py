#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

try:
    import ovirtsdk4 as sdk
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.ovirt import *


DOCUMENTATION = '''
---
module: ovirt_host_networks
short_description: Module to manage host networks in oVirt
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage host networks in oVirt."
options:
    name:
        description:
            - "Name of the the host to manage networks for."
        required: true
    state:
        description:
            - "Should the host be present/absent."
        choices: ['present', 'absent']
        default: present
    bond:
        description:
            - "Dictionary describing network bond:"
            - "C(name) - Bond name."
            - "C(mode) - Bonding mode."
            - "C(interfaces) - List of interfaces to create a bond."
    interface:
        description:
            - "Name of the network interface where logical network should be attached."
    networks:
        description:
            - "List of dictionary describing networks to be attached to interface or bond:"
            - "C(name) - Name of the logical network to be assigned to bond or interface."
            - "C(boot_protocol) - Boot protocol one of the I(none), I(static) or I(dhcp)."
            - "C(address) - IP address in case of I(static) boot protocol is used."
            - "C(prefix) - Routing prefix in case of I(static) boot protocol is used."
            - "C(gateway) - Gateway in case of I(static) boot protocol is used."
            - "C(version) - IP version. Either v4 or v6."
    labels:
        description:
            - "List of names of the network label to be assigned to bond or interface."
    check:
        description:
            - "If I(true) verify connectivity between host and engine."
            - "Network configuration changes will be rolled back if connectivity between
               engine and the host is lost after changing network configuration."
    save:
        description:
            - "If I(true) network configuration will be persistent, by default they are temporary."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create bond on eth0 and eth1 interface, and put 'myvlan' network on top of it:
- name: Bonds
  ovirt_host_networks:
    name: myhost
    bond:
      name: bond0
      mode: 2
      interfaces:
        - eth1
        - eth2
    networks:
      - name: myvlan
        boot_protocol: static
        address: 1.2.3.4
        prefix: 24
        gateway: 1.2.3.4
        version: v4

# Remove bond0 bond from host interfaces:
- ovirt_host_networks:
    state: absent
    name: myhost
    bond:
      name: bond0

# Assign myvlan1 and myvlan2 vlans to host eth0 interface:
- ovirt_host_networks:
    name: myhost
    interface: eth0
    networks:
      - name: myvlan1
      - name: myvlan2

# Remove myvlan2 vlan from host eth0 interface:
- ovirt_host_networks:
    state: absent
    name: myhost
    interface: eth0
    networks:
      - name: myvlan2

# Remove all networks/vlans from host eth0 interface:
- ovirt_host_networks:
    state: absent
    name: myhost
    interface: eth0
'''

RETURN = '''
id:
    description: ID of the host NIC which is managed
    returned: On success if host NIC is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
host_nic:
    description: "Dictionary of all the host NIC attributes. Host NIC attributes can be found on your oVirt instance
                  at following url: https://ovirt.example.com/ovirt-engine/api/model#types/host_nic."
    returned: On success if host NIC is found.
'''


class HostNetworksModule(BaseModule):

    def build_entity(self):
        return otypes.Host()

    def update_address(self, attachment, network):
        # Check if there is any change in address assignenmts and
        # update it if needed:
        for ip in attachment.ip_address_assignments:
            if str(ip.ip.version) == network.get('version'):
                changed = False
                if not equal(network.get('boot_protocol'), str(ip.assignment_method)):
                    ip.assignment_method = otypes.BootProtocol(network.get('boot_protocol'))
                    changed = True
                if not equal(network.get('address'), ip.ip.address):
                    ip.ip.address = network.get('address')
                    changed = True
                if not equal(network.get('gateway'), ip.ip.gateway):
                    ip.ip.gateway = network.get('gateway')
                    changed = True
                if not equal(network.get('prefix'), int(ip.ip.netmask)):
                    ip.ip.netmask = str(network.get('prefix'))
                    changed = True

                if changed:
                    attachments_service.service(attachment.id).update(attachment)
                    self.changed = True
                    break

    def has_update(self, nic_service):
        update = False
        bond = self._module.params['bond']
        networks = self._module.params['networks']
        nic = nic_service.get()

        if nic is None:
            return update

        # Check if bond configuration should be updated:
        if bond:
            update = not (
                equal(str(bond.get('mode')), nic.bonding.options[0].value) and
                equal(
                    sorted(bond.get('interfaces')) if bond.get('interfaces') else None,
                    sorted(get_link_name(self._connection, s) for s in nic.bonding.slaves)
                )
            )

        if not networks:
            return update

        # Check if networks attachments configuration should be updated:
        attachments_service = nic_service.network_attachments_service()
        network_names = [network.get('name') for network in networks]

        attachments = {}
        for attachment in attachments_service.list():
            name = get_link_name(self._connection, attachment.network)
            if name in network_names:
                attachments[name] = attachment

        for network in networks:
            attachment = attachments.get(network.get('name'))
            # If attachment don't exsits, we need to create it:
            if attachment is None:
                return True

            self.update_address(attachment, network)

        return update

    def _action_save_configuration(self, entity):
        if self._module.params['save']:
            if not self._module.check_mode:
                self._service.service(entity.id).commit_net_config()
            self.changed = True


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(default=None, aliases=['host'], required=True),
        bond=dict(default=None, type='dict'),
        interface=dict(default=None),
        networks=dict(default=None, type='list'),
        labels=dict(default=None, type='list'),
        check=dict(default=None, type='bool'),
        save=dict(default=None, type='bool'),
    )
    module = AnsibleModule(argument_spec=argument_spec)
    check_sdk(module)

    try:
        connection = create_connection(module.params.pop('auth'))
        hosts_service = connection.system_service().hosts_service()
        host_networks_module = HostNetworksModule(
            connection=connection,
            module=module,
            service=hosts_service,
        )

        host = host_networks_module.search_entity()
        if host is None:
            raise Exception("Host '%s' was not found." % module.params['name'])

        bond = module.params['bond']
        interface = module.params['interface']
        networks = module.params['networks']
        labels = module.params['labels']
        nic_name = bond.get('name') if bond else module.params['interface']

        nics_service = hosts_service.host_service(host.id).nics_service()
        nic = search_by_name(nics_service, nic_name)

        state = module.params['state']
        if (
            state == 'present' and
            (nic is None or host_networks_module.has_update(nics_service.service(nic.id)))
        ):
            host_networks_module.action(
                entity=host,
                action='setup_networks',
                post_action=host_networks_module._action_save_configuration,
                check_connectivity=module.params['check'],
                modified_bonds=[
                    otypes.HostNic(
                        name=bond.get('name'),
                        bonding=otypes.Bonding(
                            options=[
                                otypes.Option(
                                    name="mode",
                                    value=str(bond.get('mode')),
                                )
                            ],
                            slaves=[
                                otypes.HostNic(name=i) for i in bond.get('interfaces', [])
                            ],
                        ),
                    ),
                ] if bond else None,
                modified_labels=[
                    otypes.NetworkLabel(
                        name=str(name),
                        host_nic=otypes.HostNic(
                            name=bond.get('name') if bond else interface
                        ),
                    ) for name in labels
                ] if labels else None,
                modified_network_attachments=[
                    otypes.NetworkAttachment(
                        network=otypes.Network(
                            name=network['name']
                        ) if network['name'] else None,
                        host_nic=otypes.HostNic(
                            name=bond.get('name') if bond else interface
                        ),
                        ip_address_assignments=[
                            otypes.IpAddressAssignment(
                                assignment_method=otypes.BootProtocol(
                                    network.get('boot_protocol', 'none')
                                ),
                                ip=otypes.Ip(
                                    address=network.get('address'),
                                    gateway=network.get('gateway'),
                                    netmask=network.get('netmask'),
                                    version=otypes.IpVersion(
                                        network.get('version')
                                    ) if network.get('version') else None,
                                ),
                            ),
                        ],
                    ) for network in networks
                ] if networks else None,
            )
        elif state == 'absent' and nic:
            attachments_service = nics_service.nic_service(nic.id).network_attachments_service()
            attachments = attachments_service.list()
            if networks:
                network_names = [network['name'] for network in networks]
                attachments = [
                    attachment for attachment in attachments
                    if get_link_name(connection, attachment.network) in network_names
                ]
            if labels or bond or attachments:
                host_networks_module.action(
                    entity=host,
                    action='setup_networks',
                    post_action=host_networks_module._action_save_configuration,
                    check_connectivity=module.params['check'],
                    removed_bonds=[
                        otypes.HostNic(
                            name=bond.get('name'),
                        ),
                    ] if bond else None,
                    removed_labels=[
                        otypes.NetworkLabel(
                            name=str(name),
                        ) for name in labels
                    ] if labels else None,
                    removed_network_attachments=list(attachments),
                )

        nic = search_by_name(nics_service, nic_name)
        module.exit_json(**{
            'changed': host_networks_module.changed,
            'id': nic.id if nic else None,
            'host_nic': get_dict_of_struct(nic),
        })
    except Exception as e:
        module.fail_json(msg=str(e))
    finally:
        connection.close(logout=False)

from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
