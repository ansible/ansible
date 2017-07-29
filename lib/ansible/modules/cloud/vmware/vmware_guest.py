#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This module is also sponsored by E.T.A.I. (www.etai.fr)
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest
short_description: Manages virtual machines in vcenter
description:
    - Create new virtual machines (from templates or not)
    - Power on/power off/restart a virtual machine
    - Modify, rename or remove a virtual machine
version_added: 2.2
author:
    - James Tanner (@jctanner) <tanner.jc@gmail.com>
    - Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
notes:
    - Tested on vSphere 5.5 and 6.0
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   state:
        description:
            - What state should the virtual machine be in?
            - If C(state) is set to C(present) and VM exists, ensure the VM configuration conforms to task arguments
        required: True
        choices: ['present', 'absent', 'poweredon', 'poweredoff', 'restarted', 'suspended', 'shutdownguest', 'rebootguest']
   name:
        description:
            - Name of the VM to work with
        required: True
   name_match:
        description:
            - If multiple VMs matching the name, use the first or last found
        default: 'first'
        choices: ['first', 'last']
   uuid:
        description:
            - UUID of the instance to manage if known, this is VMware's unique identifier.
            - This is required if name is not supplied.
   template:
        description:
            - Template used to create VM.
            - If this value is not set, VM is created without using a template.
            - If the VM exists already this setting will be ignored.
   is_template:
        description:
            - Flag the instance as a template
        default: False
        version_added: "2.3"
   folder:
        description:
            - Destination folder, absolute path to find an existing guest or create the new guest
   hardware:
        description:
            - "Manage some VM hardware attributes."
            - "Valid attributes are: memory_mb, num_cpus and scsi"
            - "scsi: Valid values are buslogic, lsilogic, lsilogicsas and paravirtual (default)"
   guest_id:
        description:
            - "Set the guest ID (Debian, RHEL, Windows...)"
            - "This field is required when creating a VM"
            - "Valid values are referenced here: https://www.vmware.com/support/developer/converter-sdk/conv55_apireference/vim.vm.GuestOsDescriptor.GuestOsIdentifier.html"
        version_added: "2.3"
   disk:
        description:
            - "A list of disks to add"
            - "Valid attributes are: size_[tb,gb,mb,kb], type, datastore and autoselect_datastore"
            - "type: Valid value is thin (default: None)"
            - "datastore: Datastore to use for the disk. If autoselect_datastore is True, filter datastore selection."
            - "autoselect_datastore (bool): select the less used datastore."
   resource_pool:
        description:
            - Affect machine to the given resource pool
            - Resource pool should be child of the selected host parent
        default: None
        version_added: "2.3"
   wait_for_ip_address:
        description:
            - Wait until vCenter detects an IP address for the VM
            - This requires vmware-tools (vmtoolsd) to properly work after creation
        default: False
   force:
        description:
            - Ignore warnings and complete the actions
   datacenter:
        description:
            - Destination datacenter for the deploy operation
        default: ha-datacenter
   cluster:
        description:
            - The cluster name where the VM will run.
        version_added: "2.3"
   esxi_hostname:
        description:
            - The esxi hostname where the VM will run.
   annotation:
        description:
            - A note or annotation to include in the VM
        version_added: "2.3"
   customvalues:
        description:
            - Define a list of customvalues to set on VM.
            - "A customvalue object takes 2 fields 'key' and 'value'."
        version_added: "2.3"
   networks:
        description:
          - Network to use should include C(name) or C(vlan) entry
          - Add an optional C(ip) and C(netmask) for network configuration
          - Add an optional C(gateway) entry to configure a gateway
          - Add an optional C(mac) entry to customize mac address
          - Add an optional C(dns_servers) or C(domain) entry per interface (Windows)
          - Add an optional C(device_type) to configure the virtual NIC (pcnet32, vmxnet2, vmxnet3, e1000, e1000e)
        version_added: "2.3"
   customization:
        description:
          - "Parameters to customize template"
          - "Common parameters (Linux/Windows):"
          - "  C(dns_servers) (list): List of DNS servers to configure"
          - "  C(dns_suffix) (list): List of domain suffixes, aka DNS search path (default: C(domain) parameter)"
          - "  C(domain) (string): DNS domain name to use"
          - "  C(hostname) (string): Computer hostname (default: C(name) parameter)"
          - "Parameters related to windows customization:"
          - "  C(autologon) (bool): Auto logon after VM customization (default: False)"
          - "  C(autologoncount) (int): Number of autologon after reboot (default: 1)"
          - "  C(domainadmin) (string): User used to join in AD domain (mandatory with joindomain)"
          - "  C(domainadminpassword) (string): Password used to join in AD domain (mandatory with joindomain)"
          - "  C(fullname) (string): Server owner name (default: Administrator)"
          - "  C(joindomain) (string): AD domain to join (Not compatible with C(joinworkgroup))"
          - "  C(joinworkgroup) (string): Workgroup to join (Not compatible with C(joindomain), default: WORKGROUP)"
          - "  C(orgname) (string): Organisation name (default: ACME)"
          - "  C(password) (string): Local administrator password (mandatory)"
          - "  C(productid) (string): Product ID"
          - "  C(runonce) (list): List of commands to run at first user logon"
          - "  C(timezone) (int): Timezone (default: 85) See U(https://msdn.microsoft.com/en-us/library/ms912391(v=winembedded.11).aspx)"
        version_added: "2.3"
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
# Create a VM from a template
  - name: create the VM
    vmware_guest:
      hostname: 192.0.2.44
      username: administrator@vsphere.local
      password: vmware
      validate_certs: no
      esxi_hostname: 192.0.2.117
      datacenter: datacenter1
      folder: testvms
      name: testvm_2
      state: poweredon
      guest_id: centos64guest
      disk:
      - size_gb: 10
        type: thin
        datastore: g73_datastore
      hardware:
        memory_mb: 512
        num_cpus: 1
        scsi: paravirtual
      networks:
      - name: VM Network
        ip: 192.168.1.100
        netmask: 255.255.255.0
        mac: 'aa:bb:dd:aa:00:14'
      template: template_el7
      wait_for_ip_address: yes
    register: deploy

# Clone a VM from Template and customize
  - name: Clone template and customize
    vmware_guest:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
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
        mac: 'aa:bb:dd:aa:00:14'
        domain: my_domain
        dns_servers:
        - 192.168.1.1
        - 192.168.1.2
      customization:
        autologon: True
        dns_servers:
        - 192.168.1.1
        - 192.168.1.2
        domain: my_domain
        password: new_vm_password
        runonce:
        - powershell.exe -ExecutionPolicy Unrestricted -File C:\Windows\Temp\Enable-WinRM.ps1 -ForceNewSSLCert

# Create a VM template
  - name: create a VM template
    vmware_guest:
      hostname: 192.0.2.88
      username: administrator@vsphere.local
      password: vmware
      validate_certs: no
      datacenter: datacenter1
      cluster: vmware_cluster_esx
      resource_pool: highperformance_pool
      folder: testvms
      name: testvm_6
      is_template: yes
      guest_id: debian6_64Guest
      disk:
      - size_gb: 10
        type: thin
        datastore: g73_datastore
      hardware:
        memory_mb: 512
        num_cpus: 1
        scsi: lsilogic
      wait_for_ip_address: yes
    register: deploy

# Rename a VM (requires the VM's uuid)
  - vmware_guest:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      uuid: 421e4592-c069-924d-ce20-7e7533fab926
      name: new_name
      state: present

# Remove a VM by uuid
  - vmware_guest:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      uuid: 421e4592-c069-924d-ce20-7e7533fab926
      state: absent
'''

RETURN = """
instance:
    descripton: metadata about the new virtualmachine
    returned: always
    type: dict
    sample: None
"""

import os
import time

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import get_all_objs, connect_to_api, gather_vm_facts

try:
    import json
except ImportError:
    import simplejson as json

HAS_PYVMOMI = False
try:
    import pyVmomi
    from pyVmomi import vim

    HAS_PYVMOMI = True
except ImportError:
    pass


class PyVmomiDeviceHelper(object):
    """ This class is a helper to create easily VMWare Objects for PyVmomiHelper """

    def __init__(self, module):
        self.module = module
        self.next_disk_unit_number = 0

    @staticmethod
    def create_scsi_controller(scsi_type):
        scsi_ctl = vim.vm.device.VirtualDeviceSpec()
        scsi_ctl.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        if scsi_type == 'lsilogic':
            scsi_ctl.device = vim.vm.device.VirtualLsiLogicController()
        elif scsi_type == 'paravirtual':
            scsi_ctl.device = vim.vm.device.ParaVirtualSCSIController()
        elif scsi_type == 'buslogic':
            scsi_ctl.device = vim.vm.device.VirtualBusLogicController()
        elif scsi_type == 'lsilogicsas':
            scsi_ctl.device = vim.vm.device.VirtualLsiLogicSASController()

        scsi_ctl.device.deviceInfo = vim.Description()
        scsi_ctl.device.slotInfo = vim.vm.device.VirtualDevice.PciBusSlotInfo()
        scsi_ctl.device.slotInfo.pciSlotNumber = 16
        scsi_ctl.device.controllerKey = 100
        scsi_ctl.device.unitNumber = 3
        scsi_ctl.device.busNumber = 0
        scsi_ctl.device.hotAddRemove = True
        scsi_ctl.device.sharedBus = 'noSharing'
        scsi_ctl.device.scsiCtlrUnitNumber = 7

        return scsi_ctl

    @staticmethod
    def is_scsi_controller(device):
        return isinstance(device, vim.vm.device.VirtualLsiLogicController) or \
            isinstance(device, vim.vm.device.ParaVirtualSCSIController) or \
            isinstance(device, vim.vm.device.VirtualBusLogicController) or \
            isinstance(device, vim.vm.device.VirtualLsiLogicSASController)

    def create_scsi_disk(self, scsi_ctl, disk_index=None):
        diskspec = vim.vm.device.VirtualDeviceSpec()
        diskspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        diskspec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create
        diskspec.device = vim.vm.device.VirtualDisk()
        diskspec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        diskspec.device.backing.diskMode = 'persistent'
        diskspec.device.controllerKey = scsi_ctl.device.key

        assert self.next_disk_unit_number != 7
        assert disk_index != 7
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

    def create_nic(self, device_type, device_label, device_infos):
        nic = vim.vm.device.VirtualDeviceSpec()
        if device_type == 'pcnet32':
            nic.device = vim.vm.device.VirtualPCNet32()
        elif device_type == 'vmxnet2':
            nic.device = vim.vm.device.VirtualVmxnet2()
        elif device_type == 'vmxnet3':
            nic.device = vim.vm.device.VirtualVmxnet3()
        elif device_type == 'e1000':
            nic.device = vim.vm.device.VirtualE1000()
        elif device_type == 'e1000e':
            nic.device = vim.vm.device.VirtualE1000e()
        elif device_type == 'sriov':
            nic.device = vim.vm.device.VirtualSriovEthernetCard()
        else:
            self.module.fail_json(msg="Invalid device_type '%s' for network %s" %
                                      (device_type, device_infos['name']))

        nic.device.wakeOnLanEnabled = True
        nic.device.addressType = 'assigned'
        nic.device.deviceInfo = vim.Description()
        nic.device.deviceInfo.label = device_label
        nic.device.deviceInfo.summary = device_infos['name']
        nic.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic.device.connectable.startConnected = True
        nic.device.connectable.allowGuestControl = True
        nic.device.connectable.connected = True
        if 'mac' in device_infos:
            nic.device.macAddress = device_infos['mac']

        return nic


class PyVmomiCache(object):
    """ This class caches references to objects which are requested multiples times but not modified """
    def __init__(self, content):
        self.content = content
        self.networks = {}
        self.clusters = {}
        self.esx_hosts = {}

    def get_network(self, network):
        if network not in self.networks:
            self.networks[network] = get_obj(self.content, [vim.Network], network)

        return self.networks[network]

    def get_cluster(self, cluster):
        if cluster not in self.clusters:
            self.clusters[cluster] = get_obj(self.content, [vim.ClusterComputeResource], cluster)

        return self.clusters[cluster]

    def get_esx_host(self, host):
        if host not in self.esx_hosts:
            self.esx_hosts[host] = get_obj(self.content, [vim.HostSystem], host)

        return self.esx_hosts[host]


class PyVmomiHelper(object):
    def __init__(self, module):
        if not HAS_PYVMOMI:
            module.fail_json(msg='pyvmomi module required')

        self.module = module
        self.device_helper = PyVmomiDeviceHelper(self.module)
        self.params = module.params
        self.si = None
        self.content = connect_to_api(self.module)
        self.configspec = None
        self.change_detected = False
        self.customspec = None
        self.current_vm_obj = None
        self.cache = PyVmomiCache(self.content)

    def should_deploy_from_template(self):
        return self.params.get('template') is not None

    def getvm(self, name=None, uuid=None, folder=None):

        # https://www.vmware.com/support/developer/vc-sdk/visdk2xpubs/ReferenceGuide/vim.SearchIndex.html
        # self.si.content.searchIndex.FindByInventoryPath('DC1/vm/test_folder')

        vm = None
        searchpath = None

        if uuid:
            vm = self.content.searchIndex.FindByUuid(uuid=uuid, vmSearch=True)
        elif folder:
            # Build the absolute folder path to pass into the search method
            if not self.params['folder'].startswith('/'):
                self.module.fail_json(msg="Folder %(folder)s needs to be an absolute path, starting with '/'." % self.params)
            searchpath = '%(datacenter)s%(folder)s' % self.params

            # get all objects for this path ...
            f_obj = self.content.searchIndex.FindByInventoryPath(searchpath)
            if f_obj:
                if isinstance(f_obj, vim.Datacenter):
                    f_obj = f_obj.vmFolder
                for c_obj in f_obj.childEntity:
                    if not isinstance(c_obj, vim.VirtualMachine):
                        continue
                    if c_obj.name == name:
                        vm = c_obj
                        if self.params['name_match'] == 'first':
                            break

        if vm:
            self.current_vm_obj = vm

        return vm

    def set_powerstate(self, vm, state, force):
        """
        Set the power status for a VM determined by the current and
        requested states. force is forceful
        """
        facts = self.gather_facts(vm)
        expected_state = state.replace('_', '').lower()
        current_state = facts['hw_power_status'].lower()
        result = dict(
            changed=False,
            failed=False,
        )

        # Need Force
        if not force and current_state not in ['poweredon', 'poweredoff']:
            result['failed'] = True
            result['msg'] = "VM is in %s power state. Force is required!" % current_state
            return result

        # State is not already true
        if current_state != expected_state:
            task = None
            try:
                if expected_state == 'poweredoff':
                    task = vm.PowerOff()

                elif expected_state == 'poweredon':
                    task = vm.PowerOn()

                elif expected_state == 'restarted':
                    if current_state in ('poweredon', 'poweringon', 'resetting', 'poweredoff'):
                        task = vm.Reset()
                    else:
                        result['failed'] = True
                        result['msg'] = "Cannot restart VM in the current state %s" % current_state

                elif expected_state == 'suspended':
                    if current_state in ('poweredon', 'poweringon'):
                        task = vm.Suspend()
                    else:
                        result['failed'] = True
                        result['msg'] = 'Cannot suspend VM in the current state %s' % current_state

                elif expected_state in ['shutdownguest', 'rebootguest']:
                    if current_state == 'poweredon' and vm.guest.toolsRunningStatus == 'guestToolsRunning':
                        if expected_state == 'shutdownguest':
                            task = vm.ShutdownGuest()
                        else:
                            task = vm.RebootGuest()
                    else:
                        result['failed'] = True
                        result['msg'] = "VM %s must be in 'poweredon' state & tools should be installed for guest shutdown/reboot" % vm.name

            except Exception as e:
                result['failed'] = True
                result['msg'] = to_native(e)

            if task:
                self.wait_for_task(task)
                if task.info.state == 'error':
                    result['failed'] = True
                    result['msg'] = to_native(task.info.error.msg)
                else:
                    result['changed'] = True

        # need to get new metadata if changed
        if result['changed']:
            newvm = self.getvm(uuid=vm.config.uuid)
            facts = self.gather_facts(newvm)
            result['instance'] = facts
        return result

    def gather_facts(self, vm):
        return gather_vm_facts(self.content, vm)

    def remove_vm(self, vm):
        # https://www.vmware.com/support/developer/converter-sdk/conv60_apireference/vim.ManagedEntity.html#destroy
        task = vm.Destroy()
        self.wait_for_task(task)

        if task.info.state == 'error':
            return {'changed': False, 'failed': True, 'msg': task.info.error.msg}
        else:
            return {'changed': True, 'failed': False}

    def configure_guestid(self, vm_obj, vm_creation=False):
        # guest_id is not required when using templates
        if self.should_deploy_from_template() and self.params.get('guest_id') is None:
            return

        # guest_id is only mandatory on VM creation
        if vm_creation and self.params['guest_id'] is None:
            self.module.fail_json(msg="guest_id attribute is mandatory for VM creation")

        if vm_obj is None or self.params['guest_id'] != vm_obj.summary.config.guestId:
            self.change_detected = True
            self.configspec.guestId = self.params['guest_id']

    def configure_cpu_and_memory(self, vm_obj, vm_creation=False):
        # set cpu/memory/etc
        if 'hardware' in self.params:
            if 'num_cpus' in self.params['hardware']:
                self.configspec.numCPUs = int(self.params['hardware']['num_cpus'])
                if vm_obj is None or self.configspec.numCPUs != vm_obj.config.hardware.numCPU:
                    self.change_detected = True
            # num_cpu is mandatory for VM creation
            elif vm_creation and not self.should_deploy_from_template():
                self.module.fail_json(msg="hardware.num_cpus attribute is mandatory for VM creation")

            if 'memory_mb' in self.params['hardware']:
                self.configspec.memoryMB = int(self.params['hardware']['memory_mb'])
                if vm_obj is None or self.configspec.memoryMB != vm_obj.config.hardware.memoryMB:
                    self.change_detected = True
            # memory_mb is mandatory for VM creation
            elif vm_creation and not self.should_deploy_from_template():
                self.module.fail_json(msg="hardware.memory_mb attribute is mandatory for VM creation")


    def get_vm_network_interfaces(self, vm=None):
        if vm is None:
            return []

        device_list = []
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualPCNet32) or \
               isinstance(device, vim.vm.device.VirtualVmxnet2) or \
               isinstance(device, vim.vm.device.VirtualVmxnet3) or \
               isinstance(device, vim.vm.device.VirtualE1000) or \
               isinstance(device, vim.vm.device.VirtualE1000e) or \
               isinstance(device, vim.vm.device.VirtualSriovEthernetCard):
                device_list.append(device)

        return device_list

    def configure_network(self, vm_obj):
        # Ignore empty networks, this permits to keep networks when deploying a template/cloning a VM
        if len(self.params['networks']) == 0:
            return

        network_devices = list()
        for network in self.params['networks']:
            if 'ip' in network or 'netmask' in network:
                if 'ip' not in network or not 'netmask' in network:
                    self.module.fail_json(msg="Both 'ip' and 'netmask' are required together.")

            if 'name' in network:
                if get_obj(self.content, [vim.Network], network['name']) is None:
                    self.module.fail_json(msg="Network '%(name)s' does not exists" % network)

            elif 'vlan' in network:
                dvps = get_all_objs(self.content, [vim.dvs.DistributedVirtualPortgroup])
                for dvp in dvps:
                    if hasattr(dvp.config.defaultPortConfig, 'vlan') and dvp.config.defaultPortConfig.vlan.vlanId == network['vlan']:
                        network['name'] = dvp.config.name
                        break
                    if dvp.config.name == network['vlan']:
                        network['name'] = dvp.config.name
                        break
                else:
                    self.module.fail_json(msg="VLAN '%(vlan)s' does not exist" % network)
            else:
                self.module.fail_json(msg="You need to define a network name or a vlan")

            network_devices.append(network)

        # List current device for Clone or Idempotency
        current_net_devices = self.get_vm_network_interfaces(vm=vm_obj)
        if len(network_devices) < len(current_net_devices):
            self.module.fail_json(msg="given network device list is lesser than current VM device list (%d < %d). "
                                      "Removing interfaces is not allowed"
                                      % (len(network_devices), len(current_net_devices)))

        for key in range(0, len(network_devices)):
            # Default device type is vmxnet3, VMWare best practice
            device_type = network_devices[key].get('device_type', 'vmxnet3')
            nic = self.device_helper.create_nic(device_type,
                                                'Network Adapter %s' % (key + 1),
                                                network_devices[key])

            nic_change_detected = False
            if key < len(current_net_devices) and (vm_obj or self.should_deploy_from_template()):
                nic.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                # Changing mac address has no effect when editing interface
                if 'mac' in network_devices[key] and nic.device.macAddress != current_net_devices[key].macAddress:
                    self.module.fail_json(msg="Changing MAC address has not effect when interface is already present. "
                                              "The failing new MAC address is %s" % nic.device.macAddress)

                nic.device = current_net_devices[key]
                nic.device.deviceInfo = vim.Description()
            else:
                nic.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                nic_change_detected = True

            if hasattr(self.cache.get_network(network_devices[key]['name']), 'portKeys'):
                # VDS switch
                pg_obj = get_obj(self.content, [vim.dvs.DistributedVirtualPortgroup], network_devices[key]['name'])

                if nic.device.backing and ( nic.device.backing.port.portgroupKey != pg_obj.key or nic.device.backing.port.switchUuid != pg_obj.config.distributedVirtualSwitch.uuid ):
                    nic_change_detected = True

                dvs_port_connection = vim.dvs.PortConnection()
                dvs_port_connection.portgroupKey = pg_obj.key
                dvs_port_connection.switchUuid = pg_obj.config.distributedVirtualSwitch.uuid
                nic.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                nic.device.backing.port = dvs_port_connection
                nic_change_detected = True
            else:
                # vSwitch
                if not isinstance(nic.device.backing, vim.vm.device.VirtualEthernetCard.NetworkBackingInfo):
                    nic.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                    nic_change_detected = True

                net_obj = self.cache.get_network(network_devices[key]['name'])
                if nic.device.backing.network != net_obj:
                    nic.device.backing.network = net_obj
                    nic_change_detected = True

                if nic.device.backing.deviceName != network_devices[key]['name']:
                    nic.device.backing.deviceName = network_devices[key]['name']
                    nic_change_detected = True

            if nic_change_detected:
                self.configspec.deviceChange.append(nic)
                self.change_detected = True

    def customize_customvalues(self, vm_obj):
        if len(self.params['customvalues']) == 0:
            return

        facts = self.gather_facts(vm_obj)
        for kv in self.params['customvalues']:
            if 'key' not in kv or 'value' not in kv:
                self.module.exit_json(msg="customvalues items required both 'key' and 'value fields.")

            # If kv is not kv fetched from facts, change it
            if kv['key'] not in facts['customvalues'] or facts['customvalues'][kv['key']] != kv['value']:
                try:
                    vm_obj.setCustomValue(key=kv['key'], value=kv['value'])
                    self.change_detected = True
                except Exception as e:
                    self.module.fail_json(msg="Failed to set custom value for key='%s' and value='%s'. Error was: %s"
                                          % (kv['key'], kv['value'], to_native(e)))

    def customize_vm(self, vm_obj):
        # Network settings
        adaptermaps = []
        for network in self.params['networks']:
            if 'ip' in network and 'netmask' in network:
                guest_map = vim.vm.customization.AdapterMapping()
                guest_map.adapter = vim.vm.customization.IPSettings()
                guest_map.adapter.ip = vim.vm.customization.FixedIp()
                guest_map.adapter.ip.ipAddress = str(network['ip'])
                guest_map.adapter.subnetMask = str(network['netmask'])

                if 'gateway' in network:
                    guest_map.adapter.gateway = network['gateway']

                # On Windows, DNS domain and DNS servers can be set by network interface
                # https://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.vm.customization.IPSettings.html
                if 'domain' in network:
                    guest_map.adapter.dnsDomain = network['domain']
                elif self.params['customization'].get('domain'):
                    guest_map.adapter.dnsDomain = self.params['customization']['domain']
                if 'dns_servers' in network:
                    guest_map.adapter.dnsServerList = network['dns_servers']
                elif self.params['customization'].get('dns_servers'):
                    guest_map.adapter.dnsServerList = self.params['customization']['dns_servers']

                adaptermaps.append(guest_map)

        # Global DNS settings
        globalip = vim.vm.customization.GlobalIPSettings()
        if 'dns_servers' in self.params['customization']:
            globalip.dnsServerList = self.params['customization'].get('dns_servers')
        # TODO: Maybe list the different domains from the interfaces here by default ?
        if 'dns_suffix' in self.params['customization'] or 'domain' in self.params['customization']:
            globalip.dnsSuffixList = self.params['customization'].get('dns_suffix', self.params['customization']['domain'])

        if self.params['guest_id']:
            guest_id = self.params['guest_id']
        else:
            guest_id = vm_obj.summary.config.guestId

        # If I install a Windows use Sysprep
        # https://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.vm.customization.Sysprep.html#field_detail
        if 'win' in guest_id:
            ident = vim.vm.customization.Sysprep()

            ident.userData = vim.vm.customization.UserData()
            ident.userData.computerName = vim.vm.customization.FixedName()
            ident.userData.computerName.name = str(self.params['customization'].get('hostname', self.params['name']))
            ident.userData.fullName = str(self.params['customization'].get('fullname', 'Administrator'))
            ident.userData.orgName = str(self.params['customization'].get('orgname', 'ACME'))

            ident.guiUnattended = vim.vm.customization.GuiUnattended()
            ident.guiUnattended.autoLogon = self.params['customization'].get('autologon', False)
            ident.guiUnattended.autoLogonCount = self.params['customization'].get('autologoncount', 1)
            ident.guiUnattended.timeZone = self.params['customization'].get('timezone', 85)

            ident.identification = vim.vm.customization.Identification()

            if self.params['customization'].get('password', '') != '':
                ident.guiUnattended.password = vim.vm.customization.Password()
                ident.guiUnattended.password.value = str(self.params['customization']['password'])
                ident.guiUnattended.password.plainText = True
            else:
                self.module.fail_json(msg="The 'customization' section requires a 'password' entry, which cannot be empty.")

            if 'productid' in self.params['customization']:
                ident.userData.orgName = str(self.params['customization']['productid'])

            if 'joindomain' in self.params['customization']:
                if 'domainadmin' not in self.params['customization'] or 'domainadminpassword' not in self.params['customization']:
                    self.module.fail_json(msg="'domainadmin' and 'domainadminpassword' entries are mandatory in 'customization' section to use joindomain feature")

                ident.identification.domainAdmin = str(self.params['customization'].get('domainadmin'))
                ident.identification.joinDomain = str(self.params['customization'].get('joindomain'))
                ident.identification.domainAdminPassword = vim.vm.customization.Password()
                ident.identification.domainAdminPassword.value = str(self.params['customization'].get('domainadminpassword'))
                ident.identification.domainAdminPassword.plainText = True

            elif 'joinworkgroup' in self.params['customization']:
                ident.identification.joinWorkgroup = str(self.params['customization'].get('joinworkgroup'))

            if 'runonce' in self.params['customization']:
                ident.guiRunOnce = vim.vm.customization.GuiRunOnce()
                ident.guiRunOnce.commandList = self.params['customization']['runonce']
        else:
            # Else use LinuxPrep
            # https://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.vm.customization.LinuxPrep.html
            ident = vim.vm.customization.LinuxPrep()
            # TODO: Maybe add domain from interface if missing ?
            if 'domain' in self.params['customization']:
                ident.domain = str(self.params['customization'].get('domain'))
            ident.hostName = vim.vm.customization.FixedName()
            ident.hostName.name = str(self.params['customization'].get('hostname', self.params['name']))

        self.customspec = vim.vm.customization.Specification()
        self.customspec.nicSettingMap = adaptermaps
        self.customspec.globalIPSettings = globalip
        self.customspec.identity = ident

    def get_vm_scsi_controller(self, vm_obj):
        # If vm_obj doesn't exists no SCSI controller to find
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
            # size_tb, size_gb, size_mb, size_kb, size_b ...?
            if 'size' in expected_disk_spec:
                expected = ''.join(c for c in expected_disk_spec['size'] if c.isdigit())
                unit = expected_disk_spec['size'].replace(expected, '').lower()
                expected = int(expected)
            else:
                param = [x for x in expected_disk_spec.keys() if x.startswith('size_')][0]
                unit = param.split('_')[-1].lower()
                expected = [x[1] for x in expected_disk_spec.items() if x[0].startswith('size_')][0]
                expected = int(expected)

            if unit == 'tb':
                return expected * 1024 * 1024 * 1024
            elif unit == 'gb':
                return expected * 1024 * 1024
            elif unit == ' mb':
                return expected * 1024
            elif unit == 'kb':
                return expected

            self.module.fail_json(
                msg='%s is not a supported unit for disk size. Supported units are kb, mb, gb or tb' % unit)

        # No size found but disk, fail
        self.module.fail_json(
            msg="No size, size_kb, size_mb, size_gb or size_tb attribute found into disk configuration")

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

            # is it thin?
            if 'type' in expected_disk_spec:
                if expected_disk_spec.get('type', '').lower() == 'thin':
                    diskspec.device.backing.thinProvisioned = True

            # which datastore?
            if expected_disk_spec.get('datastore'):
                # TODO: This is already handled by the relocation spec,
                # but it needs to eventually be handled for all the
                # other disks defined
                pass

            # increment index for next disk search
            disk_index += 1
            # index 7 is reserved to SCSI controller
            if disk_index == 7:
                disk_index += 1

            kb = self.get_configured_disk_size(expected_disk_spec)
            # VMWare doesn't allow to reduce disk sizes
            if kb < diskspec.device.capacityInKB:
                self.module.fail_json(
                    msg="Given disk size is lesser than found (%d < %d). Reducing disks is not allowed." %
                        (kb, diskspec.device.capacityInKB))

            if kb != diskspec.device.capacityInKB or disk_modified:
                diskspec.device.capacityInKB = kb
                self.configspec.deviceChange.append(diskspec)

                self.change_detected = True

    def select_host(self):
        # if the user wants a cluster, get the list of hosts for the cluster and use the first one
        if self.params['cluster']:
            cluster = self.cache.get_cluster(self.params['cluster'])
            if not cluster:
                self.module.fail_json(msg="Failed to find a cluster named %(cluster)s" % self.params)
            hostsystems = [x for x in cluster.host]
            # TODO: add a policy to select host
            hostsystem = hostsystems[0]
        else:
            hostsystem = self.cache.get_esx_host(self.params['esxi_hostname'])
            if not hostsystem:
                self.module.fail_json(msg="Failed to find a host named %(esxi_hostname)s" % self.params)

        return hostsystem

    def select_datastore(self, vm_obj=None):
        datastore = None
        datastore_name = None
        if len(self.params['disk']) != 0:
            # TODO: really use the datastore for newly created disks
            if 'autoselect_datastore' in self.params['disk'][0] and self.params['disk'][0]['autoselect_datastore']:
                datastores = get_all_objs(self.content, [vim.Datastore])
                if datastores is None or len(datastores) == 0:
                    self.module.fail_json(msg="Unable to find a datastore list when autoselecting")

                datastore_freespace = 0
                for ds in datastores:
                    if ds.summary.freeSpace > datastore_freespace:
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
                datastore = get_obj(self.content, [vim.Datastore], datastore_name)
            else:
                self.module.fail_json(msg="Either datastore or autoselect_datastore "
                                          "should be provided to select datastore")
        if not datastore and self.should_deploy_from_template():
            # use the template's existing DS
            disks = [x for x in vm_obj.config.hardware.device if isinstance(x, vim.vm.device.VirtualDisk)]
            datastore = disks[0].backing.datastore
            datastore_name = datastore.name
        if not datastore:
            self.module.fail_json(msg="Failed to find a matching datastore")

        return datastore, datastore_name

    def obj_has_parent(self, obj, parent):
        assert obj is not None and parent is not None
        current_parent = obj

        while True:
            if current_parent.name == parent.name:
                return True

            current_parent = current_parent.parent
            if current_parent is None:
                return False

    def select_resource_pool(self, host):
        resource_pools = get_all_objs(self.content, [vim.ResourcePool])
        for rp in resource_pools.items():
            if not rp[0]:
                continue

            if not hasattr(rp[0], 'parent'):
                continue

            # Find resource pool on host
            if self.obj_has_parent(rp[0].parent, host.parent):
                # If no resource_pool selected or it's the selected pool, return it
                if self.module.params['resource_pool'] is None or rp[0].name == self.module.params['resource_pool']:
                    return rp[0]

        if self.module.params['resource_pool'] is not None:
            self.module.fail_json(msg="Could not find resource_pool %s for selected host %s"
                                  % (self.module.params['resource_pool'], host.name))
        else:
            self.module.fail_json(msg="Failed to find a resource group for %s" % host.name)

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

    def deploy_vm(self):
        # https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/clone_vm.py
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.vm.CloneSpec.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.vm.ConfigSpec.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk41pubs/ApiReference/vim.vm.RelocateSpec.html

        # FIXME:
        #   - multiple datacenters
        #   - multiple templates by the same name
        #   - static IPs

        #datacenters = get_all_objs(self.content, [vim.Datacenter])
        datacenter = get_obj(self.content, [vim.Datacenter], self.params['datacenter'])
        if not datacenter:
            self.module.fail_json(msg='No datacenter named %(datacenter)s was found' % self.params)

        destfolder = None
        if not self.params['folder'].startswith('/'):
            self.module.fail_json(msg="Folder %(folder)s needs to be an absolute path, starting with '/'." % self.params)

        f_obj = self.content.searchIndex.FindByInventoryPath('/%(datacenter)s%(folder)s' % self.params)
        if f_obj is None:
            self.module.fail_json(msg='No folder matched the path: %(folder)s' % self.params)
        destfolder = f_obj

        hostsystem = self.select_host()

        if self.should_deploy_from_template():
            # FIXME: need to search for this in the same way as guests to ensure accuracy
            vm_obj = get_obj(self.content, [vim.VirtualMachine], self.params['template'])
            if not vm_obj:
                self.module.fail_json(msg="Could not find a template named %(template)s" % self.params)
        else:
            vm_obj = None

        # set the destination datastore for VM & disks
        (datastore, datastore_name) = self.select_datastore(vm_obj)
        resource_pool = self.select_resource_pool(hostsystem)

        self.configspec = vim.vm.ConfigSpec(cpuHotAddEnabled=True, memoryHotAddEnabled=True)
        self.configspec.deviceChange = []
        self.configure_guestid(vm_obj=vm_obj, vm_creation=True)
        self.configure_cpu_and_memory(vm_obj=vm_obj, vm_creation=True)
        self.configure_disks(vm_obj=vm_obj)
        self.configure_network(vm_obj=vm_obj)

        if len(self.params['customization']) > 0 or len(self.params['networks']) > 0:
            self.customize_vm(vm_obj=vm_obj)

        try:
            if self.should_deploy_from_template():
                # create the relocation spec
                relospec = vim.vm.RelocateSpec()
                relospec.host = hostsystem
                relospec.datastore = datastore
                relospec.pool = resource_pool

                clonespec = vim.vm.CloneSpec(template=self.params['is_template'], location=relospec)
                if self.customspec:
                    clonespec.customization = self.customspec

                clonespec.config = self.configspec
                task = vm_obj.Clone(folder=destfolder, name=self.params['name'], spec=clonespec)
                self.change_detected = True
            else:
                # ConfigSpec require name for VM creation
                self.configspec.name = self.params['name']
                self.configspec.files = vim.vm.FileInfo(logDirectory=None,
                                                        snapshotDirectory=None,
                                                        suspendDirectory=None,
                                                        vmPathName="[" + datastore_name + "] " + self.params["name"])

                task = destfolder.CreateVM_Task(config=self.configspec, pool=resource_pool)
                self.change_detected = True
            self.wait_for_task(task)
        except TypeError:
            self.module.fail_json(msg="TypeError was returned, please ensure to give correct inputs.")

        if task.info.state == 'error':
            # https://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=2021361
            # https://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=2173
            return {'changed': self.change_detected, 'failed': True, 'msg': task.info.error.msg}
        else:
            # set annotation
            vm = task.info.result
            if self.params['annotation']:
                annotation_spec = vim.vm.ConfigSpec()
                annotation_spec.annotation = str(self.params['annotation'])
                task = vm.ReconfigVM_Task(annotation_spec)
                self.wait_for_task(task)

            self.customize_customvalues(vm_obj=vm)

            if self.params['wait_for_ip_address'] or self.params['state'] in ['poweredon', 'restarted']:
                self.set_powerstate(vm, 'poweredon', force=False)

                if self.params['wait_for_ip_address']:
                    self.wait_for_vm_ip(vm)

            vm_facts = self.gather_facts(vm)
            return {'changed': self.change_detected, 'failed': False, 'instance': vm_facts}

    def reconfigure_vm(self):
        self.configspec = vim.vm.ConfigSpec()
        self.configspec.deviceChange = []

        self.configure_guestid(vm_obj=self.current_vm_obj)
        self.configure_cpu_and_memory(vm_obj=self.current_vm_obj)
        self.configure_disks(vm_obj=self.current_vm_obj)
        self.configure_network(vm_obj=self.current_vm_obj)
        self.customize_customvalues(vm_obj=self.current_vm_obj)

        if self.params['annotation'] and self.current_vm_obj.config.annotation != self.params['annotation']:
            self.configspec.annotation = str(self.params['annotation'])
            self.change_detected = True

        relospec = vim.vm.RelocateSpec()
        hostsystem = self.select_host()
        relospec.pool = self.select_resource_pool(hostsystem)

        change_applied = False
        if relospec.pool != self.current_vm_obj.resourcePool:
            task = self.current_vm_obj.RelocateVM_Task(spec=relospec)
            self.wait_for_task(task)
            change_applied = True

        # Only send VMWare task if we see a modification
        if self.change_detected:
            task = self.current_vm_obj.ReconfigVM_Task(spec=self.configspec)
            self.wait_for_task(task)
            change_applied = True

            if task.info.state == 'error':
                # https://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=2021361
                # https://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=2173
                return {'changed': change_applied, 'failed': True, 'msg': task.info.error.msg}

        # Rename VM
        if self.params['uuid'] and self.params['name'] and self.params['name'] != self.current_vm_obj.config.name:
            task = self.current_vm_obj.Rename_Task(self.params['name'])
            self.wait_for_task(task)
            change_applied = True

            if task.info.state == 'error':
                return {'changed': change_applied, 'failed': True, 'msg': task.info.error.msg}

        # Mark VM as Template
        if self.params['is_template']:
            self.current_vm_obj.MarkAsTemplate()
            change_applied = True

        vm_facts = self.gather_facts(self.current_vm_obj)
        return {'changed': change_applied, 'failed': False, 'instance': vm_facts}

    @staticmethod
    def wait_for_task(task):
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.Task.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.TaskInfo.html
        # https://github.com/virtdevninja/pyvmomi-community-samples/blob/master/samples/tools/tasks.py
        while task.info.state not in ['success', 'error']:
            time.sleep(1)

    def wait_for_vm_ip(self, vm, poll=100, sleep=5):
        ips = None
        facts = {}
        thispoll = 0
        while not ips and thispoll <= poll:
            newvm = self.getvm(uuid=vm.config.uuid)
            facts = self.gather_facts(newvm)
            if facts['ipv4'] or facts['ipv6']:
                ips = True
            else:
                time.sleep(sleep)
                thispoll += 1

        return facts


def get_obj(content, vimtype, name):
    """
    Return an object by name, if name is None the
    first found object is returned
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    container.Destroy()
    return obj


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(
                type='str',
                default=os.environ.get('VMWARE_HOST')
            ),
            username=dict(
                type='str',
                default=os.environ.get('VMWARE_USER')
            ),
            password=dict(
                type='str', no_log=True,
                default=os.environ.get('VMWARE_PASSWORD')
            ),
            state=dict(
                required=False,
                choices=[
                    'poweredon',
                    'poweredoff',
                    'present',
                    'absent',
                    'restarted',
                    'suspended',
                    'shutdownguest',
                    'rebootguest'
                ],
                default='present'),
            validate_certs=dict(type='bool', default=True),
            template_src=dict(type='str', aliases=['template'], default=None),
            is_template=dict(type='bool', default=False),
            annotation=dict(type='str', aliases=['notes']),
            customvalues=dict(type='list', default=[]),
            name=dict(required=True, type='str'),
            name_match=dict(type='str', default='first'),
            uuid=dict(type='str'),
            folder=dict(type='str', default='/vm'),
            guest_id=dict(type='str', default=None),
            disk=dict(type='list', default=[]),
            hardware=dict(type='dict', default={}),
            force=dict(type='bool', default=False),
            datacenter=dict(type='str', default='ha-datacenter'),
            esxi_hostname=dict(type='str', default=None),
            cluster=dict(type='str', default=None),
            wait_for_ip_address=dict(type='bool', default=False),
            networks=dict(type='list', default=[]),
            resource_pool=dict(type='str', default=None),
            customization=dict(type='dict', no_log=True, default={}),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ['esxi_hostname', 'cluster'],
        ],
        required_together=[
            ['state', 'force'],
            ['template'],
        ],
    )

    result = {'failed': False, 'changed': False}

    # Prepend /vm if it was missing from the folder path, also strip trailing slashes
    if not module.params['folder'].startswith('/vm') and module.params['folder'].startswith('/'):
        module.params['folder'] = '/vm%(folder)s' % module.params
    module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.getvm(name=module.params['name'],
                   folder=module.params['folder'],
                   uuid=module.params['uuid'])

    # VM already exists
    if vm:
        if module.params['state'] == 'absent':
            # destroy it
            if module.params['force']:
                # has to be poweredoff first
                pyv.set_powerstate(vm, 'poweredoff', module.params['force'])
            result = pyv.remove_vm(vm)
        elif module.params['state'] == 'present':
            result = pyv.reconfigure_vm()
        elif module.params['state'] in ['poweredon', 'poweredoff', 'restarted', 'suspended', 'shutdownguest', 'rebootguest']:
            # set powerstate
            tmp_result = pyv.set_powerstate(vm, module.params['state'], module.params['force'])
            if tmp_result['changed']:
                result["changed"] = True
            if not tmp_result["failed"]:
                result["failed"] = False
        else:
            # This should not happen
            assert False
    # VM doesn't exist
    else:
        if module.params['state'] in ['poweredon', 'poweredoff', 'present', 'restarted', 'suspended']:
            # Create it ...
            result = pyv.deploy_vm()

    if 'failed' not in result:
        result['failed'] = False

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)

if __name__ == '__main__':
    main()
