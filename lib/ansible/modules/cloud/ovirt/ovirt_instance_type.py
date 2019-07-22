#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ovirt_instance_type
short_description: Module to manage Instance Types in oVirt/RHV
version_added: "2.8"
author:
- Martin Necas (@mnecas)
- Ondra Machacek (@machacekondra)
description:
    - This module manages whole lifecycle of the Instance Type in oVirt/RHV.
options:
    name:
        description:
            - Name of the Instance Type to manage.
            - If instance type don't exists C(name) is required. Otherwise C(id) or C(name) can be used.
    id:
        description:
            - ID of the Instance Type to manage.
    state:
        description:
            - Should the Instance Type be present/absent.
            - I(present) state will create/update instance type and don't change its state if it already exists.
        choices: [ absent, present ]
        default: present
    memory:
        description:
            - Amount of memory of the Instance Type. Prefix uses IEC 60027-2 standard (for example 1GiB, 1024MiB).
            - Default value is set by engine.
    memory_guaranteed:
        description:
            - Amount of minimal guaranteed memory of the Instance Type.
              Prefix uses IEC 60027-2 standard (for example 1GiB, 1024MiB).
            - C(memory_guaranteed) parameter can't be lower than C(memory) parameter.
            - Default value is set by engine.
    nics:
        description:
            - List of NICs, which should be attached to Virtual Machine. NIC is described by following dictionary.
            - C(name) - Name of the NIC.
            - C(profile_name) - Profile name where NIC should be attached.
            - C(interface) -  Type of the network interface. One of following I(virtio), I(e1000), I(rtl8139), default is I(virtio).
            - C(mac_address) - Custom MAC address of the network interface, by default it's obtained from MAC pool.
            - NOTE - This parameter is used only when C(state) is I(running) or I(present) and is able to only create NICs.
              To manage NICs of the instance type in more depth please use M(ovirt_nics) module instead.
    memory_max:
        description:
            - Upper bound of instance type memory up to which memory hot-plug can be performed.
              Prefix uses IEC 60027-2 standard (for example 1GiB, 1024MiB).
            - Default value is set by engine.
    cpu_cores:
        description:
            - Number of virtual CPUs cores of the Instance Type.
            - Default value is set by oVirt/RHV engine.
    cpu_sockets:
        description:
            - Number of virtual CPUs sockets of the Instance Type.
            - Default value is set by oVirt/RHV engine.
    cpu_threads:
        description:
            - Number of virtual CPUs sockets of the Instance Type.
            - Default value is set by oVirt/RHV engine.
    operating_system:
        description:
            - Operating system of the Instance Type.
            - Default value is set by oVirt/RHV engine.
            - "Possible values: debian_7, freebsd, freebsdx64, other, other_linux,
               other_linux_ppc64, other_ppc64, rhel_3, rhel_4, rhel_4x64, rhel_5, rhel_5x64,
               rhel_6, rhel_6x64, rhel_6_ppc64, rhel_7x64, rhel_7_ppc64, sles_11, sles_11_ppc64,
               ubuntu_12_04, ubuntu_12_10, ubuntu_13_04, ubuntu_13_10, ubuntu_14_04, ubuntu_14_04_ppc64,
               windows_10, windows_10x64, windows_2003, windows_2003x64, windows_2008, windows_2008x64,
               windows_2008r2x64, windows_2008R2x64, windows_2012x64, windows_2012R2x64, windows_7,
               windows_7x64, windows_8, windows_8x64, windows_xp"
    boot_devices:
        description:
            - List of boot devices which should be used to boot. For example C([ cdrom, hd ]).
            - Default value is set by oVirt/RHV engine.
        choices: [ cdrom, hd, network ]
    serial_console:
        description:
            - "I(True) enable VirtIO serial console, I(False) to disable it. By default is chosen by oVirt/RHV engine."
        type: bool
    usb_support:
        description:
            - "I(True) enable USB support, I(False) to disable it. By default is chosen by oVirt/RHV engine."
        type: bool
    high_availability:
        description:
            - If I(yes) Instance Type will be set as highly available.
            - If I(no) Instance Type won't be set as highly available.
            - If no value is passed, default value is set by oVirt/RHV engine.
        type: bool
    high_availability_priority:
        description:
            - Indicates the priority of the instance type inside the run and migration queues.
              Instance Type with higher priorities will be started and migrated before instance types with lower
              priorities. The value is an integer between 0 and 100. The higher the value, the higher the priority.
            - If no value is passed, default value is set by oVirt/RHV engine.
    watchdog:
        description:
            - "Assign watchdog device for the instance type."
            - "Watchdogs is a dictionary which can have following values:"
            - "C(model) - Model of the watchdog device. For example: I(i6300esb), I(diag288) or I(null)."
            - "C(action) - Watchdog action to be performed when watchdog is triggered. For example: I(none), I(reset), I(poweroff), I(pause) or I(dump)."
    host:
        description:
            - Specify host where Instance Type should be running. By default the host is chosen by engine scheduler.
            - This parameter is used only when C(state) is I(running) or I(present).
    graphical_console:
        description:
            - "Assign graphical console to the instance type."
            - "Graphical console is a dictionary which can have following values:"
            - "C(headless_mode) - If I(true) disable the graphics console for this instance type."
            - "C(protocol) - Graphical protocol, a list of I(spice), I(vnc), or both."
    description:
        description:
            - "Description of the instance type."
    cpu_mode:
        description:
            - "CPU mode of the instance type. It can be some of the following: I(host_passthrough), I(host_model) or I(custom)."
            - "For I(host_passthrough) CPU type you need to set C(placement_policy) to I(pinned)."
            - "If no value is passed, default value is set by oVirt/RHV engine."
    rng_device:
        description:
            - "Random number generator (RNG). You can choose of one the following devices I(urandom), I(random) or I(hwrng)."
            - "In order to select I(hwrng), you must have it enabled on cluster first."
            - "/dev/urandom is used for cluster version >= 4.1, and /dev/random for cluster version <= 4.0"
    rng_bytes:
        description:
            - "Number of bytes allowed to consume per period."
    rng_period:
        description:
            - "Duration of one period in milliseconds."
    placement_policy:
        description:
            - "The configuration of the instance type's placement policy."
            - "Placement policy can be one of the following values:"
            - "C(migratable) - Allow manual and automatic migration."
            - "C(pinned) - Do not allow migration."
            - "C(user_migratable) - Allow manual migration only."
            - "If no value is passed, default value is set by oVirt/RHV engine."
    cpu_pinning:
        description:
            - "CPU Pinning topology to map instance type CPU to host CPU."
            - "CPU Pinning topology is a list of dictionary which can have following values:"
            - "C(cpu) - Number of the host CPU."
            - "C(vcpu) - Number of the instance type CPU."
    soundcard_enabled:
        description:
            - "If I(true), the sound card is added to the instance type."
        type: bool
    smartcard_enabled:
        description:
            - "If I(true), use smart card authentication."
        type: bool
    virtio_scsi:
        description:
            - "If I(true), virtio scsi will be enabled."
        type: bool
    io_threads:
        description:
            - "Number of IO threads used by instance type. I(0) means IO threading disabled."
    ballooning_enabled:
        description:
            - "If I(true), use memory ballooning."
            - "Memory balloon is a guest device, which may be used to re-distribute / reclaim the host memory
               based on instance type needs in a dynamic way. In this way it's possible to create memory over commitment states."
        type: bool
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create instance type
- name: Create instance type
  ovirt_instance_type:
    state: present
    name: myit
    rng_device: hwrng
    rng_bytes: 200
    rng_period: 200
    soundcard_enabled: true
    virtio_scsi: true
    boot_devices:
      - network

# Remove instance type
- ovirt_instance_type:
    state: absent
    name: myit


# Create instance type with predefined memory and cpu limits.
- ovirt_instance_type:
    state: present
    name: myit
    memory: 2GiB
    cpu_cores: 2
    cpu_sockets: 2
    nics:
      - name: nic1

# Enable usb suppport and serial console
- ovirt_instance_type:
    name: myit
    usb_support: True
    serial_console: True

# Use graphical console with spice and vnc
- name: Create a instance type that has the console configured for both Spice and VNC
  ovirt_instance_type:
    name: myit
    graphical_console:
      protocol:
        - spice
        - vnc
'''


RETURN = '''

id:
    description: ID of the instance type which is managed
    returned: On success if instance type is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
instancetype:
    description: "Dictionary of all the instance type attributes. instance type attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/instance_type."
    returned: On success if instance type is found.
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
import traceback

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
        # Attach NICs to instance type, if specified:
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
        self.changed = self.__attach_nics(entity)
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
            equal(self.param('virtio_scsi'), getattr(entity, 'smartcard_enabled', False)) and
            equal(self.param('high_availability'), entity.high_availability.enabled) and
            equal(self.param('high_availability_priority'), entity.high_availability.priority) and
            equal(self.param('boot_devices'), [str(dev) for dev in getattr(entity.os.boot, 'devices', [])]) and
            equal(self.param('description'), entity.description) and
            equal(self.param('rng_device'), str(entity.rng_device.source) if entity.rng_device else None) and
            equal(self.param('rng_bytes'), entity.rng_device.rate.bytes if entity.rng_device else None) and
            equal(self.param('rng_period'), entity.rng_device.rate.period if entity.rng_device else None) and
            equal(self.param('placement_policy'), str(entity.placement_policy.affinity) if entity.placement_policy else None)
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(type='str', default='present',
                   choices=['absent', 'present']),
        name=dict(type='str'),
        id=dict(type='str'),
        memory=dict(type='str'),
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
        nics=dict(type='list', default=[]),
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
