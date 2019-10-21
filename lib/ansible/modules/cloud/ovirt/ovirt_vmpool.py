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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_vmpool
short_description: Module to manage VM pools in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage VM pools in oVirt/RHV."
options:
    id:
        description:
            - "ID of the vmpool to manage."
        version_added: "2.8"
    name:
        description:
            - "Name of the VM pool to manage."
        required: true
    comment:
        description:
            - Comment of the Virtual Machine pool.
    state:
        description:
            - "Should the VM pool be present/absent."
            - "Note that when C(state) is I(absent) all VMs in VM pool are stopped and removed."
        choices: ['present', 'absent']
        default: present
    template:
        description:
            - "Name of the template, which will be used to create VM pool."
    description:
        description:
            - "Description of the VM pool."
    cluster:
        description:
            - "Name of the cluster, where VM pool should be created."
    type:
        description:
            - "Type of the VM pool. Either manual or automatic."
            - "C(manual) - The administrator is responsible for explicitly returning the virtual machine to the pool.
               The virtual machine reverts to the original base image after the administrator returns it to the pool."
            - "C(Automatic) - When the virtual machine is shut down, it automatically reverts to its base image and
               is returned to the virtual machine pool."
            - "Default value is set by engine."
        choices: ['manual', 'automatic']
    vm_per_user:
        description:
            - "Maximum number of VMs a single user can attach to from this pool."
            - "Default value is set by engine."
    prestarted:
        description:
            - "Number of pre-started VMs defines the number of VMs in run state, that are waiting
               to be attached to Users."
            - "Default value is set by engine."
    vm_count:
        description:
            - "Number of VMs in the pool."
            - "Default value is set by engine."
    vm:
        description:
            - "For creating vm pool without editing template."
            - "Note: You can use C(vm) only for creating vm pool."
        type: dict
        suboptions:
            comment:
                description:
                    - Comment of the Virtual Machine.
            timezone:
                description:
                    - Sets time zone offset of the guest hardware clock.
                    - For example C(Etc/GMT)
            memory:
                description:
                    - Amount of memory of the Virtual Machine. Prefix uses IEC 60027-2 standard (for example 1GiB, 1024MiB).
                    - Default value is set by engine.
            memory_guaranteed:
                description:
                    - Amount of minimal guaranteed memory of the Virtual Machine.
                      Prefix uses IEC 60027-2 standard (for example 1GiB, 1024MiB).
                    - C(memory_guaranteed) parameter can't be lower than C(memory) parameter.
                    - Default value is set by engine.
            memory_max:
                description:
                    - Upper bound of virtual machine memory up to which memory hot-plug can be performed.
                      Prefix uses IEC 60027-2 standard (for example 1GiB, 1024MiB).
                    - Default value is set by engine.
            cloud_init:
                description:
                    - Dictionary with values for Unix-like Virtual Machine initialization using cloud init.
                    - C(host_name) - Hostname to be set to Virtual Machine when deployed.
                    - C(timezone) - Timezone to be set to Virtual Machine when deployed.
                    - C(user_name) - Username to be used to set password to Virtual Machine when deployed.
                    - C(root_password) - Password to be set for user specified by C(user_name) parameter.
                    - C(authorized_ssh_keys) - Use this SSH keys to login to Virtual Machine.
                    - C(regenerate_ssh_keys) - If I(True) SSH keys will be regenerated on Virtual Machine.
                    - C(custom_script) - Cloud-init script which will be executed on Virtual Machine when deployed.  This is appended to the end of the
                      cloud-init script generated by any other options.
                    - C(dns_servers) - DNS servers to be configured on Virtual Machine.
                    - C(dns_search) - DNS search domains to be configured on Virtual Machine.
                    - C(nic_boot_protocol) - Set boot protocol of the network interface of Virtual Machine. Can be one of C(none), C(dhcp) or C(static).
                    - C(nic_ip_address) - If boot protocol is static, set this IP address to network interface of Virtual Machine.
                    - C(nic_netmask) - If boot protocol is static, set this netmask to network interface of Virtual Machine.
                    - C(nic_gateway) - If boot protocol is static, set this gateway to network interface of Virtual Machine.
                    - C(nic_name) - Set name to network interface of Virtual Machine.
                    - C(nic_on_boot) - If I(True) network interface will be set to start on boot.
            sso:
                description:
                    - "I(True) enable Single Sign On by Guest Agent, I(False) to disable it. By default is chosen by oVirt/RHV engine."
                type: bool
            smartcard_enabled:
                description:
                    - "If I(true), use smart card authentication."
                type: bool
            nics:
                description:
                    - List of NICs, which should be attached to Virtual Machine. NIC is described by following dictionary.
                    - C(name) - Name of the NIC.
                    - C(profile_name) - Profile name where NIC should be attached.
                    - C(interface) -  Type of the network interface. One of following I(virtio), I(e1000), I(rtl8139), default is I(virtio).
                    - C(mac_address) - Custom MAC address of the network interface, by default it's obtained from MAC pool.
                    - NOTE - This parameter is used only when C(state) is I(running) or I(present) and is able to only create NICs.
                    - To manage NICs of the VM in more depth please use M(ovirt_nics) module instead.
        version_added: "2.9"
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

- name: Create VM pool from template
  ovirt_vmpool:
    cluster: mycluster
    name: myvmpool
    template: rhel7
    vm_count: 2
    prestarted: 2
    vm_per_user: 1

- name: Remove vmpool, note that all VMs in pool will be stopped and removed
  ovirt_vmpool:
    state: absent
    name: myvmpool

- name: Change Pool Name
  ovirt_vmpool:
    id: 00000000-0000-0000-0000-000000000000
    name: "new_pool_name"

- name: Create vm pool and override the pool values
  ovirt_vmpool:
    cluster: mycluster
    name: vmpool
    template: blank
    vm_count: 2
    prestarted: 1
    vm_per_user: 1
    vm:
      memory: 4GiB
      memory_guaranteed: 4GiB
      memory_max: 10GiB
      comment: vncomment
      cloud_init:
        nic_boot_protocol: static
        nic_ip_address: 10.34.60.86
        nic_netmask: 255.255.252.0
        nic_gateway: 10.34.63.254
        nic_name: eth1
        nic_on_boot: true
        host_name: example.com
        custom_script: |
          write_files:
           - content: |
               Hello, world!
             path: /tmp/greeting.txt
             permissions: '0644'
        user_name: root
        root_password: super_password
      nics:
        - name: nicname
          interface: virtio
          profile_name: network

'''

RETURN = '''
id:
    description: ID of the VM pool which is managed
    returned: On success if VM pool is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
vm_pool:
    description: "Dictionary of all the VM pool attributes. VM pool attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/vm_pool."
    returned: On success if VM pool is found.
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
    check_params,
    check_sdk,
    create_connection,
    equal,
    get_link_name,
    ovirt_full_argument_spec,
    wait,
    convert_to_bytes,
    search_by_name,
)


class VmPoolsModule(BaseModule):
    def __init__(self, *args, **kwargs):
        super(VmPoolsModule, self).__init__(*args, **kwargs)
        self._initialization = None

    def build_entity(self):
        vm = self.param('vm')
        return otypes.VmPool(
            id=self._module.params['id'],
            name=self._module.params['name'],
            description=self._module.params['description'],
            comment=self._module.params['comment'],
            cluster=otypes.Cluster(
                name=self._module.params['cluster']
            ) if self._module.params['cluster'] else None,
            template=otypes.Template(
                name=self._module.params['template']
            ) if self._module.params['template'] else None,
            max_user_vms=self._module.params['vm_per_user'],
            prestarted_vms=self._module.params['prestarted'],
            size=self._module.params['vm_count'],
            type=otypes.VmPoolType(
                self._module.params['type']
            ) if self._module.params['type'] else None,
            vm=self.build_vm(vm) if self._module.params['vm'] else None,
        )

    def build_vm(self, vm):
        return otypes.Vm(
            comment=vm.get('comment'),
            memory=convert_to_bytes(
                vm.get('memory')
            ) if vm.get('memory') else None,
            memory_policy=otypes.MemoryPolicy(
                guaranteed=convert_to_bytes(vm.get('memory_guaranteed')),
                max=convert_to_bytes(vm.get('memory_max')),
            ) if any((
                vm.get('memory_guaranteed'),
                vm.get('memory_max')
            )) else None,
            initialization=self.get_initialization(vm),
            display=otypes.Display(
                smartcard_enabled=vm.get('smartcard_enabled')
            ) if vm.get('smartcard_enabled') is not None else None,
            sso=(
                otypes.Sso(
                    methods=[otypes.Method(id=otypes.SsoMethod.GUEST_AGENT)] if vm.get('sso') else []
                )
            ) if vm.get('sso') is not None else None,
            time_zone=otypes.TimeZone(
                name=vm.get('timezone'),
            ) if vm.get('timezone') else None,
        )

    def get_initialization(self, vm):
        if self._initialization is not None:
            return self._initialization

        sysprep = vm.get('sysprep')
        cloud_init = vm.get('cloud_init')
        cloud_init_nics = vm.get('cloud_init_nics') or []
        if cloud_init is not None:
            cloud_init_nics.append(cloud_init)

        if cloud_init or cloud_init_nics:
            self._initialization = otypes.Initialization(
                nic_configurations=[
                    otypes.NicConfiguration(
                        boot_protocol=otypes.BootProtocol(
                            nic.pop('nic_boot_protocol').lower()
                        ) if nic.get('nic_boot_protocol') else None,
                        name=nic.pop('nic_name', None),
                        on_boot=nic.pop('nic_on_boot', None),
                        ip=otypes.Ip(
                            address=nic.pop('nic_ip_address', None),
                            netmask=nic.pop('nic_netmask', None),
                            gateway=nic.pop('nic_gateway', None),
                        ) if (
                            nic.get('nic_gateway') is not None or
                            nic.get('nic_netmask') is not None or
                            nic.get('nic_ip_address') is not None
                        ) else None,
                    )
                    for nic in cloud_init_nics
                    if (
                        nic.get('nic_gateway') is not None or
                        nic.get('nic_netmask') is not None or
                        nic.get('nic_ip_address') is not None or
                        nic.get('nic_boot_protocol') is not None or
                        nic.get('nic_on_boot') is not None
                    )
                ] if cloud_init_nics else None,
                **cloud_init
            )
        elif sysprep:
            self._initialization = otypes.Initialization(
                **sysprep
            )
        return self._initialization

    def get_vms(self, entity):
        vms = self._connection.system_service().vms_service().list()
        resp = []
        for vm in vms:
            if vm.vm_pool is not None and vm.vm_pool.id == entity.id:
                resp.append(vm)
        return resp

    def post_create(self, entity):
        vm_param = self.param('vm')
        if vm_param is not None and vm_param.get('nics') is not None:
            vms = self.get_vms(entity)
            for vm in vms:
                self.__attach_nics(vm, vm_param)

    def __attach_nics(self, entity, vm_param):
        # Attach NICs to VM, if specified:
        vms_service = self._connection.system_service().vms_service()
        nics_service = vms_service.service(entity.id).nics_service()
        for nic in vm_param.get('nics'):
            if search_by_name(nics_service, nic.get('name')) is None:
                if not self._module.check_mode:
                    nics_service.add(
                        otypes.Nic(
                            name=nic.get('name'),
                            interface=otypes.NicInterface(
                                nic.get('interface', 'virtio')
                            ),
                            vnic_profile=otypes.VnicProfile(
                                id=self.__get_vnic_profile_id(nic),
                            ) if nic.get('profile_name') else None,
                            mac=otypes.Mac(
                                address=nic.get('mac_address')
                            ) if nic.get('mac_address') else None,
                        )
                    )
                self.changed = True

    def __get_vnic_profile_id(self, nic):
        """
        Return VNIC profile ID looked up by it's name, because there can be
        more VNIC profiles with same name, other criteria of filter is cluster.
        """
        vnics_service = self._connection.system_service().vnic_profiles_service()
        clusters_service = self._connection.system_service().clusters_service()
        cluster = search_by_name(clusters_service, self.param('cluster'))
        profiles = [
            profile for profile in vnics_service.list()
            if profile.name == nic.get('profile_name')
        ]
        cluster_networks = [
            net.id for net in self._connection.follow_link(cluster.networks)
        ]
        try:
            return next(
                profile.id for profile in profiles
                if profile.network.id in cluster_networks
            )
        except StopIteration:
            raise Exception(
                "Profile '%s' was not found in cluster '%s'" % (
                    nic.get('profile_name'),
                    self.param('cluster')
                )
            )

    def update_check(self, entity):
        return (
            equal(self._module.params.get('name'), entity.name) and
            equal(self._module.params.get('cluster'), get_link_name(self._connection, entity.cluster)) and
            equal(self._module.params.get('description'), entity.description) and
            equal(self._module.params.get('comment'), entity.comment) and
            equal(self._module.params.get('vm_per_user'), entity.max_user_vms) and
            equal(self._module.params.get('prestarted'), entity.prestarted_vms) and
            equal(self._module.params.get('vm_count'), entity.size)
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        id=dict(default=None),
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(required=True),
        template=dict(default=None),
        cluster=dict(default=None),
        description=dict(default=None),
        vm=dict(default=None, type='dict'),
        comment=dict(default=None),
        vm_per_user=dict(default=None, type='int'),
        prestarted=dict(default=None, type='int'),
        vm_count=dict(default=None, type='int'),
        type=dict(default=None, choices=['automatic', 'manual']),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    check_sdk(module)
    check_params(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        vm_pools_service = connection.system_service().vm_pools_service()
        vm_pools_module = VmPoolsModule(
            connection=connection,
            module=module,
            service=vm_pools_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = vm_pools_module.create()

            # Wait for all VM pool VMs to be created:
            if module.params['wait']:
                vms_service = connection.system_service().vms_service()
                for vm in vms_service.list(search='pool=%s' % module.params['name']):
                    wait(
                        service=vms_service.service(vm.id),
                        condition=lambda vm: vm.status in [otypes.VmStatus.DOWN, otypes.VmStatus.UP],
                        timeout=module.params['timeout'],
                    )

        elif state == 'absent':
            ret = vm_pools_module.remove()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
