#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ovirt_vms
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
    state:
        description:
            - Should the Virtual Machine be running/stopped/present/absent/suspended/next_run/registered.
              When C(state) is I(registered) and the unregistered VM's name
              belongs to an already registered in engine VM in the same DC
              then we fail to register the unregistered template.
            - I(present) state will create/update VM and don't change its state if it already exists.
            - I(running) state will create/update VM and start it.
            - I(next_run) state updates the VM and if the VM has next run configuration it will be rebooted.
            - Please check I(notes) to more detailed description of states.
            - I(registered) is supported since 2.4.
        choices: [ absent, next_run, present, registered, running, stopped, suspended ]
        default: present
    cluster:
        description:
            - Name of the cluster, where Virtual Machine should be created.
            - Required if creating VM.
    allow_partial_import:
        description:
            - Boolean indication whether to allow partial registration of Virtual Machine when C(state) is registered.
        version_added: "2.4"
    template:
        description:
            - Name of the template, which should be used to create Virtual Machine.
            - Required if creating VM.
            - If template is not specified and VM doesn't exist, VM will be created from I(Blank) template.
    template_version:
        description:
            - Version number of the template to be used for VM.
            - By default the latest available version of the template is used.
        version_added: "2.3"
    use_latest_template_version:
        description:
            - Specify if latest template version should be used, when running a stateless VM.
            - If this parameter is set to I(yes) stateless VM is created.
        type: bool
        version_added: "2.3"
    storage_domain:
        description:
            - Name of the storage domain where all template disks should be created.
            - This parameter is considered only when C(template) is provided.
            - IMPORTANT - This parameter is not idempotent, if the VM exists and you specfiy different storage domain,
              disk won't move.
        version_added: "2.4"
    disk_format:
        description:
            - Specify format of the disk.
            - If C(cow) format is used, disk will by created as sparse, so space will be allocated for the volume as needed, also known as I(thin provision).
            - If C(raw) format is used, disk storage will be allocated right away, also known as I(preallocated).
            - Note that this option isn't idempotent as it's not currently possible to change format of the disk via API.
            - This parameter is considered only when C(template) and C(storage domain) is provided.
        choices: [ cow, raw ]
        default: cow
        version_added: "2.4"
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
    cpu_shares:
        description:
            - Set a CPU shares for this Virtual Machine.
            - Default value is set by oVirt/RHV engine.
    cpu_cores:
        description:
            - Number of virtual CPUs cores of the Virtual Machine.
            - Default value is set by oVirt/RHV engine.
    cpu_sockets:
        description:
            - Number of virtual CPUs sockets of the Virtual Machine.
            - Default value is set by oVirt/RHV engine.
    type:
        description:
            - Type of the Virtual Machine.
            - Default value is set by oVirt/RHV engine.
        choices: [ desktop, server ]
    operating_system:
        description:
            - Operating system of the Virtual Machine.
            - Default value is set by oVirt/RHV engine.
        choices:
        - debian_7
        - freebsd
        - freebsdx64
        - other
        - other_linux
        - other_linux_ppc64
        - other_ppc64
        - rhel_3
        - rhel_4
        - rhel_4x64
        - rhel_5
        - rhel_5x64
        - rhel_6
        - rhel_6x64
        - rhel_6_ppc64
        - rhel_7x64
        - rhel_7_ppc64
        - sles_11
        - sles_11_ppc64
        - ubuntu_12_04
        - ubuntu_12_10
        - ubuntu_13_04
        - ubuntu_13_10
        - ubuntu_14_04
        - ubuntu_14_04_ppc64
        - windows_10
        - windows_10x64
        - windows_2003
        - windows_2003x64
        - windows_2008
        - windows_2008x64
        - windows_2008r2x64
        - windows_2008R2x64
        - windows_2012x64
        - windows_2012R2x64
        - windows_7
        - windows_7x64
        - windows_8
        - windows_8x64
        - windows_xp
    boot_devices:
        description:
            - List of boot devices which should be used to boot. For example C([ cdrom, hd ]).
            - Default value is set by oVirt/RHV engine.
        choices: [ cdrom, hd, network ]
    host:
        description:
            - Specify host where Virtual Machine should be running. By default the host is chosen by engine scheduler.
            - This parameter is used only when C(state) is I(running) or I(present).
    high_availability:
        description:
            - If I(yes) Virtual Machine will be set as highly available.
            - If I(no) Virtual Machine won't be set as highly available.
            - If no value is passed, default value is set by oVirt/RHV engine.
        type: bool
    lease:
        description:
            - Name of the storage domain this virtual machine lease reside on.
            - NOTE - Supported since oVirt 4.1.
        version_added: "2.4"
    delete_protected:
        description:
            - If I(yes) Virtual Machine will be set as delete protected.
            - If I(no) Virtual Machine won't be set as delete protected.
            - If no value is passed, default value is set by oVirt/RHV engine.
    stateless:
        description:
            - If I(yes) Virtual Machine will be set as stateless.
            - If I(no) Virtual Machine will be unset as stateless.
            - If no value is passed, default value is set by oVirt/RHV engine.
    clone:
        description:
            - If I(yes) then the disks of the created virtual machine will be cloned and independent of the template.
            - This parameter is used only when C(state) is I(running) or I(present) and VM didn't exist before.
        type: bool
        default: 'no'
    clone_permissions:
        description:
            - If I(yes) then the permissions of the template (only the direct ones, not the inherited ones)
              will be copied to the created virtual machine.
            - This parameter is used only when C(state) is I(running) or I(present) and VM didn't exist before.
        type: bool
        default: 'no'
    cd_iso:
        description:
            - ISO file from ISO storage domain which should be attached to Virtual Machine.
            - If you pass empty string the CD will be ejected from VM.
            - If used with C(state) I(running) or I(present) and VM is running the CD will be attached to VM.
            - If used with C(state) I(running) or I(present) and VM is down the CD will be attached to VM persistently.
    force:
        description:
            - Please check to I(Synopsis) to more detailed description of force parameter, it can behave differently
              in different situations.
        type: bool
        default: 'no'
    nics:
        description:
            - List of NICs, which should be attached to Virtual Machine. NIC is described by following dictionary.
            - C(name) - Name of the NIC.
            - C(profile_name) - Profile name where NIC should be attached.
            - C(interface) -  Type of the network interface. One of following I(virtio), I(e1000), I(rtl8139), default is I(virtio).
            - C(mac_address) - Custom MAC address of the network interface, by default it's obtained from MAC pool.
            - NOTE - This parameter is used only when C(state) is I(running) or I(present) and is able to only create NICs.
              To manage NICs of the VM in more depth please use M(ovirt_nics) module instead.
    disks:
        description:
            - List of disks, which should be attached to Virtual Machine. Disk is described by following dictionary.
            - C(name) - Name of the disk. Either C(name) or C(id) is reuqired.
            - C(id) - ID of the disk. Either C(name) or C(id) is reuqired.
            - C(interface) - Interface of the disk, either I(virtio) or I(IDE), default is I(virtio).
            - C(bootable) - I(True) if the disk should be bootable, default is non bootable.
            - C(activate) - I(True) if the disk should be activated, default is activated.
            - NOTE - This parameter is used only when C(state) is I(running) or I(present) and is able to only attach disks.
              To manage disks of the VM in more depth please use M(ovirt_disks) module instead.
    sysprep:
        description:
            - Dictionary with values for Windows Virtual Machine initialization using sysprep.
            - C(host_name) - Hostname to be set to Virtual Machine when deployed.
            - C(active_directory_ou) - Active Directory Organizational Unit, to be used for login of user.
            - C(org_name) - Organization name to be set to Windows Virtual Machine.
            - C(domain) - Domain to be set to Windows Virtual Machine.
            - C(timezone) - Timezone to be set to Windows Virtual Machine.
            - C(ui_language) - UI language of the Windows Virtual Machine.
            - C(system_locale) - System localization of the Windows Virtual Machine.
            - C(input_locale) - Input localization of the Windows Virtual Machine.
            - C(windows_license_key) - License key to be set to Windows Virtual Machine.
            - C(user_name) - Username to be used for set password to Windows Virtual Machine.
            - C(root_password) - Password to be set for username to Windows Virtual Machine.
    cloud_init:
        description:
            - Dictionary with values for Unix-like Virtual Machine initialization using cloud init.
            - C(host_name) - Hostname to be set to Virtual Machine when deployed.
            - C(timezone) - Timezone to be set to Virtual Machine when deployed.
            - C(user_name) - Username to be used to set password to Virtual Machine when deployed.
            - C(root_password) - Password to be set for user specified by C(user_name) parameter.
            - C(authorized_ssh_keys) - Use this SSH keys to login to Virtual Machine.
            - C(regenerate_ssh_keys) - If I(True) SSH keys will be regenerated on Virtual Machine.
            - C(custom_script) - Cloud-init script which will be executed on Virtual Machine when deployed.
            - C(dns_servers) - DNS servers to be configured on Virtual Machine.
            - C(dns_search) - DNS search domains to be configured on Virtual Machine.
            - C(nic_boot_protocol) - Set boot protocol of the network interface of Virtual Machine. Can be one of C(none), C(dhcp) or C(static).
            - C(nic_ip_address) - If boot protocol is static, set this IP address to network interface of Virtual Machine.
            - C(nic_netmask) - If boot protocol is static, set this netmask to network interface of Virtual Machine.
            - C(nic_gateway) - If boot protocol is static, set this gateway to network interface of Virtual Machine.
            - C(nic_name) - Set name to network interface of Virtual Machine.
            - C(nic_on_boot) - If I(True) network interface will be set to start on boot.
    cloud_init_nics:
        description:
            - List of dictionaries representing network interafaces to be setup by cloud init.
            - This option is used, when user needs to setup more network interfaces via cloud init.
            - If one network interface is enough, user should use C(cloud_init) I(nic_*) parameters. C(cloud_init) I(nic_*) parameters
              are merged with C(cloud_init_nics) parameters.
            - Dictionary can contain following values.
            - C(nic_boot_protocol) - Set boot protocol of the network interface of Virtual Machine. Can be one of C(none), C(dhcp) or C(static).
            - C(nic_ip_address) - If boot protocol is static, set this IP address to network interface of Virtual Machine.
            - C(nic_netmask) - If boot protocol is static, set this netmask to network interface of Virtual Machine.
            - C(nic_gateway) - If boot protocol is static, set this gateway to network interface of Virtual Machine.
            - C(nic_name) - Set name to network interface of Virtual Machine.
            - C(nic_on_boot) - If I(True) network interface will be set to start on boot.
        version_added: "2.3"
    kernel_path:
        description:
            - Path to a kernel image used to boot the virtual machine.
            - Kernel image must be stored on either the ISO domain or on the host's storage.
        version_added: "2.3"
    initrd_path:
        description:
            - Path to an initial ramdisk to be used with the kernel specified by C(kernel_path) option.
            - Ramdisk image must be stored on either the ISO domain or on the host's storage.
        version_added: "2.3"
    kernel_params:
        description:
            - Kernel command line parameters (formatted as string) to be used with the kernel specified by C(kernel_path) option.
        version_added: "2.3"
    instance_type:
        description:
            - Name of virtual machine's hardware configuration.
            - By default no instance type is used.
        version_added: "2.3"
    description:
        description:
            - Description of the Virtual Machine.
        version_added: "2.3"
    comment:
        description:
            - Comment of the Virtual Machine.
        version_added: "2.3"
    timezone:
        description:
            - Sets time zone offset of the guest hardware clock.
            - For example C(Etc/GMT)
        version_added: "2.3"
    serial_policy:
        description:
            - Specify a serial number policy for the Virtual Machine.
            - Following options are supported.
            - C(vm) - Sets the Virtual Machine's UUID as its serial number.
            - C(host) - Sets the host's UUID as the Virtual Machine's serial number.
            - C(custom) - Allows you to specify a custom serial number in C(serial_policy_value).
        version_added: "2.3"
    serial_policy_value:
        description:
            - Allows you to specify a custom serial number.
            - This parameter is used only when C(serial_policy) is I(custom).
        version_added: "2.3"
    vmware:
        description:
            - Dictionary of values to be used to connect to VMware and import
              a virtual machine to oVirt.
            - Dictionary can contain following values.
            - C(username) - The username to authenticate against the VMware.
            - C(password) - The password to authenticate against the VMware.
            - C(url) - The URL to be passed to the I(virt-v2v) tool for conversion.
              For example I(vpx://wmware_user@vcenter-host/DataCenter/Cluster/esxi-host?no_verify=1)
            - C(drivers_iso) - The name of the ISO containing drivers that can
              be used during the I(virt-v2v) conversion process.
            - C(sparse) - Specifies the disk allocation policy of the resulting
              virtual machine. I(true) for sparse, I(false) for preallocated.
              Default value is I(true).
            - C(storage_domain) - Specifies the target storage domain for
              converted disks. This is required parameter.
        version_added: "2.3"
    xen:
        description:
            - Dictionary of values to be used to connect to XEN and import
              a virtual machine to oVirt.
            - Dictionary can contain following values.
            - C(url) - The URL to be passed to the I(virt-v2v) tool for conversion.
              For example I(xen+ssh://root@zen.server). This is required parameter.
            - C(drivers_iso) - The name of the ISO containing drivers that can
              be used during the I(virt-v2v) conversion process.
            - C(sparse) - Specifies the disk allocation policy of the resulting
              virtual machine. I(true) for sparse, I(false) for preallocated.
              Default value is I(true).
            - C(storage_domain) - Specifies the target storage domain for
              converted disks. This is required parameter.
        version_added: "2.3"
    kvm:
        description:
            - Dictionary of values to be used to connect to kvm and import
              a virtual machine to oVirt.
            - Dictionary can contain following values.
            - C(name) - The name of the KVM virtual machine.
            - C(username) - The username to authenticate against the KVM.
            - C(password) - The password to authenticate against the KVM.
            - C(url) - The URL to be passed to the I(virt-v2v) tool for conversion.
              For example I(qemu:///system). This is required parameter.
            - C(drivers_iso) - The name of the ISO containing drivers that can
              be used during the I(virt-v2v) conversion process.
            - C(sparse) - Specifies the disk allocation policy of the resulting
              virtual machine. I(true) for sparse, I(false) for preallocated.
              Default value is I(true).
            - C(storage_domain) - Specifies the target storage domain for
              converted disks. This is required parameter.
        version_added: "2.3"
notes:
    - If VM is in I(UNASSIGNED) or I(UNKNOWN) state before any operation, the module will fail.
      If VM is in I(IMAGE_LOCKED) state before any operation, we try to wait for VM to be I(DOWN).
      If VM is in I(SAVING_STATE) state before any operation, we try to wait for VM to be I(SUSPENDED).
      If VM is in I(POWERING_DOWN) state before any operation, we try to wait for VM to be I(UP) or I(DOWN). VM can
      get into I(UP) state from I(POWERING_DOWN) state, when there is no ACPI or guest agent running inside VM, or
      if the shutdown operation fails.
      When user specify I(UP) C(state), we always wait to VM to be in I(UP) state in case VM is I(MIGRATING),
      I(REBOOTING), I(POWERING_UP), I(RESTORING_STATE), I(WAIT_FOR_LAUNCH). In other states we run start operation on VM.
      When user specify I(stopped) C(state), and If user pass C(force) parameter set to I(true) we forcibly stop the VM in
      any state. If user don't pass C(force) parameter, we always wait to VM to be in UP state in case VM is
      I(MIGRATING), I(REBOOTING), I(POWERING_UP), I(RESTORING_STATE), I(WAIT_FOR_LAUNCH). If VM is in I(PAUSED) or
      I(SUSPENDED) state, we start the VM. Then we gracefully shutdown the VM.
      When user specify I(suspended) C(state), we always wait to VM to be in UP state in case VM is I(MIGRATING),
      I(REBOOTING), I(POWERING_UP), I(RESTORING_STATE), I(WAIT_FOR_LAUNCH). If VM is in I(PAUSED) or I(DOWN) state,
      we start the VM. Then we suspend the VM.
      When user specify I(absent) C(state), we forcibly stop the VM in any state and remove it.
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

- name: Creates a new Virtual Machine from template named 'rhel7_template'
  ovirt_vms:
    state: present
    name: myvm
    template: rhel7_template

- name: Register VM
  ovirt_vms:
    state: registered
    storage_domain: mystorage
    cluster: mycluster
    name: myvm

- name: Register VM using id
  ovirt_vms:
    state: registered
    storage_domain: mystorage
    cluster: mycluster
    id: 1111-1111-1111-1111

- name: Register VM, allowing partial import
  ovirt_vms:
    state: registered
    storage_domain: mystorage
    allow_partial_import: "True"
    cluster: mycluster
    id: 1111-1111-1111-1111

- name: Creates a stateless VM which will always use latest template version
  ovirt_vms:
    name: myvm
    template: rhel7
    cluster: mycluster
    use_latest_template_version: true

# Creates a new server rhel7 Virtual Machine from Blank template
# on brq01 cluster with 2GiB memory and 2 vcpu cores/sockets
# and attach bootable disk with name rhel7_disk and attach virtio NIC
- ovirt_vms:
    state: present
    cluster: brq01
    name: myvm
    memory: 2GiB
    cpu_cores: 2
    cpu_sockets: 2
    cpu_shares: 1024
    type: server
    operating_system: rhel_7x64
    disks:
      - name: rhel7_disk
        bootable: True
    nics:
      - name: nic1

- name: Run VM with cloud init
  ovirt_vms:
    name: rhel7
    template: rhel7
    cluster: Default
    memory: 1GiB
    high_availability: true
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

- name: Run VM with cloud init, with multiple network interfaces
  ovirt_vms:
    name: rhel7_4
    template: rhel7
    cluster: mycluster
    cloud_init_nics:
    - nic_name: eth0
      nic_boot_protocol: dhcp
      nic_on_boot: true
    - nic_name: eth1
      nic_boot_protocol: static
      nic_ip_address: 10.34.60.86
      nic_netmask: 255.255.252.0
      nic_gateway: 10.34.63.254
      nic_on_boot: true

- name: Run VM with sysprep
  ovirt_vms:
    name: windows2012R2_AD
    template: windows2012R2
    cluster: Default
    memory: 3GiB
    high_availability: true
    sysprep:
      host_name: windowsad.example.com
      user_name: Administrator
      root_password: SuperPassword123

- name: Migrate/Run VM to/on host named 'host1'
  ovirt_vms:
    state: running
    name: myvm
    host: host1

- name: Change VMs CD
  ovirt_vms:
    name: myvm
    cd_iso: drivers.iso

- name: Eject VMs CD
  ovirt_vms:
    name: myvm
    cd_iso: ''

- name: Boot VM from CD
  ovirt_vms:
    name: myvm
    cd_iso: centos7_x64.iso
    boot_devices:
        - cdrom

- name: Stop vm
  ovirt_vms:
    state: stopped
    name: myvm

- name: Upgrade memory to already created VM
  ovirt_vms:
    name: myvm
    memory: 4GiB

- name: Hot plug memory to already created and running VM (VM won't be restarted)
  ovirt_vms:
    name: myvm
    memory: 4GiB

# When change on the VM needs restart of the VM, use next_run state,
# The VM will be updated and rebooted if there are any changes.
# If present state would be used, VM won't be restarted.
- ovirt_vms:
    state: next_run
    name: myvm
    boot_devices:
      - network

- name: Import virtual machine from VMware
  ovirt_vms:
    state: stopped
    cluster: mycluster
    name: vmware_win10
    timeout: 1800
    poll_interval: 30
    vmware:
      url: vpx://user@1.2.3.4/Folder1/Cluster1/2.3.4.5?no_verify=1
      name: windows10
      storage_domain: mynfs
      username: user
      password: password

- name: Create vm from template and create all disks on specific storage domain
  ovirt_vms:
    name: vm_test
    cluster: mycluster
    template: mytemplate
    storage_domain: mynfs
    nics:
    - name: nic1

- name: Remove VM, if VM is running it will be stopped
  ovirt_vms:
    state: absent
    name: myvm
'''


RETURN = '''
id:
    description: ID of the VM which is managed
    returned: On success if VM is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
vm:
    description: "Dictionary of all the VM attributes. VM attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/vm."
    returned: On success if VM is found.
    type: dict
'''
import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
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
    search_by_name,
    wait,
)


class VmsModule(BaseModule):

    def __get_template_with_version(self):
        """
        oVirt/RHV in version 4.1 doesn't support search by template+version_number,
        so we need to list all templates with specific name and then iterate
        through it's version until we find the version we look for.
        """
        template = None
        if self.param('template'):
            templates_service = self._connection.system_service().templates_service()
            templates = templates_service.list(search='name=%s' % self.param('template'))
            if self.param('template_version'):
                templates = [
                    t for t in templates
                    if t.version.version_number == self.param('template_version')
                ]
            if not templates:
                raise ValueError(
                    "Template with name '%s' and version '%s' was not found'" % (
                        self.param('template'),
                        self.param('template_version')
                    )
                )
            template = sorted(templates, key=lambda t: t.version.version_number, reverse=True)[0]

        return template

    def __get_storage_domain_and_all_template_disks(self, template):

        if self.param('template') is None:
            return None

        if self.param('storage_domain') is None:
            return None

        disks = list()

        for att in self._connection.follow_link(template.disk_attachments):
            disks.append(
                otypes.DiskAttachment(
                    disk=otypes.Disk(
                        id=att.disk.id,
                        format=otypes.DiskFormat(self.param('disk_format')),
                        storage_domains=[
                            otypes.StorageDomain(
                                id=get_id_by_name(
                                    self._connection.system_service().storage_domains_service(),
                                    self.param('storage_domain')
                                )
                            )
                        ]
                    )
                )
            )

        return disks

    def build_entity(self):
        template = self.__get_template_with_version()

        disk_attachments = self.__get_storage_domain_and_all_template_disks(template)

        return otypes.Vm(
            id=self.param('id'),
            name=self.param('name'),
            cluster=otypes.Cluster(
                name=self.param('cluster')
            ) if self.param('cluster') else None,
            disk_attachments=disk_attachments,
            template=otypes.Template(
                id=template.id,
            ) if template else None,
            use_latest_template_version=self.param('use_latest_template_version'),
            stateless=self.param('stateless') or self.param('use_latest_template_version'),
            delete_protected=self.param('delete_protected'),
            high_availability=otypes.HighAvailability(
                enabled=self.param('high_availability')
            ) if self.param('high_availability') is not None else None,
            lease=otypes.StorageDomainLease(
                storage_domain=otypes.StorageDomain(
                    id=get_id_by_name(
                        service=self._connection.system_service().storage_domains_service(),
                        name=self.param('lease')
                    )
                )
            ) if self.param('lease') is not None else None,
            cpu=otypes.Cpu(
                topology=otypes.CpuTopology(
                    cores=self.param('cpu_cores'),
                    sockets=self.param('cpu_sockets'),
                )
            ) if (
                self.param('cpu_cores') or self.param('cpu_sockets')
            ) else None,
            cpu_shares=self.param('cpu_shares'),
            os=otypes.OperatingSystem(
                type=self.param('operating_system'),
                boot=otypes.Boot(
                    devices=[
                        otypes.BootDevice(dev) for dev in self.param('boot_devices')
                    ],
                ) if self.param('boot_devices') else None,
            ) if (
                self.param('operating_system') or self.param('boot_devices')
            ) else None,
            type=otypes.VmType(
                self.param('type')
            ) if self.param('type') else None,
            memory=convert_to_bytes(
                self.param('memory')
            ) if self.param('memory') else None,
            memory_policy=otypes.MemoryPolicy(
                guaranteed=convert_to_bytes(self.param('memory_guaranteed')),
            ) if self.param('memory_guaranteed') else None,
            instance_type=otypes.InstanceType(
                id=get_id_by_name(
                    self._connection.system_service().instance_types_service(),
                    self.param('instance_type'),
                ),
            ) if self.param('instance_type') else None,
            description=self.param('description'),
            comment=self.param('comment'),
            time_zone=otypes.TimeZone(
                name=self.param('timezone'),
            ) if self.param('timezone') else None,
            serial_number=otypes.SerialNumber(
                policy=otypes.SerialNumberPolicy(self.param('serial_policy')),
                value=self.param('serial_policy_value'),
            ) if (
                self.param('serial_policy') is not None or
                self.param('serial_policy_value') is not None
            ) else None,
        )

    def update_check(self, entity):
        return (
            equal(self.param('cluster'), get_link_name(self._connection, entity.cluster)) and equal(convert_to_bytes(self.param('memory')), entity.memory) and
            equal(convert_to_bytes(self.param('memory_guaranteed')), entity.memory_policy.guaranteed) and
            equal(self.param('cpu_cores'), entity.cpu.topology.cores) and
            equal(self.param('cpu_sockets'), entity.cpu.topology.sockets) and
            equal(self.param('type'), str(entity.type)) and
            equal(self.param('operating_system'), str(entity.os.type)) and
            equal(self.param('high_availability'), entity.high_availability.enabled) and
            equal(self.param('lease'), get_link_name(self._connection, getattr(entity.lease, 'storage_domain', None))) and
            equal(self.param('stateless'), entity.stateless) and
            equal(self.param('cpu_shares'), entity.cpu_shares) and
            equal(self.param('delete_protected'), entity.delete_protected) and
            equal(self.param('use_latest_template_version'), entity.use_latest_template_version) and
            equal(self.param('boot_devices'), [str(dev) for dev in getattr(entity.os, 'devices', [])]) and
            equal(self.param('instance_type'), get_link_name(self._connection, entity.instance_type), ignore_case=True) and
            equal(self.param('description'), entity.description) and
            equal(self.param('comment'), entity.comment) and
            equal(self.param('timezone'), getattr(entity.time_zone, 'name', None)) and
            equal(self.param('serial_policy'), str(getattr(entity.serial_number, 'policy', None))) and
            equal(self.param('serial_policy_value'), getattr(entity.serial_number, 'value', None))
        )

    def pre_create(self, entity):
        # If VM don't exists, and template is not specified, set it to Blank:
        if entity is None:
            if self.param('template') is None:
                self._module.params['template'] = 'Blank'

    def post_update(self, entity):
        self.post_create(entity)

    def post_create(self, entity):
        # After creation of the VM, attach disks and NICs:
        self.changed = self.__attach_disks(entity)
        self.changed = self.__attach_nics(entity)

    def pre_remove(self, entity):
        # Forcibly stop the VM, if it's not in DOWN state:
        if entity.status != otypes.VmStatus.DOWN:
            if not self._module.check_mode:
                self.changed = self.action(
                    action='stop',
                    action_condition=lambda vm: vm.status != otypes.VmStatus.DOWN,
                    wait_condition=lambda vm: vm.status == otypes.VmStatus.DOWN,
                )['changed']

    def __suspend_shutdown_common(self, vm_service):
        if vm_service.get().status in [
            otypes.VmStatus.MIGRATING,
            otypes.VmStatus.POWERING_UP,
            otypes.VmStatus.REBOOT_IN_PROGRESS,
            otypes.VmStatus.WAIT_FOR_LAUNCH,
            otypes.VmStatus.UP,
            otypes.VmStatus.RESTORING_STATE,
        ]:
            self._wait_for_UP(vm_service)

    def _pre_shutdown_action(self, entity):
        vm_service = self._service.vm_service(entity.id)
        self.__suspend_shutdown_common(vm_service)
        if entity.status in [otypes.VmStatus.SUSPENDED, otypes.VmStatus.PAUSED]:
            vm_service.start()
            self._wait_for_UP(vm_service)
        return vm_service.get()

    def _pre_suspend_action(self, entity):
        vm_service = self._service.vm_service(entity.id)
        self.__suspend_shutdown_common(vm_service)
        if entity.status in [otypes.VmStatus.PAUSED, otypes.VmStatus.DOWN]:
            vm_service.start()
            self._wait_for_UP(vm_service)
        return vm_service.get()

    def _post_start_action(self, entity):
        vm_service = self._service.service(entity.id)
        self._wait_for_UP(vm_service)
        self._attach_cd(vm_service.get())
        self._migrate_vm(vm_service.get())

    def _attach_cd(self, entity):
        cd_iso = self.param('cd_iso')
        if cd_iso is not None:
            vm_service = self._service.service(entity.id)
            current = vm_service.get().status == otypes.VmStatus.UP
            cdroms_service = vm_service.cdroms_service()
            cdrom_device = cdroms_service.list()[0]
            cdrom_service = cdroms_service.cdrom_service(cdrom_device.id)
            cdrom = cdrom_service.get(current=current)
            if getattr(cdrom.file, 'id', '') != cd_iso:
                if not self._module.check_mode:
                    cdrom_service.update(
                        cdrom=otypes.Cdrom(
                            file=otypes.File(id=cd_iso)
                        ),
                        current=current,
                    )
                self.changed = True

        return entity

    def _migrate_vm(self, entity):
        vm_host = self.param('host')
        vm_service = self._service.vm_service(entity.id)
        if vm_host is not None:
            # In case VM is preparing to be UP, wait to be up, to migrate it:
            if entity.status == otypes.VmStatus.UP:
                hosts_service = self._connection.system_service().hosts_service()
                current_vm_host = hosts_service.host_service(entity.host.id).get().name
                if vm_host != current_vm_host:
                    if not self._module.check_mode:
                        vm_service.migrate(host=otypes.Host(name=vm_host))
                        self._wait_for_UP(vm_service)
                    self.changed = True

        return entity

    def _wait_for_UP(self, vm_service):
        wait(
            service=vm_service,
            condition=lambda vm: vm.status == otypes.VmStatus.UP,
            wait=self.param('wait'),
            timeout=self.param('timeout'),
        )

    def _wait_for_vm_disks(self, vm_service):
        disks_service = self._connection.system_service().disks_service()
        for da in vm_service.disk_attachments_service().list():
            disk_service = disks_service.disk_service(da.disk.id)
            wait(
                service=disk_service,
                condition=lambda disk: disk.status == otypes.DiskStatus.OK,
                wait=self.param('wait'),
                timeout=self.param('timeout'),
            )

    def wait_for_down(self, vm):
        """
        This function will first wait for the status DOWN of the VM.
        Then it will find the active snapshot and wait until it's state is OK for
        stateless VMs and statless snaphot is removed.
        """
        vm_service = self._service.vm_service(vm.id)
        wait(
            service=vm_service,
            condition=lambda vm: vm.status == otypes.VmStatus.DOWN,
            wait=self.param('wait'),
            timeout=self.param('timeout'),
        )
        if vm.stateless:
            snapshots_service = vm_service.snapshots_service()
            snapshots = snapshots_service.list()
            snap_active = [
                snap for snap in snapshots
                if snap.snapshot_type == otypes.SnapshotType.ACTIVE
            ][0]
            snap_stateless = [
                snap for snap in snapshots
                if snap.snapshot_type == otypes.SnapshotType.STATELESS
            ]
            # Stateless snapshot may be already removed:
            if snap_stateless:
                wait(
                    service=snapshots_service.snapshot_service(snap_stateless[0].id),
                    condition=lambda snap: snap is None,
                    wait=self.param('wait'),
                    timeout=self.param('timeout'),
                )
            wait(
                service=snapshots_service.snapshot_service(snap_active.id),
                condition=lambda snap: snap.snapshot_status == otypes.SnapshotStatus.OK,
                wait=self.param('wait'),
                timeout=self.param('timeout'),
            )
        return True

    def __attach_disks(self, entity):
        if not self.param('disks'):
            return

        vm_service = self._service.service(entity.id)
        disks_service = self._connection.system_service().disks_service()
        disk_attachments_service = vm_service.disk_attachments_service()

        self._wait_for_vm_disks(vm_service)
        for disk in self.param('disks'):
            # If disk ID is not specified, find disk by name:
            disk_id = disk.get('id')
            if disk_id is None:
                disk_id = getattr(
                    search_by_name(
                        service=disks_service,
                        name=disk.get('name')
                    ),
                    'id',
                    None
                )

            # Attach disk to VM:
            disk_attachment = disk_attachments_service.attachment_service(disk_id)
            if get_entity(disk_attachment) is None:
                if not self._module.check_mode:
                    disk_attachments_service.add(
                        otypes.DiskAttachment(
                            disk=otypes.Disk(
                                id=disk_id,
                            ),
                            active=disk.get('activate', True),
                            interface=otypes.DiskInterface(
                                disk.get('interface', 'virtio')
                            ),
                            bootable=disk.get('bootable', False),
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


def import_vm(module, connection):
    vms_service = connection.system_service().vms_service()
    if search_by_name(vms_service, module.params['name']) is not None:
        return False

    events_service = connection.system_service().events_service()
    last_event = events_service.list(max=1)[0]

    external_type = [
        tmp for tmp in ['kvm', 'xen', 'vmware']
        if module.params[tmp] is not None
    ][0]

    external_vm = module.params[external_type]
    imports_service = connection.system_service().external_vm_imports_service()
    imported_vm = imports_service.add(
        otypes.ExternalVmImport(
            vm=otypes.Vm(
                name=module.params['name']
            ),
            name=external_vm.get('name'),
            username=external_vm.get('username', 'test'),
            password=external_vm.get('password', 'test'),
            provider=otypes.ExternalVmProviderType(external_type),
            url=external_vm.get('url'),
            cluster=otypes.Cluster(
                name=module.params['cluster'],
            ) if module.params['cluster'] else None,
            storage_domain=otypes.StorageDomain(
                name=external_vm.get('storage_domain'),
            ) if external_vm.get('storage_domain') else None,
            sparse=external_vm.get('sparse', True),
            host=otypes.Host(
                name=module.params['host'],
            ) if module.params['host'] else None,
        )
    )

    # Wait until event with code 1152 for our VM don't appear:
    vms_service = connection.system_service().vms_service()
    wait(
        service=vms_service.vm_service(imported_vm.vm.id),
        condition=lambda vm: len([
            event
            for event in events_service.list(
                from_=int(last_event.id),
                search='type=1152 and vm.id=%s' % vm.id,
            )
        ]) > 0 if vm is not None else False,
        fail_condition=lambda vm: vm is None,
        timeout=module.params['timeout'],
        poll_interval=module.params['poll_interval'],
    )
    return True


def _get_initialization(sysprep, cloud_init, cloud_init_nics):
    initialization = None
    if cloud_init or cloud_init_nics:
        initialization = otypes.Initialization(
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
        initialization = otypes.Initialization(
            **sysprep
        )
    return initialization


def control_state(vm, vms_service, module):
    if vm is None:
        return

    force = module.params['force']
    state = module.params['state']

    vm_service = vms_service.vm_service(vm.id)
    if vm.status == otypes.VmStatus.IMAGE_LOCKED:
        wait(
            service=vm_service,
            condition=lambda vm: vm.status == otypes.VmStatus.DOWN,
        )
    elif vm.status == otypes.VmStatus.SAVING_STATE:
        # Result state is SUSPENDED, we should wait to be suspended:
        wait(
            service=vm_service,
            condition=lambda vm: vm.status == otypes.VmStatus.SUSPENDED,
        )
    elif (
        vm.status == otypes.VmStatus.UNASSIGNED or
        vm.status == otypes.VmStatus.UNKNOWN
    ):
        # Invalid states:
        module.fail_json(msg="Not possible to control VM, if it's in '{}' status".format(vm.status))
    elif vm.status == otypes.VmStatus.POWERING_DOWN:
        if (force and state == 'stopped') or state == 'absent':
            vm_service.stop()
            wait(
                service=vm_service,
                condition=lambda vm: vm.status == otypes.VmStatus.DOWN,
            )
        else:
            # If VM is powering down, wait to be DOWN or UP.
            # VM can end in UP state in case there is no GA
            # or ACPI on the VM or shutdown operation crashed:
            wait(
                service=vm_service,
                condition=lambda vm: vm.status in [otypes.VmStatus.DOWN, otypes.VmStatus.UP],
            )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(type='str', default='present', choices=['absent', 'next_run', 'present', 'registered', 'running', 'stopped', 'suspended']),
        name=dict(type='str'),
        id=dict(type='str'),
        cluster=dict(type='str'),
        allow_partial_import=dict(type='bool'),
        template=dict(type='str'),
        template_version=dict(type='int'),
        use_latest_template_version=dict(type='bool'),
        storage_domain=dict(type='str'),
        disk_format=dict(type='str', default='cow', choices=['cow', 'raw']),
        disks=dict(type='list', default=[]),
        memory=dict(type='str'),
        memory_guaranteed=dict(type='str'),
        cpu_sockets=dict(type='int'),
        cpu_cores=dict(type='int'),
        cpu_shares=dict(type='int'),
        type=dict(type='str', choices=['server', 'desktop']),
        operating_system=dict(type='str',
                              choices=[
                                  'rhel_6_ppc64', 'other', 'freebsd', 'windows_2003x64', 'windows_10',
                                  'rhel_6x64', 'rhel_4x64', 'windows_2008x64', 'windows_2008R2x64',
                                  'debian_7', 'windows_2012x64', 'ubuntu_14_04', 'ubuntu_12_04',
                                  'ubuntu_13_10', 'windows_8x64', 'other_linux_ppc64', 'windows_2003',
                                  'other_linux', 'windows_10x64', 'windows_2008', 'rhel_3', 'rhel_5',
                                  'rhel_4', 'other_ppc64', 'sles_11', 'rhel_6', 'windows_xp', 'rhel_7x64',
                                  'freebsdx64', 'rhel_7_ppc64', 'windows_7', 'rhel_5x64',
                                  'ubuntu_14_04_ppc64', 'sles_11_ppc64', 'windows_8',
                                  'windows_2012R2x64', 'windows_2008r2x64', 'ubuntu_13_04',
                                  'ubuntu_12_10', 'windows_7x64',
                              ]),
        cd_iso=dict(type='str'),
        boot_devices=dict(type='list'),
        high_availability=dict(type='bool'),
        lease=dict(type='str'),
        stateless=dict(type='bool'),
        delete_protected=dict(type='bool'),
        force=dict(type='bool', default=False),
        nics=dict(type='list', default=[]),
        cloud_init=dict(type='dict'),
        cloud_init_nics=dict(type='list', default=[]),
        sysprep=dict(type='dict'),
        host=dict(type='str'),
        clone=dict(type='bool', default=False),
        clone_permissions=dict(type='bool', default=False),
        kernel_path=dict(type='str'),
        initrd_path=dict(type='str'),
        kernel_params=dict(type='str'),
        instance_type=dict(type='str'),
        description=dict(type='str'),
        comment=dict(type='str'),
        timezone=dict(type='str'),
        serial_policy=dict(type='str', choices=['vm', 'host', 'custom']),
        serial_policy_value=dict(type='str'),
        vmware=dict(type='dict'),
        xen=dict(type='dict'),
        kvm=dict(type='dict'),
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
        vms_service = connection.system_service().vms_service()
        vms_module = VmsModule(
            connection=connection,
            module=module,
            service=vms_service,
        )
        vm = vms_module.search_entity()

        control_state(vm, vms_service, module)
        if state in ('present', 'running', 'next_run'):
            if module.params['xen'] or module.params['kvm'] or module.params['vmware']:
                vms_module.changed = import_vm(module, connection)

            sysprep = module.params['sysprep']
            cloud_init = module.params['cloud_init']
            cloud_init_nics = module.params['cloud_init_nics'] or []
            if cloud_init is not None:
                cloud_init_nics.append(cloud_init)

            # In case VM don't exist, wait for VM DOWN state,
            # otherwise don't wait for any state, just update VM:
            ret = vms_module.create(
                entity=vm,
                result_state=otypes.VmStatus.DOWN if vm is None else None,
                clone=module.params['clone'],
                clone_permissions=module.params['clone_permissions'],
            )

            # Run the VM if it was just created, else don't run it:
            if state == 'running':
                initialization = _get_initialization(sysprep, cloud_init, cloud_init_nics)
                ret = vms_module.action(
                    action='start',
                    post_action=vms_module._post_start_action,
                    action_condition=lambda vm: (
                        vm.status not in [
                            otypes.VmStatus.MIGRATING,
                            otypes.VmStatus.POWERING_UP,
                            otypes.VmStatus.REBOOT_IN_PROGRESS,
                            otypes.VmStatus.WAIT_FOR_LAUNCH,
                            otypes.VmStatus.UP,
                            otypes.VmStatus.RESTORING_STATE,
                        ]
                    ),
                    wait_condition=lambda vm: vm.status == otypes.VmStatus.UP,
                    # Start action kwargs:
                    use_cloud_init=cloud_init is not None or len(cloud_init_nics) > 0,
                    use_sysprep=sysprep is not None,
                    vm=otypes.Vm(
                        placement_policy=otypes.VmPlacementPolicy(
                            hosts=[otypes.Host(name=module.params['host'])]
                        ) if module.params['host'] else None,
                        initialization=initialization,
                        os=otypes.OperatingSystem(
                            cmdline=module.params.get('kernel_params'),
                            initrd=module.params.get('initrd_path'),
                            kernel=module.params.get('kernel_path'),
                        ) if (
                            module.params.get('kernel_params') or
                            module.params.get('initrd_path') or
                            module.params.get('kernel_path')
                        ) else None,
                    ) if (
                        module.params.get('kernel_params') or
                        module.params.get('initrd_path') or
                        module.params.get('kernel_path') or
                        module.params.get('host') or
                        initialization
                    ) else None,
                )

            if state == 'next_run':
                # Apply next run configuration, if needed:
                vm = vms_service.vm_service(ret['id']).get()
                if vm.next_run_configuration_exists:
                    ret = vms_module.action(
                        action='reboot',
                        entity=vm,
                        action_condition=lambda vm: vm.status == otypes.VmStatus.UP,
                        wait_condition=lambda vm: vm.status == otypes.VmStatus.UP,
                    )
        elif state == 'stopped':
            if module.params['xen'] or module.params['kvm'] or module.params['vmware']:
                vms_module.changed = import_vm(module, connection)

            ret = vms_module.create(
                result_state=otypes.VmStatus.DOWN if vm is None else None,
                clone=module.params['clone'],
                clone_permissions=module.params['clone_permissions'],
            )
            if module.params['force']:
                ret = vms_module.action(
                    action='stop',
                    post_action=vms_module._attach_cd,
                    action_condition=lambda vm: vm.status != otypes.VmStatus.DOWN,
                    wait_condition=vms_module.wait_for_down,
                )
            else:
                ret = vms_module.action(
                    action='shutdown',
                    pre_action=vms_module._pre_shutdown_action,
                    post_action=vms_module._attach_cd,
                    action_condition=lambda vm: vm.status != otypes.VmStatus.DOWN,
                    wait_condition=vms_module.wait_for_down,
                )
        elif state == 'suspended':
            vms_module.create(
                result_state=otypes.VmStatus.DOWN if vm is None else None,
                clone=module.params['clone'],
                clone_permissions=module.params['clone_permissions'],
            )
            ret = vms_module.action(
                action='suspend',
                pre_action=vms_module._pre_suspend_action,
                action_condition=lambda vm: vm.status != otypes.VmStatus.SUSPENDED,
                wait_condition=lambda vm: vm.status == otypes.VmStatus.SUSPENDED,
            )
        elif state == 'absent':
            ret = vms_module.remove()
        elif state == 'registered':
            storage_domains_service = connection.system_service().storage_domains_service()

            # Find the storage domain with unregistered VM:
            sd_id = get_id_by_name(storage_domains_service, module.params['storage_domain'])
            storage_domain_service = storage_domains_service.storage_domain_service(sd_id)
            vms_service = storage_domain_service.vms_service()

            # Find the the unregistered VM we want to register:
            vms = vms_service.list(unregistered=True)
            vm = next(
                (vm for vm in vms if (vm.id == module.params['id'] or vm.name == module.params['name'])),
                None
            )
            changed = False
            if vm is None:
                vm = vms_module.search_entity()
                if vm is None:
                    raise ValueError(
                        "VM '%s(%s)' wasn't found." % (module.params['name'], module.params['id'])
                    )
            else:
                # Register the vm into the system:
                changed = True
                vm_service = vms_service.vm_service(vm.id)
                vm_service.register(
                    allow_partial_import=module.params['allow_partial_import'],
                    cluster=otypes.Cluster(
                        name=module.params['cluster']
                    ) if module.params['cluster'] else None
                )

                if module.params['wait']:
                    vm = vms_module.wait_for_import()
                else:
                    # Fetch vm to initialize return.
                    vm = vm_service.get()
            ret = {
                'changed': changed,
                'id': vm.id,
                'vm': get_dict_of_struct(vm)
            }

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
