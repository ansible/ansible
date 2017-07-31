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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_nics
short_description: Module to manage network interfaces of Virtual Machines in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage network interfaces of Virtual Machines in oVirt/RHV."
options:
    name:
        description:
            - "Name of the network interface to manage."
        required: true
    vm:
        description:
            - "Name of the Virtual Machine to manage."
            - "You must provide either C(vm) parameter or C(template) parameter."
    template:
        description:
            - "Name of the template to manage."
            - "You must provide either C(vm) parameter or C(template) parameter."
        version_added: "2.4"
    state:
        description:
            - "Should the Virtual Machine NIC be present/absent/plugged/unplugged."
        choices: ['present', 'absent', 'plugged', 'unplugged']
        default: present
    network:
        description:
            - "Logical network to which the VM network interface should use,
               by default Empty network is used if network is not specified."
    profile:
        description:
            - "Virtual network interface profile to be attached to VM network interface."
    interface:
        description:
            - "Type of the network interface."
        choices: ['virtio', 'e1000', 'rtl8139', 'pci_passthrough', 'rtl8139_virtio', 'spapr_vlan']
        default: 'virtio'
    mac_address:
        description:
            - "Custom MAC address of the network interface, by default it's obtained from MAC pool."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add NIC to VM
- ovirt_nics:
    state: present
    vm: myvm
    name: mynic
    interface: e1000
    mac_address: 00:1a:4a:16:01:56
    profile: ovirtmgmt
    network: ovirtmgmt

# Plug NIC to VM
- ovirt_nics:
    state: plugged
    vm: myvm
    name: mynic

# Unplug NIC from VM
- ovirt_nics:
    state: unplugged
    vm: myvm
    name: mynic


# add NIC to template
- ovirt_nics:
    auth: "{{ ovirt_auth }}"
    state: present
    template: my_template
    name: nic1
    interface: virtio
    profile: ovirtmgmt
    network: ovirtmgmt


# Remove NIC from VM
- ovirt_nics:
    state: absent
    vm: myvm
    name: mynic

'''

RETURN = '''
id:
    description: ID of the network interface which is managed
    returned: On success if network interface is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
nic:
    description: "Dictionary of all the network interface attributes. Network interface attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/nic."
    returned: On success if network interface is found.
    type: dict
'''

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    equal,
    get_link_name,
    ovirt_full_argument_spec,
    search_by_name,
)


class EntityNicsModule(BaseModule):

    def __init__(self, *args, **kwargs):
        super(EntityNicsModule, self).__init__(*args, **kwargs)
        self.vnic_id = None

    @property
    def vnic_id(self):
        return self._vnic_id

    @vnic_id.setter
    def vnic_id(self, vnic_id):
        self._vnic_id = vnic_id

    def build_entity(self):
        return otypes.Nic(
            name=self._module.params.get('name'),
            interface=otypes.NicInterface(
                self._module.params.get('interface')
            ) if self._module.params.get('interface') else None,
            vnic_profile=otypes.VnicProfile(
                id=self.vnic_id,
            ) if self.vnic_id else None,
            mac=otypes.Mac(
                address=self._module.params.get('mac_address')
            ) if self._module.params.get('mac_address') else None,
        )

    def update_check(self, entity):
        if self._module.params.get('vm'):
            return (
                equal(self._module.params.get('interface'), str(entity.interface)) and
                equal(self._module.params.get('profile'), get_link_name(self._connection, entity.vnic_profile)) and
                equal(self._module.params.get('mac_address'), entity.mac.address)
            )
        elif self._module.params.get('template'):
            return (
                equal(self._module.params.get('interface'), str(entity.interface)) and
                equal(self._module.params.get('profile'), get_link_name(self._connection, entity.vnic_profile))
            )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent', 'plugged', 'unplugged'],
            default='present'
        ),
        vm=dict(required=False),
        template=dict(required=False),
        name=dict(required=True),
        interface=dict(default=None),
        profile=dict(default=None),
        network=dict(default=None),
        mac_address=dict(default=None),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['vm', 'template']]
    )
    check_sdk(module)

    try:
        # Locate the service that manages the virtual machines and use it to
        # search for the NIC:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        entity_name = None

        if module.params.get('vm'):
            # Locate the VM, where we will manage NICs:
            entity_name = module.params.get('vm')
            collection_service = connection.system_service().vms_service()
        elif module.params.get('template'):
            entity_name = module.params.get('template')
            collection_service = connection.system_service().templates_service()

        # TODO: We have to modify the search_by_name function to accept raise_error=True/False,
        entity = search_by_name(collection_service, entity_name)
        if entity is None:
            raise Exception("Vm/Template '%s' was not found." % entity_name)

        service = collection_service.service(entity.id)
        cluster_id = entity.cluster

        nics_service = service.nics_service()
        entitynics_module = EntityNicsModule(
            connection=connection,
            module=module,
            service=nics_service,
        )

        # Find vNIC id of the network interface (if any):
        profile = module.params.get('profile')
        if profile and module.params['network']:
            cluster_name = get_link_name(connection, cluster_id)
            dcs_service = connection.system_service().data_centers_service()
            dc = dcs_service.list(search='Clusters.name=%s' % cluster_name)[0]
            networks_service = dcs_service.service(dc.id).networks_service()
            network = next(
                (n for n in networks_service.list()
                if n.name == module.params['network']),
                None
            )
            if network is None:
                raise Exception(
                    "Network '%s' was not found in datacenter '%s'." % (
                        module.params['network'],
                        dc.name
                    )
                )
            for vnic in connection.system_service().vnic_profiles_service().list():
                if vnic.name == profile and vnic.network.id == network.id:
                    entitynics_module.vnic_id = vnic.id

        # Handle appropriate action:
        state = module.params['state']
        if state == 'present':
            ret = entitynics_module.create()
        elif state == 'absent':
            ret = entitynics_module.remove()
        elif state == 'plugged':
            entitynics_module.create()
            ret = entitynics_module.action(
                action='activate',
                action_condition=lambda nic: not nic.plugged,
                wait_condition=lambda nic: nic.plugged,
            )
        elif state == 'unplugged':
            entitynics_module.create()
            ret = entitynics_module.action(
                action='deactivate',
                action_condition=lambda nic: nic.plugged,
                wait_condition=lambda nic: not nic.plugged,
            )

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)

if __name__ == "__main__":
    main()
