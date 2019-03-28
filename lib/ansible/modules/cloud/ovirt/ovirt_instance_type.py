#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.ovirt import (
    BaseModule,
    check_params,
    check_sdk,
    convert_to_bytes,
    create_connection,
    equal,
    get_dict_of_struct,
    get_entity,
    get_link_name,
    get_id_by_name,
    ovirt_full_argument_spec,
    search_by_attributes,
    search_by_name,
    wait,
)
from ansible.module_utils.basic import AnsibleModule
import traceback
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ovirt_vm
short_description: Module to manage Virtual Machines in oVirt/RHV
version_added: "2.2"
author:
- Ondra Machacek (@machacekondra)
description:
    - This module manages whole lifecycle of the Virtual Machine(VM) in oVirt/RHV.
    - Since VM can hold many states in oVirt/RHV, this see notes to see how the states of the VM are handled.
options:
    name:
        description:
            - Name of the Virtual Machine to manage.
            - If VM don't exists C(name) is required. Otherwise C(id) or C(name) can be used.
    id:
        description:
            - ID of the Virtual Machine to manage.
    graphical_console:
        description:
            - "Assign graphical console to the virtual machine."
            - "Graphical console is a dictionary which can have following values:"
            - "C(headless_mode) - If I(true) disable the graphics console for this virtual machine."
            - "C(protocol) - Graphical protocol, a list of I(spice), I(vnc), or both."
        version_added: "2.5"
    state:
        description:
            - Should the Virtual Machine be running/stopped/present/absent/suspended/next_run/registered/exported.
              When C(state) is I(registered) and the unregistered VM's name
              belongs to an already registered in engine VM in the same DC
              then we fail to register the unregistered template.
            - I(present) state will create/update VM and don't change its state if it already exists.
            - I(running) state will create/update VM and start it.
            - I(next_run) state updates the VM and if the VM has next run configuration it will be rebooted.
            - Please check I(notes) to more detailed description of states.
            - I(exported) state will export the VM to export domain or as OVA.
            - I(registered) is supported since 2.4.
        choices: [ absent, next_run, present, registered, running, stopped, suspended, exported ]
        default: present
    placement_policy:
        description:
            - "The configuration of the virtual machine's placement policy."
            - "Placement policy can be one of the following values:"
            - "C(migratable) - Allow manual and automatic migration."
            - "C(pinned) - Do not allow migration."
            - "C(user_migratable) - Allow manual migration only."
            - "If no value is passed, default value is set by oVirt/RHV engine."
        version_added: "2.5"
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

- name: Creates a new Virtual Machine from template named 'rhel7_template'
  ovirt_vm:
    state: present
    name: myvm
    template: rhel7_template

'''


RETURN = '''
'''

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass


class InstanceTypeModule(BaseModule):
    def build_entity(self):
        return otypes.InstanceType(
            id=self.param('id'),
            name=self.param('name'),
            console=(
                otypes.Console(enabled=self.param('serial_console'))
            ) if self.param('serial_console') is not None else None,
            usb=(
                otypes.Usb(enabled=self.param('usb_support'))
            ) if self.param('usb_support') is not None else None,
            high_availability=otypes.HighAvailability(
                enabled=self.param('high_availability'),
                priority=self.param('high_availability_priority'),
            ) if self.param('high_availability') is not None or self.param('high_availability_priority') else None,
            cpu=otypes.Cpu(
                topology=otypes.CpuTopology(
                    cores=self.param('cpu_cores'),
                    sockets=self.param('cpu_sockets'),
                    threads=self.param('cpu_threads'),
                ) if any((
                    self.param('cpu_cores'),
                    self.param('cpu_sockets'),
                    self.param('cpu_threads')
                )) else None,
                cpu_tune=otypes.CpuTune(
                    vcpu_pins=[
                        otypes.VcpuPin(vcpu=int(pin['vcpu']), cpu_set=str(pin['cpu'])) for pin in self.param('cpu_pinning')
                    ],
                ) if self.param('cpu_pinning') else None,
                mode=otypes.CpuMode(self.param('cpu_mode')) if self.param(
                    'cpu_mode') else None,
            ) if any((
                self.param('cpu_cores'),
                self.param('cpu_sockets'),
                self.param('cpu_threads'),
                self.param('cpu_mode'),
                self.param('cpu_pinning')
            )) else None,
            os=otypes.OperatingSystem(
                type=self.param('operating_system'),
                boot=otypes.Boot(
                    devices=[
                        otypes.BootDevice(dev) for dev in self.param('boot_devices')
                    ],
                ) if self.param('boot_devices') else None
            ),
            rng_device=otypes.RngDevice(
                source=otypes.RngSource(self.param('rng_device')),
                rate=otypes.Rate(
                    bytes=self.param('rng_bytes'),
                    period=self.param('rng_period')
                )
            ) if self.param('rng_device') else None,
            memory=convert_to_bytes(
                self.param('memory')
            ) if self.param('memory') else None,
            virtio_scsi=otypes.VirtioScsi(
                enabled=self.param('virtio_scsi')
            ) if self.param('virtio_scsi') else None,
            memory_policy=otypes.MemoryPolicy(
                guaranteed=convert_to_bytes(self.param('memory_guaranteed')),
                ballooning=self.param('ballooning_enabled'),
                max=convert_to_bytes(self.param('memory_max')),
            ) if any((
                self.param('memory_guaranteed'),
                self.param('ballooning_enabled') is not None,
                self.param('memory_max')
            )) else None,
            description=self.param('description'),
            placement_policy=otypes.VmPlacementPolicy(
                affinity=otypes.VmAffinity(self.param('placement_policy')),
                hosts=[
                    otypes.Host(name=self.param('host')),
                ] if self.param('host') else None,
            ) if self.param('placement_policy') else None,
            soundcard_enabled=self.param('soundcard_enabled'),
            display=otypes.Display(
                smartcard_enabled=self.param('smartcard_enabled')
            ) if self.param('smartcard_enabled') is not None else None,
            io=otypes.Io(
                threads=self.param('io_threads'),
            ) if self.param('io_threads') is not None else None,
        )

    def __attach_watchdog(self, entity):
        watchdogs_service = self._service.service(entity.id).watchdogs_service()
        watchdog = self.param('watchdog')
        if watchdog is not None:
            current_watchdog = next(iter(watchdogs_service.list()), None)
            if watchdog.get('model') is None and current_watchdog:
                watchdogs_service.watchdog_service(current_watchdog.id).remove()
                return True
            elif watchdog.get('model') is not None and current_watchdog is None:
                watchdogs_service.add( 
                    otypes.Watchdog(
                        model=otypes.WatchdogModel(watchdog.get('model').lower()),
                        action=otypes.WatchdogAction(watchdog.get('action')),
                    )
                )
                return True
            elif current_watchdog is not None:
                if (
                    str(current_watchdog.model).lower() != watchdog.get('model').lower() or
                    str(current_watchdog.action).lower() != watchdog.get('action').lower()
                ):
                    watchdogs_service.watchdog_service(current_watchdog.id).update(
                        otypes.Watchdog(
                            model=otypes.WatchdogModel(watchdog.get('model')),
                            action=otypes.WatchdogAction(watchdog.get('action')),
                        )
                    )
                    return True
        return False
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

    def __attach_nics(self, entity):
        # Attach NICs to VM, if specified:
        nics_service = self._service.service(entity.id).nics_service()
        for nic in self.param('nics'):
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

    def __attach_graphical_console(self, entity):
        graphical_console = self.param('graphical_console')
        if not graphical_console:
            return False

        it_service = self._service.instance_type_service(entity.id)
        gcs_service = it_service.graphics_consoles_service()
        graphical_consoles = gcs_service.list()
        # Remove all graphical consoles if there are any:
        if bool(graphical_console.get('headless_mode')):
            if not self._module.check_mode:
                for gc in graphical_consoles:
                    gcs_service.console_service(gc.id).remove()
            return len(graphical_consoles) > 0

        # If there are not gc add any gc to be added:
        protocol = graphical_console.get('protocol')
        if isinstance(protocol, str):
            protocol = [protocol]
        
        current_protocols = [str(gc.protocol) for gc in graphical_consoles]
        if not current_protocols:
            if not self._module.check_mode:
                for p in protocol:
                    gcs_service.add(
                        otypes.GraphicsConsole(
                            protocol=otypes.GraphicsType(p),
                        )
                    )
            return True

        # Update consoles:
        if sorted(protocol) != sorted(current_protocols):
            if not self._module.check_mode:
                for gc in graphical_consoles:
                    gcs_service.console_service(gc.id).remove()
                for p in protocol:
                    gcs_service.add(
                        otypes.GraphicsConsole(
                            protocol=otypes.GraphicsType(p),
                        )
                    )
            return True

    def post_update(self, entity):
        self.post_present(entity.id)

    def post_present(self, entity_id):
        entity = self._service.service(entity_id).get()
        #self.__attach_nics(entity)
        self.changed = self.__attach_watchdog(entity)
        self.changed = self.__attach_graphical_console(entity)

    def update_check(self, entity):
        cpu_mode = getattr(entity.cpu, 'mode')
        it_display = entity.display
        return (
            not self.param('kernel_params_persist') and
            equal(convert_to_bytes(self.param('memory_guaranteed')), entity.memory_policy.guaranteed) and
            equal(convert_to_bytes(self.param('memory_max')), entity.memory_policy.max) and
            equal(self.param('cpu_cores'), entity.cpu.topology.cores) and
            equal(self.param('cpu_sockets'), entity.cpu.topology.sockets) and
            equal(self.param('cpu_threads'), entity.cpu.topology.threads) and
            equal(self.param('cpu_mode'), str(cpu_mode) if cpu_mode else None) and
            equal(self.param('type'), str(entity.type)) and
            equal(self.param('name'), str(entity.name)) and
            equal(self.param('operating_system'), str(entity.os.type)) and
            equal(self.param('soundcard_enabled'), entity.soundcard_enabled) and
            equal(self.param('smartcard_enabled'), getattr(it_display, 'smartcard_enabled', False)) and
            equal(self.param('io_threads'), entity.io.threads) and
            equal(self.param('ballooning_enabled'), entity.memory_policy.ballooning) and
            equal(self.param('serial_console'), getattr(entity.console, 'enabled', None)) and
            equal(self.param('usb_support'), entity.usb.enabled) and
            equal(self.param('virtio_scsi'), entity.virtio_scsi.enabled) and
            equal(self.param('high_availability'), entity.high_availability.enabled) and
            equal(self.param('high_availability_priority'), entity.high_availability.priority) and
            equal(self.param('boot_devices'), [str(dev) for dev in getattr(entity.os.boot, 'devices', [])]) and
            equal(self.param('description'), entity.description) and
            equal(self.param('rng_device'), str(entity.rng_device.source) if entity.rng_device else None) and
            equal(self.param('rng_bytes'), entity.rng_device.rate.bytes if entity.rng_device else None) and
            equal(self.param('rng_period'), entity.rng_device.rate.period if entity.rng_device else None) and
            equal(self.param('placement_policy'), str(
                entity.placement_policy.affinity) if entity.placement_policy else None)
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(type='str', default='present',
                   choices=['absent', 'present']),
        name=dict(type='str'),
        id=dict(type='str'),
        memory=dict(type='str', default='256MiB'),
        memory_guaranteed=dict(type='str'),
        memory_max=dict(type='str'),
        cpu_sockets=dict(type='int'),
        cpu_cores=dict(type='int'),
        cpu_threads=dict(type='int'),
        operating_system=dict(type='str'),
        boot_devices=dict(type='list', choices=['cdrom', 'hd', 'network']),
        serial_console=dict(type='bool'),
        usb_support=dict(type='bool'),
        high_availability=dict(type='bool'),
        high_availability_priority=dict(type='int'),
        watchdog=dict(type='dict'),
        host=dict(type='str'),
        graphical_console=dict(type='dict'),
        description=dict(type='str'),
        cpu_mode=dict(type='str'),
        rng_device=dict(type='str'),
        rng_bytes=dict(type='int', default=None),
        rng_period=dict(type='int', default=None),
        placement_policy=dict(type='str'),
        cpu_pinning=dict(type='list'),
        soundcard_enabled=dict(type='bool', default=None),
        virtio_scsi=dict(type='bool', default=None),
        smartcard_enabled=dict(type='bool', default=None),
        io_threads=dict(type='int', default=None),
        ballooning_enabled=dict(type='bool', default=None),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['id', 'name']],
    )

    check_sdk(module)
    check_params(module)

    try:
        state = module.params['state']
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        its_service = connection.system_service().instance_types_service()
        its_module = InstanceTypeModule(
            connection=connection,
            module=module,
            service=its_service,
        )
        it = its_module.search_entity()

        if state == 'present':

            ret = its_module.create(
                entity=it
            )

            its_module.post_present(ret['id'])
            ret['changed'] = its_module.changed
        elif state == 'absent':
            ret = its_module.remove()
        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
