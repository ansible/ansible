#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This module is also sponsored by E.T.A.I. (www.etai.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vmware_guest
short_description: Manages virtual machines in vCenter
description: >
   This module can be used to create new virtual machines from templates or other virtual machines,
   manage power state of virtual machine such as power on, power off, suspend, shutdown, reboot, restart etc.,
   modify various virtual machine components like network, disk, customization etc.,
   rename a virtual machine and remove a virtual machine with associated components.
version_added: '2.2'
author:
- Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
- Philippe Dellaert (@pdellaert) <philippe@dellaert.org>
- Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
requirements:
- python >= 2.6
- PyVmomi
notes:
    - Please make sure that the user used for vmware_guest has the correct level of privileges.
    - For example, following is the list of minimum privileges required by users to create virtual machines.
    - "   DataStore > Allocate Space"
    - "   Virtual Machine > Configuration > Add New Disk"
    - "   Virtual Machine > Configuration > Add or Remove Device"
    - "   Virtual Machine > Inventory > Create New"
    - "   Network > Assign Network"
    - "   Resource > Assign Virtual Machine to Resource Pool"
    - "Module may require additional privileges as well, which may be required for gathering facts - e.g. ESXi configurations."
    - Tested on vSphere 5.5, 6.0, 6.5 and 6.7
    - Use SCSI disks instead of IDE when you want to expand online disks by specifing a SCSI controller
    - "For additional information please visit Ansible VMware community wiki - U(https://github.com/ansible/community/wiki/VMware)."
options:
  state:
    description:
    - Specify the state the virtual machine should be in.
    - 'If C(state) is set to C(present) and virtual machine exists, ensure the virtual machine
       configurations conforms to task arguments.'
    - 'If C(state) is set to C(absent) and virtual machine exists, then the specified virtual machine
      is removed with its associated components.'
    - 'If C(state) is set to one of the following C(poweredon), C(poweredoff), C(present), C(restarted), C(suspended)
      and virtual machine does not exists, then virtual machine is deployed with given parameters.'
    - 'If C(state) is set to C(poweredon) and virtual machine exists with powerstate other than powered on,
      then the specified virtual machine is powered on.'
    - 'If C(state) is set to C(poweredoff) and virtual machine exists with powerstate other than powered off,
      then the specified virtual machine is powered off.'
    - 'If C(state) is set to C(restarted) and virtual machine exists, then the virtual machine is restarted.'
    - 'If C(state) is set to C(suspended) and virtual machine exists, then the virtual machine is set to suspended mode.'
    - 'If C(state) is set to C(shutdownguest) and virtual machine exists, then the virtual machine is shutdown.'
    - 'If C(state) is set to C(rebootguest) and virtual machine exists, then the virtual machine is rebooted.'
    default: present
    choices: [ present, absent, poweredon, poweredoff, restarted, suspended, shutdownguest, rebootguest ]
  name:
    description:
    - Name of the virtual machine to work with.
    - Virtual machine names in vCenter are not necessarily unique, which may be problematic, see C(name_match).
    - 'If multiple virtual machines with same name exists, then C(folder) is required parameter to
       identify uniqueness of the virtual machine.'
    - This parameter is required, if C(state) is set to C(poweredon), C(poweredoff), C(present), C(restarted), C(suspended)
      and virtual machine does not exists.
    - This parameter is case sensitive.
    required: yes
  name_match:
    description:
    - If multiple virtual machines matching the name, use the first or last found.
    default: 'first'
    choices: [ first, last ]
  uuid:
    description:
    - UUID of the virtual machine to manage if known, this is VMware's unique identifier.
    - This is required if C(name) is not supplied.
    - If virtual machine does not exists, then this parameter is ignored.
    - Please note that a supplied UUID will be ignored on virtual machine creation, as VMware creates the UUID internally.
  use_instance_uuid:
    description:
    - Whether to use the VMWare instance UUID rather than the BIOS UUID.
    default: no
    type: bool
    version_added: '2.8'
  template:
    description:
    - Template or existing virtual machine used to create new virtual machine.
    - If this value is not set, virtual machine is created without using a template.
    - If the virtual machine already exists, this parameter will be ignored.
    - This parameter is case sensitive.
    - You can also specify template or VM UUID for identifying source. version_added 2.8. Use C(hw_product_uuid) from M(vmware_guest_facts) as UUID value.
    - From version 2.8 onwards, absolute path to virtual machine or template can be used.
    aliases: [ 'template_src' ]
  is_template:
    description:
    - Flag the instance as a template.
    - This will mark the given virtual machine as template.
    default: 'no'
    type: bool
    version_added: '2.3'
  folder:
    description:
    - Destination folder, absolute path to find an existing guest or create the new guest.
    - The folder should include the datacenter. ESX's datacenter is ha-datacenter.
    - This parameter is case sensitive.
    - This parameter is required, while deploying new virtual machine. version_added 2.5.
    - 'If multiple machines are found with same name, this parameter is used to identify
       uniqueness of the virtual machine. version_added 2.5'
    - 'Examples:'
    - '   folder: /ha-datacenter/vm'
    - '   folder: ha-datacenter/vm'
    - '   folder: /datacenter1/vm'
    - '   folder: datacenter1/vm'
    - '   folder: /datacenter1/vm/folder1'
    - '   folder: datacenter1/vm/folder1'
    - '   folder: /folder1/datacenter1/vm'
    - '   folder: folder1/datacenter1/vm'
    - '   folder: /folder1/datacenter1/vm/folder2'
  hardware:
    description:
    - Manage virtual machine's hardware attributes.
    - All parameters case sensitive.
    - 'Valid attributes are:'
    - ' - C(hotadd_cpu) (boolean): Allow virtual CPUs to be added while the virtual machine is running.'
    - ' - C(hotremove_cpu) (boolean): Allow virtual CPUs to be removed while the virtual machine is running.
          version_added: 2.5'
    - ' - C(hotadd_memory) (boolean): Allow memory to be added while the virtual machine is running.'
    - ' - C(memory_mb) (integer): Amount of memory in MB.'
    - ' - C(nested_virt) (bool): Enable nested virtualization. version_added: 2.5'
    - ' - C(num_cpus) (integer): Number of CPUs.'
    - ' - C(num_cpu_cores_per_socket) (integer): Number of Cores Per Socket. Value should be multiple of C(num_cpus).'
    - ' - C(scsi) (string): Valid values are C(buslogic), C(lsilogic), C(lsilogicsas) and C(paravirtual) (default).'
    - ' - C(memory_reservation) (integer): Amount of memory in MB to set resource limits for memory. version_added: 2.5'
    - " - C(memory_reservation_lock) (boolean): If set true, memory resource reservation for the virtual machine
          will always be equal to the virtual machine's memory size. version_added: 2.5"
    - ' - C(max_connections) (integer): Maximum number of active remote display connections for the virtual machines.
          version_added: 2.5.'
    - ' - C(mem_limit) (integer): The memory utilization of a virtual machine will not exceed this limit. Unit is MB.
          version_added: 2.5'
    - ' - C(mem_reservation) (integer): The amount of memory resource that is guaranteed available to the virtual
          machine. Unit is MB. version_added: 2.5'
    - ' - C(cpu_limit) (integer): The CPU utilization of a virtual machine will not exceed this limit. Unit is MHz.
          version_added: 2.5'
    - ' - C(cpu_reservation) (integer): The amount of CPU resource that is guaranteed available to the virtual machine.
          Unit is MHz. version_added: 2.5'
    - ' - C(version) (integer): The Virtual machine hardware versions. Default is 10 (ESXi 5.5 and onwards).
          Please check VMware documentation for correct virtual machine hardware version.
          Incorrect hardware version may lead to failure in deployment. If hardware version is already equal to the given
          version then no action is taken. version_added: 2.6'
    - ' - C(boot_firmware) (string): Choose which firmware should be used to boot the virtual machine.
          Allowed values are "bios" and "efi". version_added: 2.7'
    - ' - C(virt_based_security) (bool): Enable Virtualization Based Security feature for Windows 10.
          (Support from Virtual machine hardware version 14, Guest OS Windows 10 64 bit, Windows Server 2016)'

  guest_id:
    description:
    - Set the guest ID.
    - This parameter is case sensitive.
    - 'Examples:'
    - "  virtual machine with RHEL7 64 bit, will be 'rhel7_64Guest'"
    - "  virtual machine with CensOS 64 bit, will be 'centos64Guest'"
    - "  virtual machine with Ubuntu 64 bit, will be 'ubuntu64Guest'"
    - This field is required when creating a virtual machine.
    - >
         Valid values are referenced here:
         U(http://pubs.vmware.com/vsphere-6-5/topic/com.vmware.wssdk.apiref.doc/vim.vm.GuestOsDescriptor.GuestOsIdentifier.html)
    version_added: '2.3'
  disk:
    description:
    - A list of disks to add.
    - This parameter is case sensitive.
    - Shrinking disks is not supported.
    - Removing existing disks of the virtual machine is not supported.
    - 'Valid attributes are:'
    - ' - C(size_[tb,gb,mb,kb]) (integer): Disk storage size in specified unit.'
    - ' - C(type) (string): Valid values are:'
    - '     - C(thin) thin disk'
    - '     - C(eagerzeroedthick) eagerzeroedthick disk, added in version 2.5'
    - '     Default: C(None) thick disk, no eagerzero.'
    - ' - C(datastore) (string): The name of datastore which will be used for the disk. If C(autoselect_datastore) is set to True,
          then will select the less used datastore whose name contains this "disk.datastore" string.'
    - ' - C(filename) (string): Existing disk image to be used. Filename must be already exists on the datastore.'
    - '   Specify filename string in C([datastore_name] path/to/file.vmdk) format. Added in version 2.8.'
    - ' - C(autoselect_datastore) (bool): select the less used datastore. "disk.datastore" and "disk.autoselect_datastore"
          will not be used if C(datastore) is specified outside this C(disk) configuration.'
    - ' - C(disk_mode) (string): Type of disk mode. Added in version 2.6'
    - '     - Available options are :'
    - '     - C(persistent): Changes are immediately and permanently written to the virtual disk. This is default.'
    - '     - C(independent_persistent): Same as persistent, but not affected by snapshots.'
    - '     - C(independent_nonpersistent): Changes to virtual disk are made to a redo log and discarded at power off, but not affected by snapshots.'
  cdrom:
    description:
    - A CD-ROM configuration for the virtual machine.
    - 'Valid attributes are:'
    - ' - C(type) (string): The type of CD-ROM, valid options are C(none), C(client) or C(iso). With C(none) the CD-ROM will be disconnected but present.'
    - ' - C(iso_path) (string): The datastore path to the ISO file to use, in the form of C([datastore1] path/to/file.iso). Required if type is set C(iso).'
    version_added: '2.5'
  resource_pool:
    description:
    - Use the given resource pool for virtual machine operation.
    - This parameter is case sensitive.
    - Resource pool should be child of the selected host parent.
    version_added: '2.3'
  wait_for_ip_address:
    description:
    - Wait until vCenter detects an IP address for the virtual machine.
    - This requires vmware-tools (vmtoolsd) to properly work after creation.
    - "vmware-tools needs to be installed on the given virtual machine in order to work with this parameter."
    default: 'no'
    type: bool
  wait_for_customization:
    description:
    - Wait until vCenter detects all guest customizations as successfully completed.
    - When enabled, the VM will automatically be powered on.
    default: 'no'
    type: bool
    version_added: '2.8'
  state_change_timeout:
    description:
    - If the C(state) is set to C(shutdownguest), by default the module will return immediately after sending the shutdown signal.
    - If this argument is set to a positive integer, the module will instead wait for the virtual machine to reach the poweredoff state.
    - The value sets a timeout in seconds for the module to wait for the state change.
    default: 0
    version_added: '2.6'
  snapshot_src:
    description:
    - Name of the existing snapshot to use to create a clone of a virtual machine.
    - This parameter is case sensitive.
    - While creating linked clone using C(linked_clone) parameter, this parameter is required.
    version_added: '2.4'
  linked_clone:
    description:
    - Whether to create a linked clone from the snapshot specified.
    - If specified, then C(snapshot_src) is required parameter.
    default: 'no'
    type: bool
    version_added: '2.4'
  force:
    description:
    - Ignore warnings and complete the actions.
    - This parameter is useful while removing virtual machine which is powered on state.
    - 'This module reflects the VMware vCenter API and UI workflow, as such, in some cases the `force` flag will
       be mandatory to perform the action to ensure you are certain the action has to be taken, no matter what the consequence.
       This is specifically the case for removing a powered on the virtual machine when C(state) is set to C(absent).'
    default: 'no'
    type: bool
  datacenter:
    description:
    - Destination datacenter for the deploy operation.
    - This parameter is case sensitive.
    default: ha-datacenter
  cluster:
    description:
    - The cluster name where the virtual machine will run.
    - This is a required parameter, if C(esxi_hostname) is not set.
    - C(esxi_hostname) and C(cluster) are mutually exclusive parameters.
    - This parameter is case sensitive.
    version_added: '2.3'
  esxi_hostname:
    description:
    - The ESXi hostname where the virtual machine will run.
    - This is a required parameter, if C(cluster) is not set.
    - C(esxi_hostname) and C(cluster) are mutually exclusive parameters.
    - This parameter is case sensitive.
  annotation:
    description:
    - A note or annotation to include in the virtual machine.
    version_added: '2.3'
  customvalues:
    description:
    - Define a list of custom values to set on virtual machine.
    - A custom value object takes two fields C(key) and C(value).
    - Incorrect key and values will be ignored.
    version_added: '2.3'
  networks:
    description:
    - A list of networks (in the order of the NICs).
    - Removing NICs is not allowed, while reconfiguring the virtual machine.
    - All parameters and VMware object names are case sensetive.
    - 'One of the below parameters is required per entry:'
    - ' - C(name) (string): Name of the portgroup or distributed virtual portgroup for this interface.
          When specifying distributed virtual portgroup make sure given C(esxi_hostname) or C(cluster) is associated with it.'
    - ' - C(vlan) (integer): VLAN number for this interface.'
    - 'Optional parameters per entry (used for virtual hardware):'
    - ' - C(device_type) (string): Virtual network device (one of C(e1000), C(e1000e), C(pcnet32), C(vmxnet2), C(vmxnet3) (default), C(sriov)).'
    - ' - C(mac) (string): Customize MAC address.'
    - ' - C(dvswitch_name) (string): Name of the distributed vSwitch.
          This value is required if multiple distributed portgroups exists with the same name. version_added 2.7'
    - ' - C(start_connected) (bool): Indicates that virtual network adapter starts with associated virtual machine powers on. version_added: 2.5'
    - 'Optional parameters per entry (used for OS customization):'
    - ' - C(type) (string): Type of IP assignment (either C(dhcp) or C(static)). C(dhcp) is default.'
    - ' - C(ip) (string): Static IP address (implies C(type: static)).'
    - ' - C(netmask) (string): Static netmask required for C(ip).'
    - ' - C(gateway) (string): Static gateway.'
    - ' - C(dns_servers) (string): DNS servers for this network interface (Windows).'
    - ' - C(domain) (string): Domain name for this network interface (Windows).'
    - ' - C(wake_on_lan) (bool): Indicates if wake-on-LAN is enabled on this virtual network adapter. version_added: 2.5'
    - ' - C(allow_guest_control) (bool): Enables guest control over whether the connectable device is connected. version_added: 2.5'
    version_added: '2.3'
  customization:
    description:
    - Parameters for OS customization when cloning from the template or the virtual machine, or apply to the existing virtual machine directly.
    - Not all operating systems are supported for customization with respective vCenter version,
      please check VMware documentation for respective OS customization.
    - For supported customization operating system matrix, (see U(http://partnerweb.vmware.com/programs/guestOS/guest-os-customization-matrix.pdf))
    - All parameters and VMware object names are case sensitive.
    - Linux based OSes requires Perl package to be installed for OS customizations.
    - 'Common parameters (Linux/Windows):'
    - ' - C(existing_vm) (bool): If set to C(True), do OS customization on the specified virtual machine directly.
          If set to C(False) or not specified, do OS customization when cloning from the template or the virtual machine. version_added: 2.8'
    - ' - C(dns_servers) (list): List of DNS servers to configure.'
    - ' - C(dns_suffix) (list): List of domain suffixes, also known as DNS search path (default: C(domain) parameter).'
    - ' - C(domain) (string): DNS domain name to use.'
    - ' - C(hostname) (string): Computer hostname (default: shorted C(name) parameter). Allowed characters are alphanumeric (uppercase and lowercase)
          and minus, rest of the characters are dropped as per RFC 952.'
    - 'Parameters related to Windows customization:'
    - ' - C(autologon) (bool): Auto logon after virtual machine customization (default: False).'
    - ' - C(autologoncount) (int): Number of autologon after reboot (default: 1).'
    - ' - C(domainadmin) (string): User used to join in AD domain (mandatory with C(joindomain)).'
    - ' - C(domainadminpassword) (string): Password used to join in AD domain (mandatory with C(joindomain)).'
    - ' - C(fullname) (string): Server owner name (default: Administrator).'
    - ' - C(joindomain) (string): AD domain to join (Not compatible with C(joinworkgroup)).'
    - ' - C(joinworkgroup) (string): Workgroup to join (Not compatible with C(joindomain), default: WORKGROUP).'
    - ' - C(orgname) (string): Organisation name (default: ACME).'
    - ' - C(password) (string): Local administrator password.'
    - ' - C(productid) (string): Product ID.'
    - ' - C(runonce) (list): List of commands to run at first user logon.'
    - ' - C(timezone) (int): Timezone (See U(https://msdn.microsoft.com/en-us/library/ms912391.aspx)).'
    version_added: '2.3'
  vapp_properties:
    description:
    - A list of vApp properties
    - 'For full list of attributes and types refer to: U(https://github.com/vmware/pyvmomi/blob/master/docs/vim/vApp/PropertyInfo.rst)'
    - 'Basic attributes are:'
    - ' - C(id) (string): Property id - required.'
    - ' - C(value) (string): Property value.'
    - ' - C(type) (string): Value type, string type by default.'
    - ' - C(operation): C(remove): This attribute is required only when removing properties.'
    version_added: '2.6'
  customization_spec:
    description:
    - Unique name identifying the requested customization specification.
    - This parameter is case sensitive.
    - If set, then overrides C(customization) parameter values.
    version_added: '2.6'
  datastore:
    description:
    - Specify datastore or datastore cluster to provision virtual machine.
    - 'This parameter takes precedence over "disk.datastore" parameter.'
    - 'This parameter can be used to override datastore or datastore cluster setting of the virtual machine when deployed
      from the template.'
    - Please see example for more usage.
    version_added: '2.7'
  convert:
    description:
    - Specify convert disk type while cloning template or virtual machine.
    choices: [ thin, thick, eagerzeroedthick ]
    version_added: '2.8'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Create a virtual machine on given ESXi hostname
  vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    folder: /DC1/vm/
    name: test_vm_0001
    state: poweredon
    guest_id: centos64Guest
    # This is hostname of particular ESXi server on which user wants VM to be deployed
    esxi_hostname: "{{ esxi_hostname }}"
    disk:
    - size_gb: 10
      type: thin
      datastore: datastore1
    hardware:
      memory_mb: 512
      num_cpus: 4
      scsi: paravirtual
    networks:
    - name: VM Network
      mac: aa:bb:dd:aa:00:14
      ip: 10.10.10.100
      netmask: 255.255.255.0
      device_type: vmxnet3
    wait_for_ip_address: yes
  delegate_to: localhost
  register: deploy_vm

- name: Create a virtual machine from a template
  vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    folder: /testvms
    name: testvm_2
    state: poweredon
    template: template_el7
    disk:
    - size_gb: 10
      type: thin
      datastore: g73_datastore
    hardware:
      memory_mb: 512
      num_cpus: 6
      num_cpu_cores_per_socket: 3
      scsi: paravirtual
      memory_reservation: 512
      memory_reservation_lock: True
      mem_limit: 8096
      mem_reservation: 4096
      cpu_limit: 8096
      cpu_reservation: 4096
      max_connections: 5
      hotadd_cpu: True
      hotremove_cpu: True
      hotadd_memory: False
      version: 12 # Hardware version of virtual machine
      boot_firmware: "efi"
    cdrom:
      type: iso
      iso_path: "[datastore1] livecd.iso"
    networks:
    - name: VM Network
      mac: aa:bb:dd:aa:00:14
    wait_for_ip_address: yes
  delegate_to: localhost
  register: deploy

- name: Clone a virtual machine from Windows template and customize
  vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: datacenter1
    cluster: cluster
    name: testvm-2
    template: template_windows
    networks:
    - name: VM Network
      ip: 192.168.1.100
      netmask: 255.255.255.0
      gateway: 192.168.1.1
      mac: aa:bb:dd:aa:00:14
      domain: my_domain
      dns_servers:
      - 192.168.1.1
      - 192.168.1.2
    - vlan: 1234
      type: dhcp
    customization:
      autologon: yes
      dns_servers:
      - 192.168.1.1
      - 192.168.1.2
      domain: my_domain
      password: new_vm_password
      runonce:
      - powershell.exe -ExecutionPolicy Unrestricted -File C:\Windows\Temp\ConfigureRemotingForAnsible.ps1 -ForceNewSSLCert -EnableCredSSP
  delegate_to: localhost

- name:  Clone a virtual machine from Linux template and customize
  vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: "{{ datacenter }}"
    state: present
    folder: /DC1/vm
    template: "{{ template }}"
    name: "{{ vm_name }}"
    cluster: DC1_C1
    networks:
      - name: VM Network
        ip: 192.168.10.11
        netmask: 255.255.255.0
    wait_for_ip_address: True
    customization:
      domain: "{{ guest_domain }}"
      dns_servers:
        - 8.9.9.9
        - 7.8.8.9
      dns_suffix:
        - example.com
        - example2.com
  delegate_to: localhost

- name: Rename a virtual machine (requires the virtual machine's uuid)
  vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    uuid: "{{ vm_uuid }}"
    name: new_name
    state: present
  delegate_to: localhost

- name: Remove a virtual machine by uuid
  vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    uuid: "{{ vm_uuid }}"
    state: absent
  delegate_to: localhost

- name: Manipulate vApp properties
  vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    name: vm_name
    state: present
    vapp_properties:
      - id: remoteIP
        category: Backup
        label: Backup server IP
        type: str
        value: 10.10.10.1
      - id: old_property
        operation: remove
  delegate_to: localhost

- name: Set powerstate of a virtual machine to poweroff by using UUID
  vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    uuid: "{{ vm_uuid }}"
    state: poweredoff
  delegate_to: localhost

- name: Deploy a virtual machine in a datastore different from the datastore of the template
  vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    name: "{{ vm_name }}"
    state: present
    template: "{{ template_name }}"
    # Here datastore can be different which holds template
    datastore: "{{ virtual_machine_datastore }}"
    hardware:
      memory_mb: 512
      num_cpus: 2
      scsi: paravirtual
  delegate_to: localhost
'''

RETURN = r'''
instance:
    description: metadata about the new virtual machine
    returned: always
    type: dict
    sample: None
'''

import re
import time
import string

HAS_PYVMOMI = False
try:
    from pyVmomi import vim, vmodl, VmomiSupport
    HAS_PYVMOMI = True
except ImportError:
    pass

from random import randint
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.vmware import (find_obj, gather_vm_facts, get_all_objs,
                                         compile_folder_path_for_object, serialize_spec,
                                         vmware_argument_spec, set_vm_power_state, PyVmomi,
                                         find_dvs_by_name, find_dvspg_by_name, wait_for_vm_ip,
                                         wait_for_task, TaskError)


class PyVmomiDeviceHelper(object):
    """ This class is a helper to create easily VMWare Objects for PyVmomiHelper """

    def __init__(self, module):
        self.module = module
        self.next_disk_unit_number = 0
        self.scsi_device_type = {
            'lsilogic': vim.vm.device.VirtualLsiLogicController,
            'paravirtual': vim.vm.device.ParaVirtualSCSIController,
            'buslogic': vim.vm.device.VirtualBusLogicController,
            'lsilogicsas': vim.vm.device.VirtualLsiLogicSASController,
        }

    def create_scsi_controller(self, scsi_type):
        scsi_ctl = vim.vm.device.VirtualDeviceSpec()
        scsi_ctl.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        scsi_device = self.scsi_device_type.get(scsi_type, vim.vm.device.ParaVirtualSCSIController)
        scsi_ctl.device = scsi_device()
        scsi_ctl.device.busNumber = 0
        # While creating a new SCSI controller, temporary key value
        # should be unique negative integers
        scsi_ctl.device.key = -randint(1000, 9999)
        scsi_ctl.device.hotAddRemove = True
        scsi_ctl.device.sharedBus = 'noSharing'
        scsi_ctl.device.scsiCtlrUnitNumber = 7

        return scsi_ctl

    def is_scsi_controller(self, device):
        return isinstance(device, tuple(self.scsi_device_type.values()))

    @staticmethod
    def create_ide_controller():
        ide_ctl = vim.vm.device.VirtualDeviceSpec()
        ide_ctl.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        ide_ctl.device = vim.vm.device.VirtualIDEController()
        ide_ctl.device.deviceInfo = vim.Description()
        # While creating a new IDE controller, temporary key value
        # should be unique negative integers
        ide_ctl.device.key = -randint(200, 299)
        ide_ctl.device.busNumber = 0

        return ide_ctl

    @staticmethod
    def create_cdrom(ide_ctl, cdrom_type, iso_path=None):
        cdrom_spec = vim.vm.device.VirtualDeviceSpec()
        cdrom_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        cdrom_spec.device = vim.vm.device.VirtualCdrom()
        cdrom_spec.device.controllerKey = ide_ctl.device.key
        cdrom_spec.device.key = -1
        cdrom_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        cdrom_spec.device.connectable.allowGuestControl = True
        cdrom_spec.device.connectable.startConnected = (cdrom_type != "none")
        if cdrom_type in ["none", "client"]:
            cdrom_spec.device.backing = vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo()
        elif cdrom_type == "iso":
            cdrom_spec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso_path)

        return cdrom_spec

    @staticmethod
    def is_equal_cdrom(vm_obj, cdrom_device, cdrom_type, iso_path):
        if cdrom_type == "none":
            return (isinstance(cdrom_device.backing, vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo) and
                    cdrom_device.connectable.allowGuestControl and
                    not cdrom_device.connectable.startConnected and
                    (vm_obj.runtime.powerState != vim.VirtualMachinePowerState.poweredOn or not cdrom_device.connectable.connected))
        elif cdrom_type == "client":
            return (isinstance(cdrom_device.backing, vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo) and
                    cdrom_device.connectable.allowGuestControl and
                    cdrom_device.connectable.startConnected and
                    (vm_obj.runtime.powerState != vim.VirtualMachinePowerState.poweredOn or cdrom_device.connectable.connected))
        elif cdrom_type == "iso":
            return (isinstance(cdrom_device.backing, vim.vm.device.VirtualCdrom.IsoBackingInfo) and
                    cdrom_device.backing.fileName == iso_path and
                    cdrom_device.connectable.allowGuestControl and
                    cdrom_device.connectable.startConnected and
                    (vm_obj.runtime.powerState != vim.VirtualMachinePowerState.poweredOn or cdrom_device.connectable.connected))

    def create_scsi_disk(self, scsi_ctl, disk_index=None):
        diskspec = vim.vm.device.VirtualDeviceSpec()
        diskspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        diskspec.device = vim.vm.device.VirtualDisk()
        diskspec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        diskspec.device.controllerKey = scsi_ctl.device.key

        if self.next_disk_unit_number == 7:
            raise AssertionError()
        if disk_index == 7:
            raise AssertionError()
        """
        Configure disk unit number.
        """
        if disk_index is not None:
            diskspec.device.unitNumber = disk_index
            self.next_disk_unit_number = disk_index + 1
        else:
            diskspec.device.unitNumber = self.next_disk_unit_number
            self.next_disk_unit_number += 1

        # unit number 7 is reserved to SCSI controller, increase next index
        if self.next_disk_unit_number == 7:
            self.next_disk_unit_number += 1

        return diskspec

    def get_device(self, device_type, name):
        nic_dict = dict(pcnet32=vim.vm.device.VirtualPCNet32(),
                        vmxnet2=vim.vm.device.VirtualVmxnet2(),
                        vmxnet3=vim.vm.device.VirtualVmxnet3(),
                        e1000=vim.vm.device.VirtualE1000(),
                        e1000e=vim.vm.device.VirtualE1000e(),
                        sriov=vim.vm.device.VirtualSriovEthernetCard(),
                        )
        if device_type in nic_dict:
            return nic_dict[device_type]
        else:
            self.module.fail_json(msg='Invalid device_type "%s"'
                                      ' for network "%s"' % (device_type, name))

    def create_nic(self, device_type, device_label, device_infos):
        nic = vim.vm.device.VirtualDeviceSpec()
        nic.device = self.get_device(device_type, device_infos['name'])
        nic.device.wakeOnLanEnabled = bool(device_infos.get('wake_on_lan', True))
        nic.device.deviceInfo = vim.Description()
        nic.device.deviceInfo.label = device_label
        nic.device.deviceInfo.summary = device_infos['name']
        nic.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic.device.connectable.startConnected = bool(device_infos.get('start_connected', True))
        nic.device.connectable.allowGuestControl = bool(device_infos.get('allow_guest_control', True))
        nic.device.connectable.connected = True
        if 'mac' in device_infos and self.is_valid_mac_addr(device_infos['mac']):
            nic.device.addressType = 'manual'
            nic.device.macAddress = device_infos['mac']
        else:
            nic.device.addressType = 'generated'

        return nic

    @staticmethod
    def is_valid_mac_addr(mac_addr):
        """
        Function to validate MAC address for given string
        Args:
            mac_addr: string to validate as MAC address

        Returns: (Boolean) True if string is valid MAC address, otherwise False
        """
        mac_addr_regex = re.compile('[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$')
        return bool(mac_addr_regex.match(mac_addr))

    def integer_value(self, input_value, name):
        """
        Function to return int value for given input, else return error
        Args:
            input_value: Input value to retrive int value from
            name:  Name of the Input value (used to build error message)
        Returns: (int) if integer value can be obtained, otherwise will send a error message.
        """
        if isinstance(input_value, int):
            return input_value
        elif isinstance(input_value, str) and input_value.isdigit():
            return int(input_value)
        else:
            self.module.fail_json(msg='"%s" attribute should be an'
                                  ' integer value.' % name)


class PyVmomiCache(object):
    """ This class caches references to objects which are requested multiples times but not modified """

    def __init__(self, content, dc_name=None):
        self.content = content
        self.dc_name = dc_name
        self.networks = {}
        self.clusters = {}
        self.esx_hosts = {}
        self.parent_datacenters = {}

    def find_obj(self, content, types, name, confine_to_datacenter=True):
        """ Wrapper around find_obj to set datacenter context """
        result = find_obj(content, types, name)
        if result and confine_to_datacenter:
            if to_text(self.get_parent_datacenter(result).name) != to_text(self.dc_name):
                result = None
                objects = self.get_all_objs(content, types, confine_to_datacenter=True)
                for obj in objects:
                    if name is None or to_text(obj.name) == to_text(name):
                        return obj
        return result

    def get_all_objs(self, content, types, confine_to_datacenter=True):
        """ Wrapper around get_all_objs to set datacenter context """
        objects = get_all_objs(content, types)
        if confine_to_datacenter:
            if hasattr(objects, 'items'):
                # resource pools come back as a dictionary
                # make a copy
                tmpobjs = objects.copy()
                for k, v in objects.items():
                    parent_dc = self.get_parent_datacenter(k)
                    if parent_dc.name != self.dc_name:
                        tmpobjs.pop(k, None)
                objects = tmpobjs
            else:
                # everything else should be a list
                objects = [x for x in objects if self.get_parent_datacenter(x).name == self.dc_name]

        return objects

    def get_network(self, network):
        if network not in self.networks:
            self.networks[network] = self.find_obj(self.content, [vim.Network], network)

        return self.networks[network]

    def get_cluster(self, cluster):
        if cluster not in self.clusters:
            self.clusters[cluster] = self.find_obj(self.content, [vim.ClusterComputeResource], cluster)

        return self.clusters[cluster]

    def get_esx_host(self, host):
        if host not in self.esx_hosts:
            self.esx_hosts[host] = self.find_obj(self.content, [vim.HostSystem], host)

        return self.esx_hosts[host]

    def get_parent_datacenter(self, obj):
        """ Walk the parent tree to find the objects datacenter """
        if isinstance(obj, vim.Datacenter):
            return obj
        if obj in self.parent_datacenters:
            return self.parent_datacenters[obj]
        datacenter = None
        while True:
            if not hasattr(obj, 'parent'):
                break
            obj = obj.parent
            if isinstance(obj, vim.Datacenter):
                datacenter = obj
                break
        self.parent_datacenters[obj] = datacenter
        return datacenter


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.device_helper = PyVmomiDeviceHelper(self.module)
        self.configspec = None
        self.change_detected = False  # a change was detected and needs to be applied through reconfiguration
        self.change_applied = False   # a change was applied meaning at least one task succeeded
        self.customspec = None
        self.cache = PyVmomiCache(self.content, dc_name=self.params['datacenter'])

    def gather_facts(self, vm):
        return gather_vm_facts(self.content, vm)

    def remove_vm(self, vm):
        # https://www.vmware.com/support/developer/converter-sdk/conv60_apireference/vim.ManagedEntity.html#destroy
        if vm.summary.runtime.powerState.lower() == 'poweredon':
            self.module.fail_json(msg="Virtual machine %s found in 'powered on' state, "
                                      "please use 'force' parameter to remove or poweroff VM "
                                      "and try removing VM again." % vm.name)
        task = vm.Destroy()
        self.wait_for_task(task)
        if task.info.state == 'error':
            return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'destroy'}
        else:
            return {'changed': self.change_applied, 'failed': False}

    def configure_guestid(self, vm_obj, vm_creation=False):
        # guest_id is not required when using templates
        if self.params['template'] and not self.params['guest_id']:
            return

        # guest_id is only mandatory on VM creation
        if vm_creation and self.params['guest_id'] is None:
            self.module.fail_json(msg="guest_id attribute is mandatory for VM creation")

        if self.params['guest_id'] and \
                (vm_obj is None or self.params['guest_id'].lower() != vm_obj.summary.config.guestId.lower()):
            self.change_detected = True
            self.configspec.guestId = self.params['guest_id']

    def configure_resource_alloc_info(self, vm_obj):
        """
        Function to configure resource allocation information about virtual machine
        :param vm_obj: VM object in case of reconfigure, None in case of deploy
        :return: None
        """
        rai_change_detected = False
        memory_allocation = vim.ResourceAllocationInfo()
        cpu_allocation = vim.ResourceAllocationInfo()

        if 'hardware' in self.params:
            if 'mem_limit' in self.params['hardware']:
                mem_limit = None
                try:
                    mem_limit = int(self.params['hardware'].get('mem_limit'))
                except ValueError:
                    self.module.fail_json(msg="hardware.mem_limit attribute should be an integer value.")
                memory_allocation.limit = mem_limit
                if vm_obj is None or memory_allocation.limit != vm_obj.config.memoryAllocation.limit:
                    rai_change_detected = True

            if 'mem_reservation' in self.params['hardware']:
                mem_reservation = None
                try:
                    mem_reservation = int(self.params['hardware'].get('mem_reservation'))
                except ValueError:
                    self.module.fail_json(msg="hardware.mem_reservation should be an integer value.")

                memory_allocation.reservation = mem_reservation
                if vm_obj is None or \
                        memory_allocation.reservation != vm_obj.config.memoryAllocation.reservation:
                    rai_change_detected = True

            if 'cpu_limit' in self.params['hardware']:
                cpu_limit = None
                try:
                    cpu_limit = int(self.params['hardware'].get('cpu_limit'))
                except ValueError:
                    self.module.fail_json(msg="hardware.cpu_limit attribute should be an integer value.")
                cpu_allocation.limit = cpu_limit
                if vm_obj is None or cpu_allocation.limit != vm_obj.config.cpuAllocation.limit:
                    rai_change_detected = True

            if 'cpu_reservation' in self.params['hardware']:
                cpu_reservation = None
                try:
                    cpu_reservation = int(self.params['hardware'].get('cpu_reservation'))
                except ValueError:
                    self.module.fail_json(msg="hardware.cpu_reservation should be an integer value.")
                cpu_allocation.reservation = cpu_reservation
                if vm_obj is None or \
                        cpu_allocation.reservation != vm_obj.config.cpuAllocation.reservation:
                    rai_change_detected = True

        if rai_change_detected:
            self.configspec.memoryAllocation = memory_allocation
            self.configspec.cpuAllocation = cpu_allocation
            self.change_detected = True

    def configure_cpu_and_memory(self, vm_obj, vm_creation=False):
        # set cpu/memory/etc
        if 'hardware' in self.params:
            if 'num_cpus' in self.params['hardware']:
                try:
                    num_cpus = int(self.params['hardware']['num_cpus'])
                except ValueError:
                    self.module.fail_json(msg="hardware.num_cpus attribute should be an integer value.")
                # check VM power state and cpu hot-add/hot-remove state before re-config VM
                if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                    if not vm_obj.config.cpuHotRemoveEnabled and num_cpus < vm_obj.config.hardware.numCPU:
                        self.module.fail_json(msg="Configured cpu number is less than the cpu number of the VM, "
                                                  "cpuHotRemove is not enabled")
                    if not vm_obj.config.cpuHotAddEnabled and num_cpus > vm_obj.config.hardware.numCPU:
                        self.module.fail_json(msg="Configured cpu number is more than the cpu number of the VM, "
                                                  "cpuHotAdd is not enabled")

                if 'num_cpu_cores_per_socket' in self.params['hardware']:
                    try:
                        num_cpu_cores_per_socket = int(self.params['hardware']['num_cpu_cores_per_socket'])
                    except ValueError:
                        self.module.fail_json(msg="hardware.num_cpu_cores_per_socket attribute "
                                                  "should be an integer value.")
                    if num_cpus % num_cpu_cores_per_socket != 0:
                        self.module.fail_json(msg="hardware.num_cpus attribute should be a multiple "
                                                  "of hardware.num_cpu_cores_per_socket")
                    self.configspec.numCoresPerSocket = num_cpu_cores_per_socket
                    if vm_obj is None or self.configspec.numCoresPerSocket != vm_obj.config.hardware.numCoresPerSocket:
                        self.change_detected = True
                self.configspec.numCPUs = num_cpus
                if vm_obj is None or self.configspec.numCPUs != vm_obj.config.hardware.numCPU:
                    self.change_detected = True
            # num_cpu is mandatory for VM creation
            elif vm_creation and not self.params['template']:
                self.module.fail_json(msg="hardware.num_cpus attribute is mandatory for VM creation")

            if 'memory_mb' in self.params['hardware']:
                try:
                    memory_mb = int(self.params['hardware']['memory_mb'])
                except ValueError:
                    self.module.fail_json(msg="Failed to parse hardware.memory_mb value."
                                              " Please refer the documentation and provide"
                                              " correct value.")
                # check VM power state and memory hotadd state before re-config VM
                if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                    if vm_obj.config.memoryHotAddEnabled and memory_mb < vm_obj.config.hardware.memoryMB:
                        self.module.fail_json(msg="Configured memory is less than memory size of the VM, "
                                                  "operation is not supported")
                    elif not vm_obj.config.memoryHotAddEnabled and memory_mb != vm_obj.config.hardware.memoryMB:
                        self.module.fail_json(msg="memoryHotAdd is not enabled")
                self.configspec.memoryMB = memory_mb
                if vm_obj is None or self.configspec.memoryMB != vm_obj.config.hardware.memoryMB:
                    self.change_detected = True
            # memory_mb is mandatory for VM creation
            elif vm_creation and not self.params['template']:
                self.module.fail_json(msg="hardware.memory_mb attribute is mandatory for VM creation")

            if 'hotadd_memory' in self.params['hardware']:
                if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                        vm_obj.config.memoryHotAddEnabled != bool(self.params['hardware']['hotadd_memory']):
                    self.module.fail_json(msg="Configure hotadd memory operation is not supported when VM is power on")
                self.configspec.memoryHotAddEnabled = bool(self.params['hardware']['hotadd_memory'])
                if vm_obj is None or self.configspec.memoryHotAddEnabled != vm_obj.config.memoryHotAddEnabled:
                    self.change_detected = True

            if 'hotadd_cpu' in self.params['hardware']:
                if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                        vm_obj.config.cpuHotAddEnabled != bool(self.params['hardware']['hotadd_cpu']):
                    self.module.fail_json(msg="Configure hotadd cpu operation is not supported when VM is power on")
                self.configspec.cpuHotAddEnabled = bool(self.params['hardware']['hotadd_cpu'])
                if vm_obj is None or self.configspec.cpuHotAddEnabled != vm_obj.config.cpuHotAddEnabled:
                    self.change_detected = True

            if 'hotremove_cpu' in self.params['hardware']:
                if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                        vm_obj.config.cpuHotRemoveEnabled != bool(self.params['hardware']['hotremove_cpu']):
                    self.module.fail_json(msg="Configure hotremove cpu operation is not supported when VM is power on")
                self.configspec.cpuHotRemoveEnabled = bool(self.params['hardware']['hotremove_cpu'])
                if vm_obj is None or self.configspec.cpuHotRemoveEnabled != vm_obj.config.cpuHotRemoveEnabled:
                    self.change_detected = True

            if 'memory_reservation' in self.params['hardware']:
                memory_reservation_mb = 0
                try:
                    memory_reservation_mb = int(self.params['hardware']['memory_reservation'])
                except ValueError as e:
                    self.module.fail_json(msg="Failed to set memory_reservation value."
                                              "Valid value for memory_reservation value in MB (integer): %s" % e)

                mem_alloc = vim.ResourceAllocationInfo()
                mem_alloc.reservation = memory_reservation_mb
                self.configspec.memoryAllocation = mem_alloc
                if vm_obj is None or self.configspec.memoryAllocation.reservation != vm_obj.config.memoryAllocation.reservation:
                    self.change_detected = True

            if 'memory_reservation_lock' in self.params['hardware']:
                self.configspec.memoryReservationLockedToMax = bool(self.params['hardware']['memory_reservation_lock'])
                if vm_obj is None or self.configspec.memoryReservationLockedToMax != vm_obj.config.memoryReservationLockedToMax:
                    self.change_detected = True

            if 'boot_firmware' in self.params['hardware']:
                # boot firmware re-config can cause boot issue
                if vm_obj is not None:
                    return
                boot_firmware = self.params['hardware']['boot_firmware'].lower()
                if boot_firmware not in ('bios', 'efi'):
                    self.module.fail_json(msg="hardware.boot_firmware value is invalid [%s]."
                                              " Need one of ['bios', 'efi']." % boot_firmware)
                self.configspec.firmware = boot_firmware
                self.change_detected = True

    def configure_cdrom(self, vm_obj):
        # Configure the VM CD-ROM
        if "cdrom" in self.params and self.params["cdrom"]:
            if "type" not in self.params["cdrom"] or self.params["cdrom"]["type"] not in ["none", "client", "iso"]:
                self.module.fail_json(msg="cdrom.type is mandatory")
            if self.params["cdrom"]["type"] == "iso" and ("iso_path" not in self.params["cdrom"] or not self.params["cdrom"]["iso_path"]):
                self.module.fail_json(msg="cdrom.iso_path is mandatory in case cdrom.type is iso")

            if vm_obj and vm_obj.config.template:
                # Changing CD-ROM settings on a template is not supported
                return

            cdrom_spec = None
            cdrom_device = self.get_vm_cdrom_device(vm=vm_obj)
            iso_path = self.params["cdrom"]["iso_path"] if "iso_path" in self.params["cdrom"] else None
            if cdrom_device is None:
                # Creating new CD-ROM
                ide_device = self.get_vm_ide_device(vm=vm_obj)
                if ide_device is None:
                    # Creating new IDE device
                    ide_device = self.device_helper.create_ide_controller()
                    self.change_detected = True
                    self.configspec.deviceChange.append(ide_device)
                elif len(ide_device.device) > 3:
                    self.module.fail_json(msg="hardware.cdrom specified for a VM or template which already has 4 IDE devices of which none are a cdrom")

                cdrom_spec = self.device_helper.create_cdrom(ide_ctl=ide_device, cdrom_type=self.params["cdrom"]["type"], iso_path=iso_path)
                if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                    cdrom_spec.device.connectable.connected = (self.params["cdrom"]["type"] != "none")

            elif not self.device_helper.is_equal_cdrom(vm_obj=vm_obj, cdrom_device=cdrom_device, cdrom_type=self.params["cdrom"]["type"], iso_path=iso_path):
                # Updating an existing CD-ROM
                if self.params["cdrom"]["type"] in ["client", "none"]:
                    cdrom_device.backing = vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo()
                elif self.params["cdrom"]["type"] == "iso":
                    cdrom_device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso_path)
                cdrom_device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
                cdrom_device.connectable.allowGuestControl = True
                cdrom_device.connectable.startConnected = (self.params["cdrom"]["type"] != "none")
                if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                    cdrom_device.connectable.connected = (self.params["cdrom"]["type"] != "none")

                cdrom_spec = vim.vm.device.VirtualDeviceSpec()
                cdrom_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                cdrom_spec.device = cdrom_device

            if cdrom_spec:
                self.change_detected = True
                self.configspec.deviceChange.append(cdrom_spec)

    def configure_hardware_params(self, vm_obj):
        """
        Function to configure hardware related configuration of virtual machine
        Args:
            vm_obj: virtual machine object
        """
        if 'hardware' in self.params:
            if 'max_connections' in self.params['hardware']:
                # maxMksConnections == max_connections
                self.configspec.maxMksConnections = int(self.params['hardware']['max_connections'])
                if vm_obj is None or self.configspec.maxMksConnections != vm_obj.config.hardware.maxMksConnections:
                    self.change_detected = True

            if 'nested_virt' in self.params['hardware']:
                self.configspec.nestedHVEnabled = bool(self.params['hardware']['nested_virt'])
                if vm_obj is None or self.configspec.nestedHVEnabled != bool(vm_obj.config.nestedHVEnabled):
                    self.change_detected = True

            if 'version' in self.params['hardware']:
                hw_version_check_failed = False
                temp_version = self.params['hardware'].get('version', 10)
                try:
                    temp_version = int(temp_version)
                except ValueError:
                    hw_version_check_failed = True

                if temp_version not in range(3, 15):
                    hw_version_check_failed = True

                if hw_version_check_failed:
                    self.module.fail_json(msg="Failed to set hardware.version '%s' value as valid"
                                              " values range from 3 (ESX 2.x) to 14 (ESXi 6.5 and greater)." % temp_version)
                # Hardware version is denoted as "vmx-10"
                version = "vmx-%02d" % temp_version
                self.configspec.version = version
                if vm_obj is None or self.configspec.version != vm_obj.config.version:
                    self.change_detected = True
                if vm_obj is not None:
                    # VM exists and we need to update the hardware version
                    current_version = vm_obj.config.version
                    # current_version = "vmx-10"
                    version_digit = int(current_version.split("-", 1)[-1])
                    if temp_version < version_digit:
                        self.module.fail_json(msg="Current hardware version '%d' which is greater than the specified"
                                                  " version '%d'. Downgrading hardware version is"
                                                  " not supported. Please specify version greater"
                                                  " than the current version." % (version_digit,
                                                                                  temp_version))
                    new_version = "vmx-%02d" % temp_version
                    try:
                        task = vm_obj.UpgradeVM_Task(new_version)
                        self.wait_for_task(task)
                        if task.info.state == 'error':
                            return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'upgrade'}
                    except vim.fault.AlreadyUpgraded:
                        # Don't fail if VM is already upgraded.
                        pass

            if 'virt_based_security' in self.params['hardware']:
                host_version = self.select_host().summary.config.product.version
                if int(host_version.split('.')[0]) < 6 or (int(host_version.split('.')[0]) == 6 and int(host_version.split('.')[1]) < 7):
                    self.module.fail_json(msg="ESXi version %s not support VBS." % host_version)
                guest_ids = ['windows9_64Guest', 'windows9Server64Guest']
                if vm_obj is None:
                    guestid = self.configspec.guestId
                else:
                    guestid = vm_obj.summary.config.guestId
                if guestid not in guest_ids:
                    self.module.fail_json(msg="Guest '%s' not support VBS." % guestid)
                if (vm_obj is None and int(self.configspec.version.split('-')[1]) >= 14) or \
                        (vm_obj and int(vm_obj.config.version.split('-')[1]) >= 14 and (vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOff)):
                    self.configspec.flags = vim.vm.FlagInfo()
                    self.configspec.flags.vbsEnabled = bool(self.params['hardware']['virt_based_security'])
                    if bool(self.params['hardware']['virt_based_security']):
                        self.configspec.flags.vvtdEnabled = True
                        self.configspec.nestedHVEnabled = True
                        if (vm_obj is None and self.configspec.firmware == 'efi') or \
                                (vm_obj and vm_obj.config.firmware == 'efi'):
                            self.configspec.bootOptions = vim.vm.BootOptions()
                            self.configspec.bootOptions.efiSecureBootEnabled = True
                        else:
                            self.module.fail_json(msg="Not support VBS when firmware is BIOS.")
                    if vm_obj is None or self.configspec.flags.vbsEnabled != vm_obj.config.flags.vbsEnabled:
                        self.change_detected = True

    def get_device_by_type(self, vm=None, type=None):
        if vm is None or type is None:
            return None

        for device in vm.config.hardware.device:
            if isinstance(device, type):
                return device

        return None

    def get_vm_cdrom_device(self, vm=None):
        return self.get_device_by_type(vm=vm, type=vim.vm.device.VirtualCdrom)

    def get_vm_ide_device(self, vm=None):
        return self.get_device_by_type(vm=vm, type=vim.vm.device.VirtualIDEController)

    def get_vm_network_interfaces(self, vm=None):
        device_list = []
        if vm is None:
            return device_list

        nw_device_types = (vim.vm.device.VirtualPCNet32, vim.vm.device.VirtualVmxnet2,
                           vim.vm.device.VirtualVmxnet3, vim.vm.device.VirtualE1000,
                           vim.vm.device.VirtualE1000e, vim.vm.device.VirtualSriovEthernetCard)
        for device in vm.config.hardware.device:
            if isinstance(device, nw_device_types):
                device_list.append(device)

        return device_list

    def sanitize_network_params(self):
        """
        Sanitize user provided network provided params

        Returns: A sanitized list of network params, else fails

        """
        network_devices = list()
        # Clean up user data here
        for network in self.params['networks']:
            if 'name' not in network and 'vlan' not in network:
                self.module.fail_json(msg="Please specify at least a network name or"
                                          " a VLAN name under VM network list.")

            if 'name' in network and self.cache.get_network(network['name']) is None:
                self.module.fail_json(msg="Network '%(name)s' does not exist." % network)
            elif 'vlan' in network:
                dvps = self.cache.get_all_objs(self.content, [vim.dvs.DistributedVirtualPortgroup])
                for dvp in dvps:
                    if hasattr(dvp.config.defaultPortConfig, 'vlan') and \
                            isinstance(dvp.config.defaultPortConfig.vlan.vlanId, int) and \
                            str(dvp.config.defaultPortConfig.vlan.vlanId) == str(network['vlan']):
                        network['name'] = dvp.config.name
                        break
                    if 'dvswitch_name' in network and \
                            dvp.config.distributedVirtualSwitch.name == network['dvswitch_name'] and \
                            dvp.config.name == network['vlan']:
                        network['name'] = dvp.config.name
                        break

                    if dvp.config.name == network['vlan']:
                        network['name'] = dvp.config.name
                        break
                else:
                    self.module.fail_json(msg="VLAN '%(vlan)s' does not exist." % network)

            if 'type' in network:
                if network['type'] not in ['dhcp', 'static']:
                    self.module.fail_json(msg="Network type '%(type)s' is not a valid parameter."
                                              " Valid parameters are ['dhcp', 'static']." % network)
                if network['type'] != 'static' and ('ip' in network or 'netmask' in network):
                    self.module.fail_json(msg='Static IP information provided for network "%(name)s",'
                                              ' but "type" is set to "%(type)s".' % network)
            else:
                # Type is optional parameter, if user provided IP or Subnet assume
                # network type as 'static'
                if 'ip' in network or 'netmask' in network:
                    network['type'] = 'static'
                else:
                    # User wants network type as 'dhcp'
                    network['type'] = 'dhcp'

            if network.get('type') == 'static':
                if 'ip' in network and 'netmask' not in network:
                    self.module.fail_json(msg="'netmask' is required if 'ip' is"
                                              " specified under VM network list.")
                if 'ip' not in network and 'netmask' in network:
                    self.module.fail_json(msg="'ip' is required if 'netmask' is"
                                              " specified under VM network list.")

            validate_device_types = ['pcnet32', 'vmxnet2', 'vmxnet3', 'e1000', 'e1000e', 'sriov']
            if 'device_type' in network and network['device_type'] not in validate_device_types:
                self.module.fail_json(msg="Device type specified '%s' is not valid."
                                          " Please specify correct device"
                                          " type from ['%s']." % (network['device_type'],
                                                                  "', '".join(validate_device_types)))

            if 'mac' in network and not PyVmomiDeviceHelper.is_valid_mac_addr(network['mac']):
                self.module.fail_json(msg="Device MAC address '%s' is invalid."
                                          " Please provide correct MAC address." % network['mac'])

            network_devices.append(network)

        return network_devices

    def configure_network(self, vm_obj):
        # Ignore empty networks, this permits to keep networks when deploying a template/cloning a VM
        if len(self.params['networks']) == 0:
            return

        network_devices = self.sanitize_network_params()

        # List current device for Clone or Idempotency
        current_net_devices = self.get_vm_network_interfaces(vm=vm_obj)
        if len(network_devices) < len(current_net_devices):
            self.module.fail_json(msg="Given network device list is lesser than current VM device list (%d < %d). "
                                      "Removing interfaces is not allowed"
                                      % (len(network_devices), len(current_net_devices)))

        for key in range(0, len(network_devices)):
            nic_change_detected = False
            network_name = network_devices[key]['name']
            if key < len(current_net_devices) and (vm_obj or self.params['template']):
                # We are editing existing network devices, this is either when
                # are cloning from VM or Template
                nic = vim.vm.device.VirtualDeviceSpec()
                nic.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit

                nic.device = current_net_devices[key]
                if ('wake_on_lan' in network_devices[key] and
                        nic.device.wakeOnLanEnabled != network_devices[key].get('wake_on_lan')):
                    nic.device.wakeOnLanEnabled = network_devices[key].get('wake_on_lan')
                    nic_change_detected = True
                if ('start_connected' in network_devices[key] and
                        nic.device.connectable.startConnected != network_devices[key].get('start_connected')):
                    nic.device.connectable.startConnected = network_devices[key].get('start_connected')
                    nic_change_detected = True
                if ('allow_guest_control' in network_devices[key] and
                        nic.device.connectable.allowGuestControl != network_devices[key].get('allow_guest_control')):
                    nic.device.connectable.allowGuestControl = network_devices[key].get('allow_guest_control')
                    nic_change_detected = True

                if nic.device.deviceInfo.summary != network_name:
                    nic.device.deviceInfo.summary = network_name
                    nic_change_detected = True
                if 'device_type' in network_devices[key]:
                    device = self.device_helper.get_device(network_devices[key]['device_type'], network_name)
                    device_class = type(device)
                    if not isinstance(nic.device, device_class):
                        self.module.fail_json(msg="Changing the device type is not possible when interface is already present. "
                                                  "The failing device type is %s" % network_devices[key]['device_type'])
                # Changing mac address has no effect when editing interface
                if 'mac' in network_devices[key] and nic.device.macAddress != current_net_devices[key].macAddress:
                    self.module.fail_json(msg="Changing MAC address has not effect when interface is already present. "
                                              "The failing new MAC address is %s" % nic.device.macAddress)

            else:
                # Default device type is vmxnet3, VMWare best practice
                device_type = network_devices[key].get('device_type', 'vmxnet3')
                nic = self.device_helper.create_nic(device_type,
                                                    'Network Adapter %s' % (key + 1),
                                                    network_devices[key])
                nic.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                nic_change_detected = True

            if hasattr(self.cache.get_network(network_name), 'portKeys'):
                # VDS switch

                pg_obj = None
                if 'dvswitch_name' in network_devices[key]:
                    dvs_name = network_devices[key]['dvswitch_name']
                    dvs_obj = find_dvs_by_name(self.content, dvs_name)
                    if dvs_obj is None:
                        self.module.fail_json(msg="Unable to find distributed virtual switch %s" % dvs_name)
                    pg_obj = find_dvspg_by_name(dvs_obj, network_name)
                    if pg_obj is None:
                        self.module.fail_json(msg="Unable to find distributed port group %s" % network_name)
                else:
                    pg_obj = self.cache.find_obj(self.content, [vim.dvs.DistributedVirtualPortgroup], network_name)

                if (nic.device.backing and
                    (not hasattr(nic.device.backing, 'port') or
                     (nic.device.backing.port.portgroupKey != pg_obj.key or
                      nic.device.backing.port.switchUuid != pg_obj.config.distributedVirtualSwitch.uuid))):
                    nic_change_detected = True

                dvs_port_connection = vim.dvs.PortConnection()
                dvs_port_connection.portgroupKey = pg_obj.key
                # If user specifies distributed port group without associating to the hostsystem on which
                # virtual machine is going to be deployed then we get error. We can infer that there is no
                # association between given distributed port group and host system.
                host_system = self.params.get('esxi_hostname')
                if host_system and host_system not in [host.config.host.name for host in pg_obj.config.distributedVirtualSwitch.config.host]:
                    self.module.fail_json(msg="It seems that host system '%s' is not associated with distributed"
                                              " virtual portgroup '%s'. Please make sure host system is associated"
                                              " with given distributed virtual portgroup" % (host_system, pg_obj.name))
                # TODO: (akasurde) There is no way to find association between resource pool and distributed virtual portgroup
                # For now, check if we are able to find distributed virtual switch
                if not pg_obj.config.distributedVirtualSwitch:
                    self.module.fail_json(msg="Failed to find distributed virtual switch which is associated with"
                                              " distributed virtual portgroup '%s'. Make sure hostsystem is associated with"
                                              " the given distributed virtual portgroup." % pg_obj.name)
                dvs_port_connection.switchUuid = pg_obj.config.distributedVirtualSwitch.uuid
                nic.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                nic.device.backing.port = dvs_port_connection

            elif isinstance(self.cache.get_network(network_name), vim.OpaqueNetwork):
                # NSX-T Logical Switch
                nic.device.backing = vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo()
                network_id = self.cache.get_network(network_name).summary.opaqueNetworkId
                nic.device.backing.opaqueNetworkType = 'nsx.LogicalSwitch'
                nic.device.backing.opaqueNetworkId = network_id
                nic.device.deviceInfo.summary = 'nsx.LogicalSwitch: %s' % network_id
            else:
                # vSwitch
                if not isinstance(nic.device.backing, vim.vm.device.VirtualEthernetCard.NetworkBackingInfo):
                    nic.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                    nic_change_detected = True

                net_obj = self.cache.get_network(network_name)
                if nic.device.backing.network != net_obj:
                    nic.device.backing.network = net_obj
                    nic_change_detected = True

                if nic.device.backing.deviceName != network_name:
                    nic.device.backing.deviceName = network_name
                    nic_change_detected = True

            if nic_change_detected:
                self.configspec.deviceChange.append(nic)
                self.change_detected = True

    def configure_vapp_properties(self, vm_obj):
        if len(self.params['vapp_properties']) == 0:
            return

        for x in self.params['vapp_properties']:
            if not x.get('id'):
                self.module.fail_json(msg="id is required to set vApp property")

        new_vmconfig_spec = vim.vApp.VmConfigSpec()

        # This is primarily for vcsim/integration tests, unset vAppConfig was not seen on my deployments
        orig_spec = vm_obj.config.vAppConfig if vm_obj.config.vAppConfig else new_vmconfig_spec

        vapp_properties_current = dict((x.id, x) for x in orig_spec.property)
        vapp_properties_to_change = dict((x['id'], x) for x in self.params['vapp_properties'])

        # each property must have a unique key
        # init key counter with max value + 1
        all_keys = [x.key for x in orig_spec.property]
        new_property_index = max(all_keys) + 1 if all_keys else 0

        for property_id, property_spec in vapp_properties_to_change.items():
            is_property_changed = False
            new_vapp_property_spec = vim.vApp.PropertySpec()

            if property_id in vapp_properties_current:
                if property_spec.get('operation') == 'remove':
                    new_vapp_property_spec.operation = 'remove'
                    new_vapp_property_spec.removeKey = vapp_properties_current[property_id].key
                    is_property_changed = True
                else:
                    # this is 'edit' branch
                    new_vapp_property_spec.operation = 'edit'
                    new_vapp_property_spec.info = vapp_properties_current[property_id]
                    try:
                        for property_name, property_value in property_spec.items():

                            if property_name == 'operation':
                                # operation is not an info object property
                                # if set to anything other than 'remove' we don't fail
                                continue

                            # Updating attributes only if needed
                            if getattr(new_vapp_property_spec.info, property_name) != property_value:
                                setattr(new_vapp_property_spec.info, property_name, property_value)
                                is_property_changed = True

                    except Exception as e:
                        self.module.fail_json(msg="Failed to set vApp property field='%s' and value='%s'. Error: %s"
                                              % (property_name, property_value, to_text(e)))
            else:
                if property_spec.get('operation') == 'remove':
                    # attemp to delete non-existent property
                    continue

                # this is add new property branch
                new_vapp_property_spec.operation = 'add'

                property_info = vim.vApp.PropertyInfo()
                property_info.classId = property_spec.get('classId')
                property_info.instanceId = property_spec.get('instanceId')
                property_info.id = property_spec.get('id')
                property_info.category = property_spec.get('category')
                property_info.label = property_spec.get('label')
                property_info.type = property_spec.get('type', 'string')
                property_info.userConfigurable = property_spec.get('userConfigurable', True)
                property_info.defaultValue = property_spec.get('defaultValue')
                property_info.value = property_spec.get('value', '')
                property_info.description = property_spec.get('description')

                new_vapp_property_spec.info = property_info
                new_vapp_property_spec.info.key = new_property_index
                new_property_index += 1
                is_property_changed = True
            if is_property_changed:
                new_vmconfig_spec.property.append(new_vapp_property_spec)
        if new_vmconfig_spec.property:
            self.configspec.vAppConfig = new_vmconfig_spec
            self.change_detected = True

    def customize_customvalues(self, vm_obj, config_spec):
        if len(self.params['customvalues']) == 0:
            return

        vm_custom_spec = config_spec
        vm_custom_spec.extraConfig = []

        changed = False
        facts = self.gather_facts(vm_obj)
        for kv in self.params['customvalues']:
            if 'key' not in kv or 'value' not in kv:
                self.module.exit_json(msg="customvalues items required both 'key' and 'value fields.")

            # If kv is not kv fetched from facts, change it
            if kv['key'] not in facts['customvalues'] or facts['customvalues'][kv['key']] != kv['value']:
                option = vim.option.OptionValue()
                option.key = kv['key']
                option.value = kv['value']

                vm_custom_spec.extraConfig.append(option)
                changed = True

        if changed:
            self.change_detected = True

    def customize_vm(self, vm_obj):

        # User specified customization specification
        custom_spec_name = self.params.get('customization_spec')
        if custom_spec_name:
            cc_mgr = self.content.customizationSpecManager
            if cc_mgr.DoesCustomizationSpecExist(name=custom_spec_name):
                temp_spec = cc_mgr.GetCustomizationSpec(name=custom_spec_name)
                self.customspec = temp_spec.spec
                return
            else:
                self.module.fail_json(msg="Unable to find customization specification"
                                          " '%s' in given configuration." % custom_spec_name)

        # Network settings
        adaptermaps = []
        for network in self.params['networks']:

            guest_map = vim.vm.customization.AdapterMapping()
            guest_map.adapter = vim.vm.customization.IPSettings()

            if 'ip' in network and 'netmask' in network:
                guest_map.adapter.ip = vim.vm.customization.FixedIp()
                guest_map.adapter.ip.ipAddress = str(network['ip'])
                guest_map.adapter.subnetMask = str(network['netmask'])
            elif 'type' in network and network['type'] == 'dhcp':
                guest_map.adapter.ip = vim.vm.customization.DhcpIpGenerator()

            if 'gateway' in network:
                guest_map.adapter.gateway = network['gateway']

            # On Windows, DNS domain and DNS servers can be set by network interface
            # https://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.vm.customization.IPSettings.html
            if 'domain' in network:
                guest_map.adapter.dnsDomain = network['domain']
            elif 'domain' in self.params['customization']:
                guest_map.adapter.dnsDomain = self.params['customization']['domain']

            if 'dns_servers' in network:
                guest_map.adapter.dnsServerList = network['dns_servers']
            elif 'dns_servers' in self.params['customization']:
                guest_map.adapter.dnsServerList = self.params['customization']['dns_servers']

            adaptermaps.append(guest_map)

        # Global DNS settings
        globalip = vim.vm.customization.GlobalIPSettings()
        if 'dns_servers' in self.params['customization']:
            globalip.dnsServerList = self.params['customization']['dns_servers']

        # TODO: Maybe list the different domains from the interfaces here by default ?
        if 'dns_suffix' in self.params['customization']:
            dns_suffix = self.params['customization']['dns_suffix']
            if isinstance(dns_suffix, list):
                globalip.dnsSuffixList = " ".join(dns_suffix)
            else:
                globalip.dnsSuffixList = dns_suffix
        elif 'domain' in self.params['customization']:
            globalip.dnsSuffixList = self.params['customization']['domain']

        if self.params['guest_id']:
            guest_id = self.params['guest_id']
        else:
            guest_id = vm_obj.summary.config.guestId

        # For windows guest OS, use SysPrep
        # https://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.vm.customization.Sysprep.html#field_detail
        if 'win' in guest_id:
            ident = vim.vm.customization.Sysprep()

            ident.userData = vim.vm.customization.UserData()

            # Setting hostName, orgName and fullName is mandatory, so we set some default when missing
            ident.userData.computerName = vim.vm.customization.FixedName()
            # computer name will be truncated to 15 characters if using VM name
            default_name = self.params['name'].translate(None, string.punctuation)
            ident.userData.computerName.name = str(self.params['customization'].get('hostname', default_name[0:15]))
            ident.userData.fullName = str(self.params['customization'].get('fullname', 'Administrator'))
            ident.userData.orgName = str(self.params['customization'].get('orgname', 'ACME'))

            if 'productid' in self.params['customization']:
                ident.userData.productId = str(self.params['customization']['productid'])

            ident.guiUnattended = vim.vm.customization.GuiUnattended()

            if 'autologon' in self.params['customization']:
                ident.guiUnattended.autoLogon = self.params['customization']['autologon']
                ident.guiUnattended.autoLogonCount = self.params['customization'].get('autologoncount', 1)

            if 'timezone' in self.params['customization']:
                # Check if timezone value is a int before proceeding.
                ident.guiUnattended.timeZone = self.device_helper.integer_value(
                    self.params['customization']['timezone'],
                    'customization.timezone')

            ident.identification = vim.vm.customization.Identification()

            if self.params['customization'].get('password', '') != '':
                ident.guiUnattended.password = vim.vm.customization.Password()
                ident.guiUnattended.password.value = str(self.params['customization']['password'])
                ident.guiUnattended.password.plainText = True

            if 'joindomain' in self.params['customization']:
                if 'domainadmin' not in self.params['customization'] or 'domainadminpassword' not in self.params['customization']:
                    self.module.fail_json(msg="'domainadmin' and 'domainadminpassword' entries are mandatory in 'customization' section to use "
                                              "joindomain feature")

                ident.identification.domainAdmin = str(self.params['customization']['domainadmin'])
                ident.identification.joinDomain = str(self.params['customization']['joindomain'])
                ident.identification.domainAdminPassword = vim.vm.customization.Password()
                ident.identification.domainAdminPassword.value = str(self.params['customization']['domainadminpassword'])
                ident.identification.domainAdminPassword.plainText = True

            elif 'joinworkgroup' in self.params['customization']:
                ident.identification.joinWorkgroup = str(self.params['customization']['joinworkgroup'])

            if 'runonce' in self.params['customization']:
                ident.guiRunOnce = vim.vm.customization.GuiRunOnce()
                ident.guiRunOnce.commandList = self.params['customization']['runonce']

        else:
            # FIXME: We have no clue whether this non-Windows OS is actually Linux, hence it might fail!

            # For Linux guest OS, use LinuxPrep
            # https://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.vm.customization.LinuxPrep.html
            ident = vim.vm.customization.LinuxPrep()

            # TODO: Maybe add domain from interface if missing ?
            if 'domain' in self.params['customization']:
                ident.domain = str(self.params['customization']['domain'])

            ident.hostName = vim.vm.customization.FixedName()
            hostname = str(self.params['customization'].get('hostname', self.params['name'].split('.')[0]))
            # Remove all characters except alphanumeric and minus which is allowed by RFC 952
            valid_hostname = re.sub(r"[^a-zA-Z0-9\-]", "", hostname)
            ident.hostName.name = valid_hostname

        self.customspec = vim.vm.customization.Specification()
        self.customspec.nicSettingMap = adaptermaps
        self.customspec.globalIPSettings = globalip
        self.customspec.identity = ident

    def get_vm_scsi_controller(self, vm_obj):
        # If vm_obj doesn't exist there is no SCSI controller to find
        if vm_obj is None:
            return None

        for device in vm_obj.config.hardware.device:
            if self.device_helper.is_scsi_controller(device):
                scsi_ctl = vim.vm.device.VirtualDeviceSpec()
                scsi_ctl.device = device
                return scsi_ctl

        return None

    def get_configured_disk_size(self, expected_disk_spec):
        # what size is it?
        if [x for x in expected_disk_spec.keys() if x.startswith('size_') or x == 'size']:
            # size, size_tb, size_gb, size_mb, size_kb
            if 'size' in expected_disk_spec:
                size_regex = re.compile(r'(\d+(?:\.\d+)?)([tgmkTGMK][bB])')
                disk_size_m = size_regex.match(expected_disk_spec['size'])
                try:
                    if disk_size_m:
                        expected = disk_size_m.group(1)
                        unit = disk_size_m.group(2)
                    else:
                        raise ValueError

                    if re.match(r'\d+\.\d+', expected):
                        # We found float value in string, let's typecast it
                        expected = float(expected)
                    else:
                        # We found int value in string, let's typecast it
                        expected = int(expected)

                    if not expected or not unit:
                        raise ValueError

                except (TypeError, ValueError, NameError):
                    # Common failure
                    self.module.fail_json(msg="Failed to parse disk size please review value"
                                              " provided using documentation.")
            else:
                param = [x for x in expected_disk_spec.keys() if x.startswith('size_')][0]
                unit = param.split('_')[-1].lower()
                expected = [x[1] for x in expected_disk_spec.items() if x[0].startswith('size_')][0]
                expected = int(expected)

            disk_units = dict(tb=3, gb=2, mb=1, kb=0)
            if unit in disk_units:
                unit = unit.lower()
                return expected * (1024 ** disk_units[unit])
            else:
                self.module.fail_json(msg="%s is not a supported unit for disk size."
                                          " Supported units are ['%s']." % (unit,
                                                                            "', '".join(disk_units.keys())))

        # No size found but disk, fail
        self.module.fail_json(
            msg="No size, size_kb, size_mb, size_gb or size_tb attribute found into disk configuration")

    def find_vmdk(self, vmdk_path):
        """
        Takes a vsphere datastore path in the format

            [datastore_name] path/to/file.vmdk

        Returns vsphere file object or raises RuntimeError
        """
        datastore_name, vmdk_fullpath, vmdk_filename, vmdk_folder = self.vmdk_disk_path_split(vmdk_path)

        datastore = self.cache.find_obj(self.content, [vim.Datastore], datastore_name)

        if datastore is None:
            self.module.fail_json(msg="Failed to find the datastore %s" % datastore_name)

        return self.find_vmdk_file(datastore, vmdk_fullpath, vmdk_filename, vmdk_folder)

    def add_existing_vmdk(self, vm_obj, expected_disk_spec, diskspec, scsi_ctl):
        """
        Adds vmdk file described by expected_disk_spec['filename'], retrieves the file
        information and adds the correct spec to self.configspec.deviceChange.
        """
        filename = expected_disk_spec['filename']
        # if this is a new disk, or the disk file names are different
        if (vm_obj and diskspec.device.backing.fileName != filename) or vm_obj is None:
            vmdk_file = self.find_vmdk(expected_disk_spec['filename'])
            diskspec.device.backing.fileName = expected_disk_spec['filename']
            diskspec.device.capacityInKB = VmomiSupport.vmodlTypes['long'](vmdk_file.fileSize / 1024)
            diskspec.device.key = -1
            self.change_detected = True
            self.configspec.deviceChange.append(diskspec)

    def configure_disks(self, vm_obj):
        # Ignore empty disk list, this permits to keep disks when deploying a template/cloning a VM
        if len(self.params['disk']) == 0:
            return

        scsi_ctl = self.get_vm_scsi_controller(vm_obj)

        # Create scsi controller only if we are deploying a new VM, not a template or reconfiguring
        if vm_obj is None or scsi_ctl is None:
            scsi_ctl = self.device_helper.create_scsi_controller(self.get_scsi_type())
            self.change_detected = True
            self.configspec.deviceChange.append(scsi_ctl)

        disks = [x for x in vm_obj.config.hardware.device if isinstance(x, vim.vm.device.VirtualDisk)] \
            if vm_obj is not None else None

        if disks is not None and self.params.get('disk') and len(self.params.get('disk')) < len(disks):
            self.module.fail_json(msg="Provided disks configuration has less disks than "
                                      "the target object (%d vs %d)" % (len(self.params.get('disk')), len(disks)))

        disk_index = 0
        for expected_disk_spec in self.params.get('disk'):
            disk_modified = False
            # If we are manipulating and existing objects which has disks and disk_index is in disks
            if vm_obj is not None and disks is not None and disk_index < len(disks):
                diskspec = vim.vm.device.VirtualDeviceSpec()
                # set the operation to edit so that it knows to keep other settings
                diskspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                diskspec.device = disks[disk_index]
            else:
                diskspec = self.device_helper.create_scsi_disk(scsi_ctl, disk_index)
                disk_modified = True

            # increment index for next disk search
            disk_index += 1
            # index 7 is reserved to SCSI controller
            if disk_index == 7:
                disk_index += 1

            if 'disk_mode' in expected_disk_spec:
                disk_mode = expected_disk_spec.get('disk_mode', 'persistent').lower()
                valid_disk_mode = ['persistent', 'independent_persistent', 'independent_nonpersistent']
                if disk_mode not in valid_disk_mode:
                    self.module.fail_json(msg="disk_mode specified is not valid."
                                              " Should be one of ['%s']" % "', '".join(valid_disk_mode))

                if (vm_obj and diskspec.device.backing.diskMode != disk_mode) or (vm_obj is None):
                    diskspec.device.backing.diskMode = disk_mode
                    disk_modified = True
            else:
                diskspec.device.backing.diskMode = "persistent"

            # is it thin?
            if 'type' in expected_disk_spec:
                disk_type = expected_disk_spec.get('type', '').lower()
                if disk_type == 'thin':
                    diskspec.device.backing.thinProvisioned = True
                elif disk_type == 'eagerzeroedthick':
                    diskspec.device.backing.eagerlyScrub = True

            if 'filename' in expected_disk_spec and expected_disk_spec['filename'] is not None:
                self.add_existing_vmdk(vm_obj, expected_disk_spec, diskspec, scsi_ctl)
                continue
            elif vm_obj is None or self.params['template']:
                # We are creating new VM or from Template
                diskspec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create

            # which datastore?
            if expected_disk_spec.get('datastore'):
                # TODO: This is already handled by the relocation spec,
                # but it needs to eventually be handled for all the
                # other disks defined
                pass

            kb = self.get_configured_disk_size(expected_disk_spec)
            # VMWare doesn't allow to reduce disk sizes
            if kb < diskspec.device.capacityInKB:
                self.module.fail_json(
                    msg="Given disk size is smaller than found (%d < %d). Reducing disks is not allowed." %
                        (kb, diskspec.device.capacityInKB))

            if kb != diskspec.device.capacityInKB or disk_modified:
                diskspec.device.capacityInKB = kb
                self.configspec.deviceChange.append(diskspec)

                self.change_detected = True

    def select_host(self):
        hostsystem = self.cache.get_esx_host(self.params['esxi_hostname'])
        if not hostsystem:
            self.module.fail_json(msg='Failed to find ESX host "%(esxi_hostname)s"' % self.params)
        if hostsystem.runtime.connectionState != 'connected' or hostsystem.runtime.inMaintenanceMode:
            self.module.fail_json(msg='ESXi "%(esxi_hostname)s" is in invalid state or in maintenance mode.' % self.params)
        return hostsystem

    def autoselect_datastore(self):
        datastore = None
        datastores = self.cache.get_all_objs(self.content, [vim.Datastore])

        if datastores is None or len(datastores) == 0:
            self.module.fail_json(msg="Unable to find a datastore list when autoselecting")

        datastore_freespace = 0
        for ds in datastores:
            if ds.summary.freeSpace > datastore_freespace:
                datastore = ds
                datastore_freespace = ds.summary.freeSpace

        return datastore

    def get_recommended_datastore(self, datastore_cluster_obj=None):
        """
        Function to return Storage DRS recommended datastore from datastore cluster
        Args:
            datastore_cluster_obj: datastore cluster managed object

        Returns: Name of recommended datastore from the given datastore cluster

        """
        if datastore_cluster_obj is None:
            return None
        # Check if Datastore Cluster provided by user is SDRS ready
        sdrs_status = datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.podConfig.enabled
        if sdrs_status:
            # We can get storage recommendation only if SDRS is enabled on given datastorage cluster
            pod_sel_spec = vim.storageDrs.PodSelectionSpec()
            pod_sel_spec.storagePod = datastore_cluster_obj
            storage_spec = vim.storageDrs.StoragePlacementSpec()
            storage_spec.podSelectionSpec = pod_sel_spec
            storage_spec.type = 'create'

            try:
                rec = self.content.storageResourceManager.RecommendDatastores(storageSpec=storage_spec)
                rec_action = rec.recommendations[0].action[0]
                return rec_action.destination.name
            except Exception:
                # There is some error so we fall back to general workflow
                pass
        datastore = None
        datastore_freespace = 0
        for ds in datastore_cluster_obj.childEntity:
            if isinstance(ds, vim.Datastore) and ds.summary.freeSpace > datastore_freespace:
                # If datastore field is provided, filter destination datastores
                datastore = ds
                datastore_freespace = ds.summary.freeSpace
        if datastore:
            return datastore.name
        return None

    def select_datastore(self, vm_obj=None):
        datastore = None
        datastore_name = None

        if len(self.params['disk']) != 0:
            # TODO: really use the datastore for newly created disks
            if 'autoselect_datastore' in self.params['disk'][0] and self.params['disk'][0]['autoselect_datastore']:
                datastores = self.cache.get_all_objs(self.content, [vim.Datastore])
                datastores = [x for x in datastores if self.cache.get_parent_datacenter(x).name == self.params['datacenter']]
                if datastores is None or len(datastores) == 0:
                    self.module.fail_json(msg="Unable to find a datastore list when autoselecting")

                datastore_freespace = 0
                for ds in datastores:
                    if (ds.summary.freeSpace > datastore_freespace) or (ds.summary.freeSpace == datastore_freespace and not datastore):
                        # If datastore field is provided, filter destination datastores
                        if 'datastore' in self.params['disk'][0] and \
                                isinstance(self.params['disk'][0]['datastore'], str) and \
                                ds.name.find(self.params['disk'][0]['datastore']) < 0:
                            continue

                        datastore = ds
                        datastore_name = datastore.name
                        datastore_freespace = ds.summary.freeSpace

            elif 'datastore' in self.params['disk'][0]:
                datastore_name = self.params['disk'][0]['datastore']
                # Check if user has provided datastore cluster first
                datastore_cluster = self.cache.find_obj(self.content, [vim.StoragePod], datastore_name)
                if datastore_cluster:
                    # If user specified datastore cluster so get recommended datastore
                    datastore_name = self.get_recommended_datastore(datastore_cluster_obj=datastore_cluster)
                # Check if get_recommended_datastore or user specified datastore exists or not
                datastore = self.cache.find_obj(self.content, [vim.Datastore], datastore_name)
            else:
                self.module.fail_json(msg="Either datastore or autoselect_datastore should be provided to select datastore")

        if not datastore and self.params['template']:
            # use the template's existing DS
            disks = [x for x in vm_obj.config.hardware.device if isinstance(x, vim.vm.device.VirtualDisk)]
            if disks:
                datastore = disks[0].backing.datastore
                datastore_name = datastore.name
            # validation
            if datastore:
                dc = self.cache.get_parent_datacenter(datastore)
                if dc.name != self.params['datacenter']:
                    datastore = self.autoselect_datastore()
                    datastore_name = datastore.name

        if not datastore:
            if len(self.params['disk']) != 0 or self.params['template'] is None:
                self.module.fail_json(msg="Unable to find the datastore with given parameters."
                                          " This could mean, %s is a non-existent virtual machine and module tried to"
                                          " deploy it as new virtual machine with no disk. Please specify disks parameter"
                                          " or specify template to clone from." % self.params['name'])
            self.module.fail_json(msg="Failed to find a matching datastore")

        return datastore, datastore_name

    def obj_has_parent(self, obj, parent):
        if obj is None and parent is None:
            raise AssertionError()
        current_parent = obj

        while True:
            if current_parent.name == parent.name:
                return True

            # Check if we have reached till root folder
            moid = current_parent._moId
            if moid in ['group-d1', 'ha-folder-root']:
                return False

            current_parent = current_parent.parent
            if current_parent is None:
                return False

    def get_scsi_type(self):
        disk_controller_type = "paravirtual"
        # set cpu/memory/etc
        if 'hardware' in self.params:
            if 'scsi' in self.params['hardware']:
                if self.params['hardware']['scsi'] in ['buslogic', 'paravirtual', 'lsilogic', 'lsilogicsas']:
                    disk_controller_type = self.params['hardware']['scsi']
                else:
                    self.module.fail_json(msg="hardware.scsi attribute should be 'paravirtual' or 'lsilogic'")
        return disk_controller_type

    def find_folder(self, searchpath):
        """ Walk inventory objects one position of the searchpath at a time """

        # split the searchpath so we can iterate through it
        paths = [x.replace('/', '') for x in searchpath.split('/')]
        paths_total = len(paths) - 1
        position = 0

        # recursive walk while looking for next element in searchpath
        root = self.content.rootFolder
        while root and position <= paths_total:
            change = False
            if hasattr(root, 'childEntity'):
                for child in root.childEntity:
                    if child.name == paths[position]:
                        root = child
                        position += 1
                        change = True
                        break
            elif isinstance(root, vim.Datacenter):
                if hasattr(root, 'vmFolder'):
                    if root.vmFolder.name == paths[position]:
                        root = root.vmFolder
                        position += 1
                        change = True
            else:
                root = None

            if not change:
                root = None

        return root

    def get_resource_pool(self, cluster=None, host=None, resource_pool=None):
        """ Get a resource pool, filter on cluster, esxi_hostname or resource_pool if given """

        cluster_name = cluster or self.params.get('cluster', None)
        host_name = host or self.params.get('esxi_hostname', None)
        resource_pool_name = resource_pool or self.params.get('resource_pool', None)

        # get the datacenter object
        datacenter = find_obj(self.content, [vim.Datacenter], self.params['datacenter'])
        if not datacenter:
            self.module.fail_json(msg='Unable to find datacenter "%s"' % self.params['datacenter'])

        # if cluster is given, get the cluster object
        if cluster_name:
            cluster = find_obj(self.content, [vim.ComputeResource], cluster_name, folder=datacenter)
            if not cluster:
                self.module.fail_json(msg='Unable to find cluster "%s"' % cluster_name)
        # if host is given, get the cluster object using the host
        elif host_name:
            host = find_obj(self.content, [vim.HostSystem], host_name, folder=datacenter)
            if not host:
                self.module.fail_json(msg='Unable to find host "%s"' % host_name)
            cluster = host.parent
        else:
            cluster = None

        # get resource pools limiting search to cluster or datacenter
        resource_pool = find_obj(self.content, [vim.ResourcePool], resource_pool_name, folder=cluster or datacenter)
        if not resource_pool:
            if resource_pool_name:
                self.module.fail_json(msg='Unable to find resource_pool "%s"' % resource_pool_name)
            else:
                self.module.fail_json(msg='Unable to find resource pool, need esxi_hostname, resource_pool, or cluster')
        return resource_pool

    def deploy_vm(self):
        # https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/clone_vm.py
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.vm.CloneSpec.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.vm.ConfigSpec.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk41pubs/ApiReference/vim.vm.RelocateSpec.html

        # FIXME:
        #   - static IPs

        self.folder = self.params.get('folder', None)
        if self.folder is None:
            self.module.fail_json(msg="Folder is required parameter while deploying new virtual machine")

        # Prepend / if it was missing from the folder path, also strip trailing slashes
        if not self.folder.startswith('/'):
            self.folder = '/%(folder)s' % self.params
        self.folder = self.folder.rstrip('/')

        datacenter = self.cache.find_obj(self.content, [vim.Datacenter], self.params['datacenter'])
        if datacenter is None:
            self.module.fail_json(msg='No datacenter named %(datacenter)s was found' % self.params)

        dcpath = compile_folder_path_for_object(datacenter)

        # Nested folder does not have trailing /
        if not dcpath.endswith('/'):
            dcpath += '/'

        # Check for full path first in case it was already supplied
        if (self.folder.startswith(dcpath + self.params['datacenter'] + '/vm') or
                self.folder.startswith(dcpath + '/' + self.params['datacenter'] + '/vm')):
            fullpath = self.folder
        elif self.folder.startswith('/vm/') or self.folder == '/vm':
            fullpath = "%s%s%s" % (dcpath, self.params['datacenter'], self.folder)
        elif self.folder.startswith('/'):
            fullpath = "%s%s/vm%s" % (dcpath, self.params['datacenter'], self.folder)
        else:
            fullpath = "%s%s/vm/%s" % (dcpath, self.params['datacenter'], self.folder)

        f_obj = self.content.searchIndex.FindByInventoryPath(fullpath)

        # abort if no strategy was successful
        if f_obj is None:
            # Add some debugging values in failure.
            details = {
                'datacenter': datacenter.name,
                'datacenter_path': dcpath,
                'folder': self.folder,
                'full_search_path': fullpath,
            }
            self.module.fail_json(msg='No folder %s matched in the search path : %s' % (self.folder, fullpath),
                                  details=details)

        destfolder = f_obj

        if self.params['template']:
            vm_obj = self.get_vm_or_template(template_name=self.params['template'])
            if vm_obj is None:
                self.module.fail_json(msg="Could not find a template named %(template)s" % self.params)
        else:
            vm_obj = None

        # always get a resource_pool
        resource_pool = self.get_resource_pool()

        # set the destination datastore for VM & disks
        if self.params['datastore']:
            # Give precedence to datastore value provided by user
            # User may want to deploy VM to specific datastore.
            datastore_name = self.params['datastore']
            # Check if user has provided datastore cluster first
            datastore_cluster = self.cache.find_obj(self.content, [vim.StoragePod], datastore_name)
            if datastore_cluster:
                # If user specified datastore cluster so get recommended datastore
                datastore_name = self.get_recommended_datastore(datastore_cluster_obj=datastore_cluster)
            # Check if get_recommended_datastore or user specified datastore exists or not
            datastore = self.cache.find_obj(self.content, [vim.Datastore], datastore_name)
        else:
            (datastore, datastore_name) = self.select_datastore(vm_obj)

        self.configspec = vim.vm.ConfigSpec()
        self.configspec.deviceChange = []
        self.configure_guestid(vm_obj=vm_obj, vm_creation=True)
        self.configure_cpu_and_memory(vm_obj=vm_obj, vm_creation=True)
        self.configure_hardware_params(vm_obj=vm_obj)
        self.configure_resource_alloc_info(vm_obj=vm_obj)
        self.configure_disks(vm_obj=vm_obj)
        self.configure_network(vm_obj=vm_obj)
        self.configure_cdrom(vm_obj=vm_obj)

        # Find if we need network customizations (find keys in dictionary that requires customizations)
        network_changes = False
        for nw in self.params['networks']:
            for key in nw:
                # We don't need customizations for these keys
                if key not in ('device_type', 'mac', 'name', 'vlan', 'type', 'start_connected'):
                    network_changes = True
                    break

        if len(self.params['customization']) > 0 or network_changes or self.params.get('customization_spec') is not None:
            self.customize_vm(vm_obj=vm_obj)

        clonespec = None
        clone_method = None
        try:
            if self.params['template']:
                # create the relocation spec
                relospec = vim.vm.RelocateSpec()

                # Only select specific host when ESXi hostname is provided
                if self.params['esxi_hostname']:
                    relospec.host = self.select_host()
                relospec.datastore = datastore

                # Convert disk present in template if is set
                if self.params['convert']:
                    for device in vm_obj.config.hardware.device:
                        if hasattr(device.backing, 'fileName'):
                            disk_locator = vim.vm.RelocateSpec.DiskLocator()
                            disk_locator.diskBackingInfo = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
                            if self.params['convert'] in ['thin']:
                                disk_locator.diskBackingInfo.thinProvisioned = True
                            if self.params['convert'] in ['eagerzeroedthick']:
                                disk_locator.diskBackingInfo.eagerlyScrub = True
                            if self.params['convert'] in ['thick']:
                                disk_locator.diskBackingInfo.diskMode = "persistent"
                            disk_locator.diskId = device.key
                            disk_locator.datastore = datastore
                            relospec.disk.append(disk_locator)

                # https://www.vmware.com/support/developer/vc-sdk/visdk41pubs/ApiReference/vim.vm.RelocateSpec.html
                # > pool: For a clone operation from a template to a virtual machine, this argument is required.
                relospec.pool = resource_pool

                linked_clone = self.params.get('linked_clone')
                snapshot_src = self.params.get('snapshot_src', None)
                if linked_clone:
                    if snapshot_src is not None:
                        relospec.diskMoveType = vim.vm.RelocateSpec.DiskMoveOptions.createNewChildDiskBacking
                    else:
                        self.module.fail_json(msg="Parameter 'linked_src' and 'snapshot_src' are"
                                                  " required together for linked clone operation.")

                clonespec = vim.vm.CloneSpec(template=self.params['is_template'], location=relospec)
                if self.customspec:
                    clonespec.customization = self.customspec

                if snapshot_src is not None:
                    if vm_obj.snapshot is None:
                        self.module.fail_json(msg="No snapshots present for virtual machine or template [%(template)s]" % self.params)
                    snapshot = self.get_snapshots_by_name_recursively(snapshots=vm_obj.snapshot.rootSnapshotList,
                                                                      snapname=snapshot_src)
                    if len(snapshot) != 1:
                        self.module.fail_json(msg='virtual machine "%(template)s" does not contain'
                                                  ' snapshot named "%(snapshot_src)s"' % self.params)

                    clonespec.snapshot = snapshot[0].snapshot

                clonespec.config = self.configspec
                clone_method = 'Clone'
                try:
                    task = vm_obj.Clone(folder=destfolder, name=self.params['name'], spec=clonespec)
                except vim.fault.NoPermission as e:
                    self.module.fail_json(msg="Failed to clone virtual machine %s to folder %s "
                                              "due to permission issue: %s" % (self.params['name'],
                                                                               destfolder,
                                                                               to_native(e.msg)))
                self.change_detected = True
            else:
                # ConfigSpec require name for VM creation
                self.configspec.name = self.params['name']
                self.configspec.files = vim.vm.FileInfo(logDirectory=None,
                                                        snapshotDirectory=None,
                                                        suspendDirectory=None,
                                                        vmPathName="[" + datastore_name + "]")

                clone_method = 'CreateVM_Task'
                try:
                    task = destfolder.CreateVM_Task(config=self.configspec, pool=resource_pool)
                except vmodl.fault.InvalidRequest as e:
                    self.module.fail_json(msg="Failed to create virtual machine due to invalid configuration "
                                              "parameter %s" % to_native(e.msg))
                except vim.fault.RestrictedVersion as e:
                    self.module.fail_json(msg="Failed to create virtual machine due to "
                                              "product versioning restrictions: %s" % to_native(e.msg))
                self.change_detected = True
            self.wait_for_task(task)
        except TypeError as e:
            self.module.fail_json(msg="TypeError was returned, please ensure to give correct inputs. %s" % to_text(e))

        if task.info.state == 'error':
            # https://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=2021361
            # https://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=2173

            # provide these to the user for debugging
            clonespec_json = serialize_spec(clonespec)
            configspec_json = serialize_spec(self.configspec)
            kwargs = {
                'changed': self.change_applied,
                'failed': True,
                'msg': task.info.error.msg,
                'clonespec': clonespec_json,
                'configspec': configspec_json,
                'clone_method': clone_method
            }

            return kwargs
        else:
            # set annotation
            vm = task.info.result
            if self.params['annotation']:
                annotation_spec = vim.vm.ConfigSpec()
                annotation_spec.annotation = str(self.params['annotation'])
                task = vm.ReconfigVM_Task(annotation_spec)
                self.wait_for_task(task)
                if task.info.state == 'error':
                    return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'annotation'}

            if self.params['customvalues']:
                vm_custom_spec = vim.vm.ConfigSpec()
                self.customize_customvalues(vm_obj=vm, config_spec=vm_custom_spec)
                task = vm.ReconfigVM_Task(vm_custom_spec)
                self.wait_for_task(task)
                if task.info.state == 'error':
                    return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'customvalues'}

            if self.params['wait_for_ip_address'] or self.params['wait_for_customization'] or self.params['state'] in ['poweredon', 'restarted']:
                set_vm_power_state(self.content, vm, 'poweredon', force=False)

                if self.params['wait_for_ip_address']:
                    self.wait_for_vm_ip(vm)

                if self.params['wait_for_customization']:
                    is_customization_ok = self.wait_for_customization(vm)
                    if not is_customization_ok:
                        vm_facts = self.gather_facts(vm)
                        return {'changed': self.change_applied, 'failed': True, 'instance': vm_facts, 'op': 'customization'}

            vm_facts = self.gather_facts(vm)
            return {'changed': self.change_applied, 'failed': False, 'instance': vm_facts}

    def get_snapshots_by_name_recursively(self, snapshots, snapname):
        snap_obj = []
        for snapshot in snapshots:
            if snapshot.name == snapname:
                snap_obj.append(snapshot)
            else:
                snap_obj = snap_obj + self.get_snapshots_by_name_recursively(snapshot.childSnapshotList, snapname)
        return snap_obj

    def reconfigure_vm(self):
        self.configspec = vim.vm.ConfigSpec()
        self.configspec.deviceChange = []

        self.configure_guestid(vm_obj=self.current_vm_obj)
        self.configure_cpu_and_memory(vm_obj=self.current_vm_obj)
        self.configure_hardware_params(vm_obj=self.current_vm_obj)
        self.configure_disks(vm_obj=self.current_vm_obj)
        self.configure_network(vm_obj=self.current_vm_obj)
        self.configure_cdrom(vm_obj=self.current_vm_obj)
        self.customize_customvalues(vm_obj=self.current_vm_obj, config_spec=self.configspec)
        self.configure_resource_alloc_info(vm_obj=self.current_vm_obj)
        self.configure_vapp_properties(vm_obj=self.current_vm_obj)

        if self.params['annotation'] and self.current_vm_obj.config.annotation != self.params['annotation']:
            self.configspec.annotation = str(self.params['annotation'])
            self.change_detected = True

        relospec = vim.vm.RelocateSpec()
        if self.params['resource_pool']:
            relospec.pool = self.get_resource_pool()

            if relospec.pool != self.current_vm_obj.resourcePool:
                task = self.current_vm_obj.RelocateVM_Task(spec=relospec)
                self.wait_for_task(task)
                if task.info.state == 'error':
                    return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'relocate'}

        # Only send VMWare task if we see a modification
        if self.change_detected:
            task = None
            try:
                task = self.current_vm_obj.ReconfigVM_Task(spec=self.configspec)
            except vim.fault.RestrictedVersion as e:
                self.module.fail_json(msg="Failed to reconfigure virtual machine due to"
                                          " product versioning restrictions: %s" % to_native(e.msg))
            self.wait_for_task(task)
            if task.info.state == 'error':
                return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'reconfig'}

        # Rename VM
        if self.params['uuid'] and self.params['name'] and self.params['name'] != self.current_vm_obj.config.name:
            task = self.current_vm_obj.Rename_Task(self.params['name'])
            self.wait_for_task(task)
            if task.info.state == 'error':
                return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'rename'}

        # Mark VM as Template
        if self.params['is_template'] and not self.current_vm_obj.config.template:
            try:
                self.current_vm_obj.MarkAsTemplate()
                self.change_applied = True
            except vmodl.fault.NotSupported as e:
                self.module.fail_json(msg="Failed to mark virtual machine [%s] "
                                          "as template: %s" % (self.params['name'], e.msg))

        # Mark Template as VM
        elif not self.params['is_template'] and self.current_vm_obj.config.template:
            resource_pool = self.get_resource_pool()
            kwargs = dict(pool=resource_pool)

            if self.params.get('esxi_hostname', None):
                host_system_obj = self.select_host()
                kwargs.update(host=host_system_obj)

            try:
                self.current_vm_obj.MarkAsVirtualMachine(**kwargs)
                self.change_applied = True
            except vim.fault.InvalidState as invalid_state:
                self.module.fail_json(msg="Virtual machine is not marked"
                                          " as template : %s" % to_native(invalid_state.msg))
            except vim.fault.InvalidDatastore as invalid_ds:
                self.module.fail_json(msg="Converting template to virtual machine"
                                          " operation cannot be performed on the"
                                          " target datastores: %s" % to_native(invalid_ds.msg))
            except vim.fault.CannotAccessVmComponent as cannot_access:
                self.module.fail_json(msg="Failed to convert template to virtual machine"
                                          " as operation unable access virtual machine"
                                          " component: %s" % to_native(cannot_access.msg))
            except vmodl.fault.InvalidArgument as invalid_argument:
                self.module.fail_json(msg="Failed to convert template to virtual machine"
                                          " due to : %s" % to_native(invalid_argument.msg))
            except Exception as generic_exc:
                self.module.fail_json(msg="Failed to convert template to virtual machine"
                                          " due to generic error : %s" % to_native(generic_exc))

            # Automatically update VMWare UUID when converting template to VM.
            # This avoids an interactive prompt during VM startup.
            uuid_action = [x for x in self.current_vm_obj.config.extraConfig if x.key == "uuid.action"]
            if not uuid_action:
                uuid_action_opt = vim.option.OptionValue()
                uuid_action_opt.key = "uuid.action"
                uuid_action_opt.value = "create"
                self.configspec.extraConfig.append(uuid_action_opt)

            self.change_detected = True

        # add customize existing VM after VM re-configure
        if 'existing_vm' in self.params['customization'] and self.params['customization']['existing_vm']:
            if self.current_vm_obj.config.template:
                self.module.fail_json(msg="VM is template, not support guest OS customization.")
            if self.current_vm_obj.runtime.powerState != vim.VirtualMachinePowerState.poweredOff:
                self.module.fail_json(msg="VM is not in poweroff state, can not do guest OS customization.")
            cus_result = self.customize_exist_vm()
            if cus_result['failed']:
                return cus_result

        vm_facts = self.gather_facts(self.current_vm_obj)
        return {'changed': self.change_applied, 'failed': False, 'instance': vm_facts}

    def customize_exist_vm(self):
        task = None
        # Find if we need network customizations (find keys in dictionary that requires customizations)
        network_changes = False
        for nw in self.params['networks']:
            for key in nw:
                # We don't need customizations for these keys
                if key not in ('device_type', 'mac', 'name', 'vlan', 'type', 'start_connected'):
                    network_changes = True
                    break
        if len(self.params['customization']) > 1 or network_changes or self.params.get('customization_spec'):
            self.customize_vm(vm_obj=self.current_vm_obj)
        try:
            task = self.current_vm_obj.CustomizeVM_Task(self.customspec)
        except vim.fault.CustomizationFault as e:
            self.module.fail_json(msg="Failed to customization virtual machine due to CustomizationFault: %s" % to_native(e.msg))
        except vim.fault.RuntimeFault as e:
            self.module.fail_json(msg="failed to customization virtual machine due to RuntimeFault: %s" % to_native(e.msg))
        except Exception as e:
            self.module.fail_json(msg="failed to customization virtual machine due to fault: %s" % to_native(e.msg))
        self.wait_for_task(task)
        if task.info.state == 'error':
            return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'customize_exist'}

        if self.params['wait_for_customization']:
            set_vm_power_state(self.content, self.current_vm_obj, 'poweredon', force=False)
            is_customization_ok = self.wait_for_customization(self.current_vm_obj)
            if not is_customization_ok:
                return {'changed': self.change_applied, 'failed': True, 'op': 'wait_for_customize_exist'}

        return {'changed': self.change_applied, 'failed': False}

    def wait_for_task(self, task, poll_interval=1):
        """
        Wait for a VMware task to complete.  Terminal states are 'error' and 'success'.

        Inputs:
          - task: the task to wait for
          - poll_interval: polling interval to check the task, in seconds

        Modifies:
          - self.change_applied
        """
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.Task.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.TaskInfo.html
        # https://github.com/virtdevninja/pyvmomi-community-samples/blob/master/samples/tools/tasks.py
        while task.info.state not in ['error', 'success']:
            time.sleep(poll_interval)
        self.change_applied = self.change_applied or task.info.state == 'success'

    def wait_for_vm_ip(self, vm, poll=100, sleep=5):
        ips = None
        facts = {}
        thispoll = 0
        while not ips and thispoll <= poll:
            newvm = self.get_vm()
            facts = self.gather_facts(newvm)
            if facts['ipv4'] or facts['ipv6']:
                ips = True
            else:
                time.sleep(sleep)
                thispoll += 1

        return facts

    def get_vm_events(self, vm, eventTypeIdList):
        byEntity = vim.event.EventFilterSpec.ByEntity(entity=vm, recursion="self")
        filterSpec = vim.event.EventFilterSpec(entity=byEntity, eventTypeId=eventTypeIdList)
        eventManager = self.content.eventManager
        return eventManager.QueryEvent(filterSpec)

    def wait_for_customization(self, vm, poll=10000, sleep=10):
        thispoll = 0
        while thispoll <= poll:
            eventStarted = self.get_vm_events(vm, ['CustomizationStartedEvent'])
            if len(eventStarted):
                thispoll = 0
                while thispoll <= poll:
                    eventsFinishedResult = self.get_vm_events(vm, ['CustomizationSucceeded', 'CustomizationFailed'])
                    if len(eventsFinishedResult):
                        if not isinstance(eventsFinishedResult[0], vim.event.CustomizationSucceeded):
                            self.module.fail_json(msg='Customization failed with error {0}:\n{1}'.format(
                                eventsFinishedResult[0]._wsdlName, eventsFinishedResult[0].fullFormattedMessage))
                            return False
                        break
                    else:
                        time.sleep(sleep)
                        thispoll += 1
                return True
            else:
                time.sleep(sleep)
                thispoll += 1
        self.module.fail_json('waiting for customizations timed out.')
        return False


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present',
                   choices=['absent', 'poweredoff', 'poweredon', 'present', 'rebootguest', 'restarted', 'shutdownguest', 'suspended']),
        template=dict(type='str', aliases=['template_src']),
        is_template=dict(type='bool', default=False),
        annotation=dict(type='str', aliases=['notes']),
        customvalues=dict(type='list', default=[]),
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        folder=dict(type='str'),
        guest_id=dict(type='str'),
        disk=dict(type='list', default=[]),
        cdrom=dict(type='dict', default={}),
        hardware=dict(type='dict', default={}),
        force=dict(type='bool', default=False),
        datacenter=dict(type='str', default='ha-datacenter'),
        esxi_hostname=dict(type='str'),
        cluster=dict(type='str'),
        wait_for_ip_address=dict(type='bool', default=False),
        state_change_timeout=dict(type='int', default=0),
        snapshot_src=dict(type='str'),
        linked_clone=dict(type='bool', default=False),
        networks=dict(type='list', default=[]),
        resource_pool=dict(type='str'),
        customization=dict(type='dict', default={}, no_log=True),
        customization_spec=dict(type='str', default=None),
        wait_for_customization=dict(type='bool', default=False),
        vapp_properties=dict(type='list', default=[]),
        datastore=dict(type='str'),
        convert=dict(type='str', choices=['thin', 'thick', 'eagerzeroedthick']),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[
                               ['cluster', 'esxi_hostname'],
                           ],
                           required_one_of=[
                               ['name', 'uuid'],
                           ],
                           )

    result = {'failed': False, 'changed': False}

    pyv = PyVmomiHelper(module)

    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    # VM already exists
    if vm:
        if module.params['state'] == 'absent':
            # destroy it
            if module.check_mode:
                result.update(
                    vm_name=vm.name,
                    changed=True,
                    current_powerstate=vm.summary.runtime.powerState.lower(),
                    desired_operation='remove_vm',
                )
                module.exit_json(**result)
            if module.params['force']:
                # has to be poweredoff first
                set_vm_power_state(pyv.content, vm, 'poweredoff', module.params['force'])
            result = pyv.remove_vm(vm)
        elif module.params['state'] == 'present':
            if module.check_mode:
                result.update(
                    vm_name=vm.name,
                    changed=True,
                    desired_operation='reconfigure_vm',
                )
                module.exit_json(**result)
            result = pyv.reconfigure_vm()
        elif module.params['state'] in ['poweredon', 'poweredoff', 'restarted', 'suspended', 'shutdownguest', 'rebootguest']:
            if module.check_mode:
                result.update(
                    vm_name=vm.name,
                    changed=True,
                    current_powerstate=vm.summary.runtime.powerState.lower(),
                    desired_operation='set_vm_power_state',
                )
                module.exit_json(**result)
            # set powerstate
            tmp_result = set_vm_power_state(pyv.content, vm, module.params['state'], module.params['force'], module.params['state_change_timeout'])
            if tmp_result['changed']:
                result["changed"] = True
                if module.params['state'] in ['poweredon', 'restarted', 'rebootguest'] and module.params['wait_for_ip_address']:
                    wait_result = wait_for_vm_ip(pyv.content, vm)
                    if not wait_result:
                        module.fail_json(msg='Waiting for IP address timed out')
                    tmp_result['instance'] = wait_result
            if not tmp_result["failed"]:
                result["failed"] = False
            result['instance'] = tmp_result['instance']
            if tmp_result["failed"]:
                result["failed"] = True
                result["msg"] = tmp_result["msg"]
        else:
            # This should not happen
            raise AssertionError()
    # VM doesn't exist
    else:
        if module.params['state'] in ['poweredon', 'poweredoff', 'present', 'restarted', 'suspended']:
            if module.check_mode:
                result.update(
                    changed=True,
                    desired_operation='deploy_vm',
                )
                module.exit_json(**result)
            result = pyv.deploy_vm()
            if result['failed']:
                module.fail_json(msg='Failed to create a virtual machine : %s' % result['msg'])

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
