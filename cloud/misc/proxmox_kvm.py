#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Abdoul Bah (@helldorado) <abdoul.bah at alterway.fr>

"""
Ansible module to manage Qemu(KVM) instance in Proxmox VE cluster.
This module is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this software.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: proxmox_kvm
short_description: Management of Qemu(KVM) Virtual Machines in Proxmox VE cluster.
description:
  - Allows you to create/delete/stop Qemu(KVM) Virtual Machines in Proxmox VE cluster.
version_added: "2.3"
author: "Abdoul Bah (@helldorado) <abdoul.bah at alterway.fr>"
options:
  acpi:
    description:
      - Specify if ACPI should be enables/disabled.
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
    type: boolean
  agent:
    description:
      - Specify if the QEMU GuestAgent should be enabled/disabled.
    required: false
    default: null
    choices: [ "yes", "no" ]
    type: boolean
  args:
    description:
      - Pass arbitrary arguments to kvm.
      - This option is for experts only!
    default: "-serial unix:/var/run/qemu-server/VMID.serial,server,nowait"
    required: false
    type: string
  api_host:
    description:
      - Specify the target host of the Proxmox VE cluster.
    required: true
  api_user:
    description:
      - Specify the user to authenticate with.
    required: true
  api_password:
    description:
      - Specify the password to authenticate with.
      - You can use C(PROXMOX_PASSWORD) environment variable.
    default: null
    required: false
  autostart:
    description:
      - Specify, if the VM should be automatically restarted after crash (currently ignored in PVE API).
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    type: boolean
  balloon:
    description:
      - Specify the amount of RAM for the VM in MB.
      - Using zero disables the balloon driver.
    required: false
    default: 0
    type: integer
  bios:
    description:
      - Specify the BIOS implementation.
    choices: ['seabios', 'ovmf']
    required: false
    default: null
    type: string
  boot:
    description:
      - Specify the boot order -> boot on floppy C(a), hard disk C(c), CD-ROM C(d), or network C(n).
      - You can combine to set order.
    required: false
    default: cnd
    type: string
  bootdisk:
    description:
      - Enable booting from specified disk. C((ide|sata|scsi|virtio)\d+)
    required: false
    default: null
    type: string
  cores:
    description:
      - Specify number of cores per socket.
    required: false
    default: 1
    type: integer
  cpu:
    description:
      - Specify emulated CPU type.
    required: false
    default: kvm64
    type: string
  cpulimit:
    description:
      - Specify if CPU usage will be limited. Value 0 indicates no CPU limit.
      - If the computer has 2 CPUs, it has total of '2' CPU time
    required: false
    default: null
    type: integer
  cpuunits:
    description:
      - Specify CPU weight for a VM.
      - You can disable fair-scheduler configuration by setting this to 0
    default: 1000
    required: false
    type: integer
  delete:
    description:
      - Specify a list of settings you want to delete.
    required: false
    default: null
    type: string
  description:
    description:
      - Specify the description for the VM. Only used on the configuration web interface.
      - This is saved as comment inside the configuration file.
    required: false
    default: null
    type: string
  digest:
    description:
      - Specify if to prevent changes if current configuration file has different SHA1 digest.
      - This can be used to prevent concurrent modifications.
    required: false
    default: null
    type: string
  force:
    description:
      - Allow to force stop VM.
      - Can be used only with states C(stopped), C(restarted).
    default: null
    choices: [ "yes", "no" ]
    required: false
    type: boolean
  freeze:
    description:
      - Specify if PVE should freeze CPU at startup (use 'c' monitor command to start execution).
    required: false
    default: null
    choices: [ "yes", "no" ]
    type: boolean
  hostpci:
    description:
      - Specify a hash/dictionary of map host pci devices into guest. C(hostpci='{"key":"value", "key":"value"}').
      - Keys allowed are - C(hostpci[n]) where 0 ≤ n ≤ N.
      - Values allowed are -  C("host="HOSTPCIID[;HOSTPCIID2...]",pcie="1|0",rombar="1|0",x-vga="1|0"").
      - The C(host) parameter is Host PCI device pass through. HOSTPCIID syntax is C(bus:dev.func) (hexadecimal numbers).
      - C(pcie=boolean) I(default=0) Choose the PCI-express bus (needs the q35 machine model).
      - C(rombar=boolean) I(default=1) Specify whether or not the device’s ROM will be visible in the guest’s memory map.
      - C(x-vga=boolean) I(default=0) Enable vfio-vga device support.
      - /!\ This option allows direct access to host hardware. So it is no longer possible to migrate such machines - use with special care.
    required: false
    default: null
    type: A hash/dictionary defining host pci devices
  hotplug:
    description:
      - Selectively enable hotplug features.
      - This is a comma separated list of hotplug features C('network', 'disk', 'cpu', 'memory' and 'usb').
      - Value 0 disables hotplug completely and value 1 is an alias for the default C('network,disk,usb').
    required: false
    default: null
    type: string
  hugepages:
    description:
      - Enable/disable hugepages memory.
    choices: ['any', '2', '1024']
    required: false
    default: null
    type: string
  ide:
    description:
      - A hash/dictionary of volume used as IDE hard disk or CD-ROM. C(ide='{"key":"value", "key":"value"}').
      - Keys allowed are - C(ide[n]) where 0 ≤ n ≤ 3.
      - Values allowed are - C("storage:size,format=value").
      - C(storage) is the storage identifier where to create the disk.
      - C(size) is the size of the disk in GB.
      - C(format) is the drive’s backing file’s data format. C(qcow2|raw|subvol).
    required: false
    default: null
    type: A hash/dictionary defining ide
  keyboard:
    description:
      - Sets the keyboard layout for VNC server.
    required: false
    default: null
    type: string
  kvm:
    description:
      - Enable/disable KVM hardware virtualization.
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
    type: boolean
  localtime:
    description:
      - Sets the real time clock to local time.
      - This is enabled by default if ostype indicates a Microsoft OS.
    required: false
    default: null
    choices: [ "yes", "no" ]
    type: boolean
  lock:
    description:
      - Lock/unlock the VM.
    choices: ['migrate', 'backup', 'snapshot', 'rollback']
    required: false
    default: null
    type: string
  machine:
    description:
      - Specifies the Qemu machine type.
      - type => C((pc|pc(-i440fx)?-\d+\.\d+(\.pxe)?|q35|pc-q35-\d+\.\d+(\.pxe)?))
    required: false
    default: null
    type: string
  memory:
    description:
      - Memory size in MB for instance.
    required: false
    default: 512
    type: integer
  migrate_downtime:
    description:
      - Sets maximum tolerated downtime (in seconds) for migrations.
    required: false
    default: null
    type: integer
  migrate_speed:
    description:
      - Sets maximum speed (in MB/s) for migrations.
      - A value of 0 is no limit.
    required: false
    default: null
    type: integer
  name:
    description:
      - Specifies the VM name. Only used on the configuration web interface.
      - Required only for C(state=present).
    default: null
    required: false
  net:
    description:
      - A hash/dictionary of network interfaces for the VM. C(net='{"key":"value", "key":"value"}').
      - Keys allowed are - C(net[n]) where 0 ≤ n ≤ N.
      - Values allowed are - C("model="XX:XX:XX:XX:XX:XX",brigde="value",rate="value",tag="value",firewall="1|0",trunks="vlanid"").
      - Model is one of C(e1000 e1000-82540em e1000-82544gc e1000-82545em i82551 i82557b i82559er ne2k_isa ne2k_pci pcnet rtl8139 virtio vmxnet3).
      - C(XX:XX:XX:XX:XX:XX) should be an unique MAC address. This is automatically generated if not specified.
      - The C(bridge) parameter can be used to automatically add the interface to a bridge device. The Proxmox VE standard bridge is called 'vmbr0'.
      - Option C(rate) is used to limit traffic bandwidth from and to this interface. It is specified as floating point number, unit is 'Megabytes per second'.
      - If you specify no bridge, we create a kvm 'user' (NATed) network device, which provides DHCP and DNS services.
    default: null
    required: false
    type: A hash/dictionary defining interfaces
  node:
    description:
      - Proxmox VE node, where the new VM will be created.
      - Only required for C(state=present).
      - For other states, it will be autodiscovered.
    default: null
    required: false
  numa:
    description:
      - A hash/dictionaries of NUMA topology. C(numa='{"key":"value", "key":"value"}').
      - Keys allowed are - C(numa[n]) where 0 ≤ n ≤ N.
      - Values allowed are - C("cpu="<id[-id];...>",hostnodes="<id[-id];...>",memory="number",policy="(bind|interleave|preferred)"").
      - C(cpus) CPUs accessing this NUMA node.
      - C(hostnodes) Host NUMA nodes to use.
      - C(memory) Amount of memory this NUMA node provides.
      - C(policy) NUMA allocation policy.
    default: null
    required: false
    type: A hash/dictionary defining NUMA topology
  onboot:
    description:
      - Specifies whether a VM will be started during system bootup.
    default: "yes"
    choices: [ "yes", "no" ]
    required: false
    type: boolean
  ostype:
    description:
      - Specifies guest operating system. This is used to enable special optimization/features for specific operating systems.
      - The l26 is Linux 2.6/3.X Kernel.
    choices: ['other', 'wxp', 'w2k', 'w2k3', 'w2k8', 'wvista', 'win7', 'win8', 'l24', 'l26', 'solaris']
    default: l26
    required: false
    type: string
  parallel:
    description:
      - A hash/dictionary of map host parallel devices. C(parallel='{"key":"value", "key":"value"}').
      - Keys allowed are - (parallel[n]) where 0 ≤ n ≤ 2.
      - Values allowed are - C("/dev/parport\d+|/dev/usb/lp\d+").
    default: null
    required: false
    type: A hash/dictionary defining host parallel devices
  protection:
    description:
      - Enable/disable the protection flag of the VM. This will enable/disable the remove VM and remove disk operations.
    default: null
    choices: [ "yes", "no" ]
    required: false
    type: boolean
  reboot:
    description:
      - Allow reboot. If set to yes, the VM exit on reboot.
    default: null
    choices: [ "yes", "no" ]
    required: false
    type: boolean
  revert:
    description:
      - Revert a pending change.
    default: null
    required: false
    type: string
  sata:
    description:
      - A hash/dictionary of volume used as sata hard disk or CD-ROM. C(sata='{"key":"value", "key":"value"}').
      - Keys allowed are - C(sata[n]) where 0 ≤ n ≤ 5.
      - Values allowed are -  C("storage:size,format=value").
      - C(storage) is the storage identifier where to create the disk.
      - C(size) is the size of the disk in GB.
      - C(format) is the drive’s backing file’s data format. C(qcow2|raw|subvol).
    default: null
    required: false
    type: A hash/dictionary defining sata
  scsi:
    description:
      - A hash/dictionary of volume used as SCSI hard disk or CD-ROM. C(scsi='{"key":"value", "key":"value"}').
      - Keys allowed are - C(sata[n]) where 0 ≤ n ≤ 13.
      - Values allowed are -  C("storage:size,format=value").
      - C(storage) is the storage identifier where to create the disk.
      - C(size) is the size of the disk in GB.
      - C(format) is the drive’s backing file’s data format. C(qcow2|raw|subvol).
    default: null
    required: false
    type: A hash/dictionary defining scsi
  scsihw:
    description:
      - Specifies the SCSI controller model.
    choices: ['lsi', 'lsi53c810', 'virtio-scsi-pci', 'virtio-scsi-single', 'megasas', 'pvscsi']
    required: false
    default: null
    type: string
  serial:
    description:
      - A hash/dictionary of serial device to create inside the VM. C('{"key":"value", "key":"value"}').
      - Keys allowed are - serial[n](str; required) where 0 ≤ n ≤ 3.
      - Values allowed are - C((/dev/.+|socket)).
      - /!\ If you pass through a host serial device, it is no longer possible to migrate such machines - use with special care.
    default: null
    required: false
    type: A hash/dictionary defining serial
  shares:
    description:
      - Rets amount of memory shares for auto-ballooning. (0 - 50000).
      - The larger the number is, the more memory this VM gets.
      - The number is relative to weights of all other running VMs.
      - Using 0 disables auto-ballooning, this means no limit.
    required: false
    default: null
    type: integer
  skiplock:
    description:
      - Ignore locks
      - Only root is allowed to use this option.
    required: false
    default: null
    choices: [ "yes", "no" ]
    type: boolean
  smbios:
    description:
      - Specifies SMBIOS type 1 fields.
    required: false
    default: null
    type: string
  sockets:
    description:
      - Sets the number of CPU sockets. (1 - N).
    required: false
    default: 1
    type: integer
  startdate:
    description:
      - Sets the initial date of the real time clock.
      - Valid format for date are C('now') or C('2016-09-25T16:01:21') or C('2016-09-25').
    required: false
    default: null
    type: string
  startup:
    description:
      - Startup and shutdown behavior. C([[order=]\d+] [,up=\d+] [,down=\d+]).
      - Order is a non-negative number defining the general startup order.
      - Shutdown in done with reverse ordering.
    required: false
    default: null
    type: string
  state:
    description:
      - Indicates desired state of the instance.
      - If C(current), the current state of the VM will be fecthed. You can acces it with C(results.status)
    choices: ['present', 'started', 'absent', 'stopped', 'restarted','current']
    required: false
    default: present
  tablet:
    description:
      - Enables/disables the USB tablet device.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
    type: boolean
  tdf:
    description:
      - Enables/disables time drift fix.
    required: false
    default: null
    choices: [ "yes", "no" ]
    type: boolean
  template:
    description:
      - Enables/disables the template.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    type: boolean
  timeout:
    description:
      - Timeout for operations.
    default: 30
    required: false
    type: integer
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
    default: "no"
    choices: [ "yes", "no" ]
    required: false
    type: boolean
  vcpus:
    description:
      - Sets number of hotplugged vcpus.
    required: false
    default: null
    type: integer
  vga:
    description:
      - Select VGA type. If you want to use high resolution modes (>= 1280x1024x16) then you should use option 'std' or 'vmware'.
    choices: ['std', 'cirrus', 'vmware', 'qxl', 'serial0', 'serial1', 'serial2', 'serial3', 'qxl2', 'qxl3', 'qxl4']
    required: false
    default: std
  virtio:
    description:
      - A hash/dictionary of volume used as VIRTIO hard disk. C(virtio='{"key":"value", "key":"value"}').
      - Keys allowed are - C(virto[n]) where 0 ≤ n ≤ 15.
      - Values allowed are -  C("storage:size,format=value").
      - C(storage) is the storage identifier where to create the disk.
      - C(size) is the size of the disk in GB.
      - C(format) is the drive’s backing file’s data format. C(qcow2|raw|subvol).
    required: false
    default: null
    type: A hash/dictionary defining virtio
  vmid:
    description:
      - Specifies the VM ID. Instead use I(name) parameter.
      - If vmid is not set, the next available VM ID will be fetched from ProxmoxAPI.
    default: null
    required: false
  watchdog:
    description:
      - Creates a virtual hardware watchdog device.
    required: false
    default: null
    type: string
Notes:
  - Requires proxmoxer and requests modules on host. This modules can be installed with pip.
requirements: [ "proxmoxer", "requests" ]
'''

EXAMPLES = '''
# Create new VM with minimal options
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf

# Create new VM with minimal options and given vmid
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    vmid        : 100

# Create new VM with two network interface options.
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    net         : '{"net0":"virtio,bridge=vmbr1,rate=200", "net1":"e1000,bridge=vmbr2,"}'

# Create new VM with one network interface, three virto hard disk, 4 cores, and 2 vcpus.
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    net         : '{"net0":"virtio,bridge=vmbr1,rate=200"}'
    virtio      : '{"virtio0":"VMs_LVM:10", "virtio1":"VMs:2,format=qcow2", "virtio2":"VMs:5,format=raw"}'
    cores       : 4
    vcpus       : 2

# Create new VM and lock it for snapashot.
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    lock        : snapshot

# Create new VM and set protection to disable the remove VM and remove disk operations
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    protection  : yes

# Start VM
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    state       : started

# Stop VM
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    state       : stopped

# Stop VM with force
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    state       : stopped
    force       : yes

# Restart VM
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    state       : restarted

# Remove VM
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    state       : absent

# Get VM current state 
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    state       : current
'''

RETURN = '''
devices:
    description: The list of devices created or used.
    returned: success
    type: dict
    sample: '
      {
        "ide0": "VMS_LVM:vm-115-disk-1",
        "ide1": "VMs:115/vm-115-disk-3.raw",
        "virtio0": "VMS_LVM:vm-115-disk-2",
        "virtio1": "VMs:115/vm-115-disk-1.qcow2",
        "virtio2": "VMs:115/vm-115-disk-2.raw"
      }'
mac:
    description: List of mac address created and net[n] attached. Useful when you want to use provision systems like Foreman via PXE.
    returned: success
    type: dict
    sample: '
      {
        "net0": "3E:6E:97:D2:31:9F",
        "net1": "B6:A1:FC:EF:78:A4"
      }'
vmid:
    description: The VM vmid.
    returned: success
    type: int
    sample: 115
status:
    description: 
      - The current virtual machine status.
      - Returned only when C(state=current)
    returned: success
    type: dict
    sample: '{
      "changed": false,
      "msg": "VM kropta with vmid = 110 is running",
      "status": "running" 
    }'
'''

import os
import time


try:
  from proxmoxer import ProxmoxAPI
  HAS_PROXMOXER = True
except ImportError:
  HAS_PROXMOXER = False

VZ_TYPE='qemu'

def get_nextvmid(proxmox):
  try:
    vmid = proxmox.cluster.nextid.get()
    return vmid
  except Exception as e:
    module.fail_json(msg="Unable to get next vmid. Failed with exception: %s")

def get_vmid(proxmox, name):
    return [ vm['vmid'] for vm in proxmox.cluster.resources.get(type='vm') if vm['name'] == name ]

def get_vm(proxmox, vmid):
  return [ vm for vm in proxmox.cluster.resources.get(type='vm') if vm['vmid'] == int(vmid) ]

def node_check(proxmox, node):
  return [ True for nd in proxmox.nodes.get() if nd['node'] == node ]

def get_vminfo(module, proxmox, node, vmid, **kwargs):
        global results
        results = {}
        mac = {}
        devices = {}
        try:
          vm = proxmox.nodes(node).qemu(vmid).config.get()
        except Exception as e:
          module.fail_json(msg='Getting information for VM with vmid = %s failed with exception: %s' % (vmid, e))

        # Sanitize kwargs. Remove not defined args and ensure True and False converted to int.
        kwargs = dict((k,v) for k, v in kwargs.iteritems() if v is not None)

        # Convert all dict in kwargs to elements. For hostpci[n], ide[n], net[n], numa[n], parallel[n], sata[n], scsi[n], serial[n], virtio[n]
        for k in kwargs.keys():
          if isinstance(kwargs[k], dict):
             kwargs.update(kwargs[k])
             del kwargs[k]

        # Split information by type
        for k, v in kwargs.iteritems():
          if re.match(r'net[0-9]', k) is not None:
            interface = k
            k = vm[k]
            k = re.search('=(.*?),', k).group(1)
            mac[interface] = k
          if re.match(r'virtio[0-9]', k) is not None or re.match(r'ide[0-9]', k) is not None or re.match(r'scsi[0-9]', k) is not None or re.match(r'sata[0-9]', k) is not None:
            device = k
            k = vm[k]
            k = re.search('(.*?),', k).group(1)
            devices[device] = k

        results['mac'] = mac
        results['devices'] = devices
        results['vmid'] = int(vmid)

def create_vm(module, proxmox, vmid, node, name, memory, cpu, cores, sockets, timeout, **kwargs):
  # Available only in PVE 4
  only_v4 = ['force','protection','skiplock']
  # Default args for vm. Note: -args option is for experts only. It allows you to pass arbitrary arguments to kvm.
  vm_args = "-serial unix:/var/run/qemu-server/{}.serial,server,nowait".format(vmid)

  proxmox_node = proxmox.nodes(node)

  # Sanitize kwargs. Remove not defined args and ensure True and False converted to int.
  kwargs = dict((k,v) for k, v in kwargs.iteritems() if v is not None)
  kwargs.update(dict([k, int(v)] for k, v in kwargs.iteritems() if isinstance(v, bool)))

  # The features work only on PVE 4
  if PVE_MAJOR_VERSION < 4:
    for p in only_v4:
      if p in kwargs:
         del kwargs[p]

  # Convert all dict in kwargs to elements. For hostpci[n], ide[n], net[n], numa[n], parallel[n], sata[n], scsi[n], serial[n], virtio[n]
  for k in kwargs.keys():
    if isinstance(kwargs[k], dict):
      kwargs.update(kwargs[k])
      del kwargs[k]

  # -args and skiplock require root@pam user
  if module.params['api_user'] == "root@pam" and module.params['args'] is None:
    kwargs['args'] = vm_args
  elif module.params['api_user'] == "root@pam" and module.params['args'] is not None:
    kwargs['args'] = module.params['args']
  elif module.params['api_user'] != "root@pam" and module.params['args'] is not None:
    module.fail_json(msg='args parameter require root@pam user. ')

  if module.params['api_user'] != "root@pam" and module.params['skiplock'] is not None:
    module.fail_json(msg='skiplock parameter require root@pam user. ')

  taskid = getattr(proxmox_node, VZ_TYPE).create(vmid=vmid, name=name, memory=memory, cpu=cpu, cores=cores, sockets=sockets, **kwargs)

  while timeout:
    if ( proxmox_node.tasks(taskid).status.get()['status'] == 'stopped'
        and proxmox_node.tasks(taskid).status.get()['exitstatus'] == 'OK' ):
      return True
    timeout = timeout - 1
    if timeout == 0:
      module.fail_json(msg='Reached timeout while waiting for creating VM. Last line in task before timeout: %s'
                       % proxmox_node.tasks(taskid).log.get()[:1])
    time.sleep(1)
  return False

def start_vm(module, proxmox, vm, vmid, timeout):
  taskid = getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.start.post()
  while timeout:
    if ( proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['status'] == 'stopped'
        and proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['exitstatus'] == 'OK' ):
      return True
    timeout = timeout - 1
    if timeout == 0:
      module.fail_json(msg='Reached timeout while waiting for starting VM. Last line in task before timeout: %s'
                       % proxmox.nodes(vm[0]['node']).tasks(taskid).log.get()[:1])

    time.sleep(1)
  return False

def stop_vm(module, proxmox, vm, vmid, timeout, force):
  if force:
    taskid = getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.shutdown.post(forceStop=1)
  else:
    taskid = getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.shutdown.post()
  while timeout:
    if ( proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['status'] == 'stopped'
        and proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['exitstatus'] == 'OK' ):
      return True
    timeout = timeout - 1
    if timeout == 0:
      module.fail_json(msg='Reached timeout while waiting for stopping VM. Last line in task before timeout: %s'
                       % proxmox.nodes(vm[0]['node']).tasks(taskid).log.get()[:1])

    time.sleep(1)
  return False

def main():
  module = AnsibleModule(
    argument_spec = dict(
      acpi = dict(type='bool', default='yes'),
      agent = dict(type='bool'),
      args = dict(type='str', default=None),
      api_host = dict(required=True),
      api_user = dict(required=True),
      api_password = dict(no_log=True),
      autostart = dict(type='bool', default='no'),
      balloon = dict(type='int',default=0),
      bios = dict(choices=['seabios', 'ovmf']),
      boot = dict(type='str', default='cnd'),
      bootdisk = dict(type='str'),
      cores = dict(type='int', default=1),
      cpu = dict(type='str', default='kvm64'),
      cpulimit = dict(type='int'),
      cpuunits = dict(type='int', default=1000),
      delete = dict(type='str'),
      description = dict(type='str'),
      digest = dict(type='str'),
      force = dict(type='bool', default=None),
      freeze = dict(type='bool'),
      hostpci = dict(type='dict'),
      hotplug = dict(type='str'),
      hugepages = dict(choices=['any', '2', '1024']),
      ide = dict(type='dict', default=None),
      keyboard = dict(type='str'),
      kvm = dict(type='bool', default='yes'),
      localtime = dict(type='bool'),
      lock = dict(choices=['migrate', 'backup', 'snapshot', 'rollback']),
      machine = dict(type='str'),
      memory = dict(type='int', default=512),
      migrate_downtime = dict(type='int'),
      migrate_speed = dict(type='int'),
      name = dict(type='str'),
      net = dict(type='dict'),
      node = dict(),
      numa = dict(type='dict'),
      onboot = dict(type='bool', default='yes'),
      ostype = dict(default='l26', choices=['other', 'wxp', 'w2k', 'w2k3', 'w2k8', 'wvista', 'win7', 'win8', 'l24', 'l26', 'solaris']),
      parallel = dict(type='dict'),
      protection = dict(type='bool'),
      reboot = dict(type='bool'),
      revert = dict(),
      sata = dict(type='dict'),
      scsi = dict(type='dict'),
      scsihw = dict(choices=['lsi', 'lsi53c810', 'virtio-scsi-pci', 'virtio-scsi-single', 'megasas', 'pvscsi']),
      serial = dict(type='dict'),
      shares = dict(type='int'),
      skiplock = dict(type='bool'),
      smbios = dict(type='str'),
      sockets = dict(type='int', default=1),
      startdate = dict(type='str'),
      startup = dict(),
      state = dict(default='present', choices=['present', 'absent', 'stopped', 'started', 'restarted', 'current']),
      tablet = dict(type='bool', default='no'),
      tdf = dict(type='bool'),
      template = dict(type='bool', default='no'),
      timeout = dict(type='int', default=30),
      validate_certs = dict(type='bool', default='no'),
      vcpus = dict(type='int', default=None),
      vga = dict(default='std', choices=['std', 'cirrus', 'vmware', 'qxl', 'serial0', 'serial1', 'serial2', 'serial3', 'qxl2', 'qxl3', 'qxl4']),
      virtio = dict(type='dict', default=None),
      vmid = dict(type='int', default=None),
      watchdog = dict(),
    )
  )

  if not HAS_PROXMOXER:
    module.fail_json(msg='proxmoxer required for this module')

  api_user = module.params['api_user']
  api_host = module.params['api_host']
  api_password = module.params['api_password']
  cpu = module.params['cpu']
  cores = module.params['cores']
  memory = module.params['memory']
  name = module.params['name']
  node = module.params['node']
  sockets = module.params['sockets'],
  state = module.params['state']
  timeout = module.params['timeout']
  validate_certs = module.params['validate_certs']

  # If password not set get it from PROXMOX_PASSWORD env
  if not api_password:
    try:
      api_password = os.environ['PROXMOX_PASSWORD']
    except KeyError as e:
      module.fail_json(msg='You should set api_password param or use PROXMOX_PASSWORD environment variable')

  try:
    proxmox = ProxmoxAPI(api_host, user=api_user, password=api_password, verify_ssl=validate_certs)
    global VZ_TYPE
    global PVE_MAJOR_VERSION
    PVE_MAJOR_VERSION = 3 if float(proxmox.version.get()['version']) < 4.0 else 4
  except Exception as e:
    module.fail_json(msg='authorization on proxmox cluster failed with exception: %s' % e)


  # If vmid not set get the Next VM id from ProxmoxAPI
  # If vm name is set get the VM id from ProxmoxAPI
  if module.params['vmid'] is not None:
    vmid = module.params['vmid']
  elif state == 'present':
    vmid = get_nextvmid(proxmox)
  elif module.params['name'] is not None:
    vmid = get_vmid(proxmox, name)[0]

  if state == 'present':
    try:
      if get_vm(proxmox, vmid) and not module.params['force']:
        module.exit_json(changed=False, msg="VM with vmid <%s> already exists" % vmid)
      elif get_vmid(proxmox, name) and not module.params['force']:
        module.exit_json(changed=False, msg="VM with name <%s> already exists" % name)
      elif not (node, module.params['name']):
        module.fail_json(msg='node, name is mandatory for creating vm')
      elif not node_check(proxmox, node):
        module.fail_json(msg="node '%s' does not exist in cluster" % node)

      create_vm(module, proxmox, vmid, node, name, memory, cpu, cores, sockets, timeout,
                      acpi = module.params['acpi'],
                      agent = module.params['agent'],
                      autostart = module.params['autostart'],
                      balloon = module.params['balloon'],
                      bios = module.params['bios'],
                      boot = module.params['boot'],
                      bootdisk = module.params['bootdisk'],
                      cpulimit = module.params['cpulimit'],
                      cpuunits = module.params['cpuunits'],
                      delete = module.params['delete'],
                      description = module.params['description'],
                      digest = module.params['digest'],
                      force = module.params['force'],
                      freeze = module.params['freeze'],
                      hostpci = module.params['hostpci'],
                      hotplug = module.params['hotplug'],
                      hugepages = module.params['hugepages'],
                      ide = module.params['ide'],
                      keyboard = module.params['keyboard'],
                      kvm = module.params['kvm'],
                      localtime = module.params['localtime'],
                      lock = module.params['lock'],
                      machine = module.params['machine'],
                      migrate_downtime = module.params['migrate_downtime'],
                      migrate_speed = module.params['migrate_speed'],
                      net = module.params['net'],
                      numa = module.params['numa'],
                      onboot = module.params['onboot'],
                      ostype = module.params['ostype'],
                      parallel = module.params['parallel'],
                      protection = module.params['protection'],
                      reboot = module.params['reboot'],
                      revert = module.params['revert'],
                      sata = module.params['sata'],
                      scsi = module.params['scsi'],
                      scsihw = module.params['scsihw'],
                      serial = module.params['serial'],
                      shares = module.params['shares'],
                      skiplock = module.params['skiplock'],
                      smbios1 = module.params['smbios'],
                      startdate = module.params['startdate'],
                      startup = module.params['startup'],
                      tablet = module.params['tablet'],
                      tdf = module.params['tdf'],
                      template = module.params['template'],
                      vcpus = module.params['vcpus'],
                      vga = module.params['vga'],
                      virtio = module.params['virtio'],
                      watchdog = module.params['watchdog'])

      get_vminfo(module, proxmox, node, vmid,
              ide = module.params['ide'],
              net = module.params['net'],
              sata = module.params['sata'],
              scsi = module.params['scsi'],
              virtio = module.params['virtio'])
      module.exit_json(changed=True, msg="VM %s with vmid %s deployed" % (name, vmid), **results)
    except Exception as e:
          module.fail_json(msg="creation of %s VM %s with vmid %s failed with exception: %s" % ( VZ_TYPE, name, vmid, e ))

  elif state == 'started':
    try:
      vm = get_vm(proxmox, vmid)
      if not vm:
        module.fail_json(msg='VM with vmid <%s> does not exist in cluster' % vmid)
      if getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.current.get()['status'] == 'running':
        module.exit_json(changed=False, msg="VM %s is already running" % vmid)

      if start_vm(module, proxmox, vm, vmid, timeout):
        module.exit_json(changed=True, msg="VM %s started" % vmid)
    except Exception as e:
      module.fail_json(msg="starting of VM %s failed with exception: %s" % ( vmid, e ))

  elif state == 'stopped':
    try:
      vm = get_vm(proxmox, vmid)
      if not vm:
        module.fail_json(msg='VM with vmid = %s does not exist in cluster' % vmid)

      if getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.current.get()['status'] == 'stopped':
        module.exit_json(changed=False, msg="VM %s is already stopped" % vmid)

      if stop_vm(module, proxmox, vm, vmid, timeout, force = module.params['force']):
        module.exit_json(changed=True, msg="VM %s is shutting down" % vmid)
    except Exception as e:
      module.fail_json(msg="stopping of VM %s failed with exception: %s" % ( vmid, e ))

  elif state == 'restarted':
    try:
      vm = get_vm(proxmox, vmid)
      if not vm:
        module.fail_json(msg='VM with vmid = %s does not exist in cluster' % vmid)
      if getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.current.get()['status'] == 'stopped':
        module.exit_json(changed=False, msg="VM %s is not running" % vmid)

      if ( stop_vm(module, proxmox, vm, vmid, timeout, force = module.params['force']) and
          start_vm(module, proxmox, vm, vmid, timeout) ):
        module.exit_json(changed=True, msg="VM %s is restarted" % vmid)
    except Exception as e:
      module.fail_json(msg="restarting of VM %s failed with exception: %s" % ( vmid, e ))

  elif state == 'absent':
    try:
      vm = get_vm(proxmox, vmid)
      if not vm:
        module.exit_json(changed=False, msg="VM %s does not exist" % vmid)

      if getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.current.get()['status'] == 'running':
        module.exit_json(changed=False, msg="VM %s is running. Stop it before deletion." % vmid)

      taskid = getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE).delete(vmid)
      while timeout:
        if ( proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['status'] == 'stopped'
            and proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['exitstatus'] == 'OK' ):
          module.exit_json(changed=True, msg="VM %s removed" % vmid)
        timeout = timeout - 1
        if timeout == 0:
          module.fail_json(msg='Reached timeout while waiting for removing VM. Last line in task before timeout: %s'
                           % proxmox_node.tasks(taskid).log.get()[:1])

        time.sleep(1)
    except Exception as e:
      module.fail_json(msg="deletion of VM %s failed with exception: %s" % ( vmid, e ))
  
  elif state == 'current':
    status = {}
    try:
      vm = get_vm(proxmox, vmid)
      if not vm:
        module.fail_json(msg='VM with vmid = %s does not exist in cluster' % vmid)
      current = getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.current.get()['status']
      status['status'] = current
      if status:
         module.exit_json(changed=False, msg="VM %s with vmid = %s is %s" % (name, vmid, current), **status)
    except Exception as e:
      module.fail_json(msg="Unable to get vm {} with vmid = {} status: ".format(name, vmid) + str(e))

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
