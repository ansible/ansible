#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Abdoul Bah (@helldorado) <bahabdoul at gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: proxmox_kvm
short_description: Management of Qemu(KVM) Virtual Machines in Proxmox VE cluster.
description:
  - Allows you to create/delete/stop Qemu(KVM) Virtual Machines in Proxmox VE cluster.
version_added: "2.3"
author: "Abdoul Bah (@helldorado) <bahabdoul at gmail.com>"
options:
  acpi:
    description:
      - Specify if ACPI should be enabled/disabled.
    type: bool
    default: 'yes'
  agent:
    description:
      - Specify if the QEMU Guest Agent should be enabled/disabled.
    type: bool
  args:
    description:
      - Pass arbitrary arguments to kvm.
      - This option is for experts only!
    default: "-serial unix:/var/run/qemu-server/VMID.serial,server,nowait"
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
  autostart:
    description:
      - Specify if the VM should be automatically restarted after crash (currently ignored in PVE API).
    type: bool
    default: 'no'
  balloon:
    description:
      - Specify the amount of RAM for the VM in MB.
      - Using zero disables the balloon driver.
    default: 0
  bios:
    description:
      - Specify the BIOS implementation.
    choices: ['seabios', 'ovmf']
  boot:
    description:
      - Specify the boot order -> boot on floppy C(a), hard disk C(c), CD-ROM C(d), or network C(n).
      - You can combine to set order.
    default: cnd
  bootdisk:
    description:
      - Enable booting from specified disk. C((ide|sata|scsi|virtio)\d+)
  clone:
    description:
      - Name of VM to be cloned. If C(vmid) is setted, C(clone) can take arbitrary value but required for intiating the clone.
  cores:
    description:
      - Specify number of cores per socket.
    default: 1
  cpu:
    description:
      - Specify emulated CPU type.
    default: kvm64
  cpulimit:
    description:
      - Specify if CPU usage will be limited. Value 0 indicates no CPU limit.
      - If the computer has 2 CPUs, it has total of '2' CPU time
  cpuunits:
    description:
      - Specify CPU weight for a VM.
      - You can disable fair-scheduler configuration by setting this to 0
    default: 1000
  delete:
    description:
      - Specify a list of settings you want to delete.
  description:
    description:
      - Specify the description for the VM. Only used on the configuration web interface.
      - This is saved as comment inside the configuration file.
  digest:
    description:
      - Specify if to prevent changes if current configuration file has different SHA1 digest.
      - This can be used to prevent concurrent modifications.
  force:
    description:
      - Allow to force stop VM.
      - Can be used only with states C(stopped), C(restarted).
    type: bool
  format:
    description:
      - Target drive's backing file's data format.
      - Used only with clone
    default: qcow2
    choices: [ "cloop", "cow", "qcow", "qcow2", "qed", "raw", "vmdk" ]
  freeze:
    description:
      - Specify if PVE should freeze CPU at startup (use 'c' monitor command to start execution).
    type: bool
  full:
    description:
      - Create a full copy of all disk. This is always done when you clone a normal VM.
      - For VM templates, we try to create a linked clone by default.
      - Used only with clone
    type: bool
    default: 'yes'
  hostpci:
    description:
      - Specify a hash/dictionary of map host pci devices into guest. C(hostpci='{"key":"value", "key":"value"}').
      - Keys allowed are - C(hostpci[n]) where 0 ≤ n ≤ N.
      - Values allowed are -  C("host="HOSTPCIID[;HOSTPCIID2...]",pcie="1|0",rombar="1|0",x-vga="1|0"").
      - The C(host) parameter is Host PCI device pass through. HOSTPCIID syntax is C(bus:dev.func) (hexadecimal numbers).
      - C(pcie=boolean) I(default=0) Choose the PCI-express bus (needs the q35 machine model).
      - C(rombar=boolean) I(default=1) Specify whether or not the device's ROM will be visible in the guest's memory map.
      - C(x-vga=boolean) I(default=0) Enable vfio-vga device support.
      - /!\ This option allows direct access to host hardware. So it is no longer possible to migrate such machines - use with special care.
  hotplug:
    description:
      - Selectively enable hotplug features.
      - This is a comma separated list of hotplug features C('network', 'disk', 'cpu', 'memory' and 'usb').
      - Value 0 disables hotplug completely and value 1 is an alias for the default C('network,disk,usb').
  hugepages:
    description:
      - Enable/disable hugepages memory.
    choices: ['any', '2', '1024']
  ide:
    description:
      - A hash/dictionary of volume used as IDE hard disk or CD-ROM. C(ide='{"key":"value", "key":"value"}').
      - Keys allowed are - C(ide[n]) where 0 ≤ n ≤ 3.
      - Values allowed are - C("storage:size,format=value").
      - C(storage) is the storage identifier where to create the disk.
      - C(size) is the size of the disk in GB.
      - C(format) is the drive's backing file's data format. C(qcow2|raw|subvol).
  keyboard:
    description:
      - Sets the keyboard layout for VNC server.
  kvm:
    description:
      - Enable/disable KVM hardware virtualization.
    type: bool
    default: 'yes'
  localtime:
    description:
      - Sets the real time clock to local time.
      - This is enabled by default if ostype indicates a Microsoft OS.
    type: bool
  lock:
    description:
      - Lock/unlock the VM.
    choices: ['migrate', 'backup', 'snapshot', 'rollback']
  machine:
    description:
      - Specifies the Qemu machine type.
      - type => C((pc|pc(-i440fx)?-\d+\.\d+(\.pxe)?|q35|pc-q35-\d+\.\d+(\.pxe)?))
  memory:
    description:
      - Memory size in MB for instance.
    default: 512
  migrate_downtime:
    description:
      - Sets maximum tolerated downtime (in seconds) for migrations.
  migrate_speed:
    description:
      - Sets maximum speed (in MB/s) for migrations.
      - A value of 0 is no limit.
  name:
    description:
      - Specifies the VM name. Only used on the configuration web interface.
      - Required only for C(state=present).
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
  newid:
    description:
      - VMID for the clone. Used only with clone.
      - If newid is not set, the next available VM ID will be fetched from ProxmoxAPI.
  node:
    description:
      - Proxmox VE node, where the new VM will be created.
      - Only required for C(state=present).
      - For other states, it will be autodiscovered.
  numa:
    description:
      - A hash/dictionaries of NUMA topology. C(numa='{"key":"value", "key":"value"}').
      - Keys allowed are - C(numa[n]) where 0 ≤ n ≤ N.
      - Values allowed are - C("cpu="<id[-id];...>",hostnodes="<id[-id];...>",memory="number",policy="(bind|interleave|preferred)"").
      - C(cpus) CPUs accessing this NUMA node.
      - C(hostnodes) Host NUMA nodes to use.
      - C(memory) Amount of memory this NUMA node provides.
      - C(policy) NUMA allocation policy.
  onboot:
    description:
      - Specifies whether a VM will be started during system bootup.
    type: bool
    default: 'yes'
  ostype:
    description:
      - Specifies guest operating system. This is used to enable special optimization/features for specific operating systems.
      - The l26 is Linux 2.6/3.X Kernel.
    choices: ['other', 'wxp', 'w2k', 'w2k3', 'w2k8', 'wvista', 'win7', 'win8', 'l24', 'l26', 'solaris']
    default: l26
  parallel:
    description:
      - A hash/dictionary of map host parallel devices. C(parallel='{"key":"value", "key":"value"}').
      - Keys allowed are - (parallel[n]) where 0 ≤ n ≤ 2.
      - Values allowed are - C("/dev/parport\d+|/dev/usb/lp\d+").
  pool:
    description:
      - Add the new VM to the specified pool.
  protection:
    description:
      - Enable/disable the protection flag of the VM. This will enable/disable the remove VM and remove disk operations.
    type: bool
  reboot:
    description:
      - Allow reboot. If set to C(yes), the VM exit on reboot.
    type: bool
  revert:
    description:
      - Revert a pending change.
  sata:
    description:
      - A hash/dictionary of volume used as sata hard disk or CD-ROM. C(sata='{"key":"value", "key":"value"}').
      - Keys allowed are - C(sata[n]) where 0 ≤ n ≤ 5.
      - Values allowed are -  C("storage:size,format=value").
      - C(storage) is the storage identifier where to create the disk.
      - C(size) is the size of the disk in GB.
      - C(format) is the drive's backing file's data format. C(qcow2|raw|subvol).
  scsi:
    description:
      - A hash/dictionary of volume used as SCSI hard disk or CD-ROM. C(scsi='{"key":"value", "key":"value"}').
      - Keys allowed are - C(sata[n]) where 0 ≤ n ≤ 13.
      - Values allowed are -  C("storage:size,format=value").
      - C(storage) is the storage identifier where to create the disk.
      - C(size) is the size of the disk in GB.
      - C(format) is the drive's backing file's data format. C(qcow2|raw|subvol).
  scsihw:
    description:
      - Specifies the SCSI controller model.
    choices: ['lsi', 'lsi53c810', 'virtio-scsi-pci', 'virtio-scsi-single', 'megasas', 'pvscsi']
  serial:
    description:
      - A hash/dictionary of serial device to create inside the VM. C('{"key":"value", "key":"value"}').
      - Keys allowed are - serial[n](str; required) where 0 ≤ n ≤ 3.
      - Values allowed are - C((/dev/.+|socket)).
      - /!\ If you pass through a host serial device, it is no longer possible to migrate such machines - use with special care.
  shares:
    description:
      - Rets amount of memory shares for auto-ballooning. (0 - 50000).
      - The larger the number is, the more memory this VM gets.
      - The number is relative to weights of all other running VMs.
      - Using 0 disables auto-ballooning, this means no limit.
  skiplock:
    description:
      - Ignore locks
      - Only root is allowed to use this option.
  smbios:
    description:
      - Specifies SMBIOS type 1 fields.
  snapname:
    description:
      - The name of the snapshot. Used only with clone.
  sockets:
    description:
      - Sets the number of CPU sockets. (1 - N).
    default: 1
  startdate:
    description:
      - Sets the initial date of the real time clock.
      - Valid format for date are C('now') or C('2016-09-25T16:01:21') or C('2016-09-25').
  startup:
    description:
      - Startup and shutdown behavior. C([[order=]\d+] [,up=\d+] [,down=\d+]).
      - Order is a non-negative number defining the general startup order.
      - Shutdown in done with reverse ordering.
  state:
    description:
      - Indicates desired state of the instance.
      - If C(current), the current state of the VM will be fecthed. You can access it with C(results.status)
    choices: ['present', 'started', 'absent', 'stopped', 'restarted','current']
    default: present
  storage:
    description:
      - Target storage for full clone.
  tablet:
    description:
      - Enables/disables the USB tablet device.
    type: bool
    default: 'no'
  target:
    description:
      - Target node. Only allowed if the original VM is on shared storage.
      - Used only with clone
  tdf:
    description:
      - Enables/disables time drift fix.
    type: bool
  template:
    description:
      - Enables/disables the template.
    type: bool
    default: 'no'
  timeout:
    description:
      - Timeout for operations.
    default: 30
  update:
    description:
      - If C(yes), the VM will be update with new value.
      - Cause of the operations of the API and security reasons, I have disabled the update of the following parameters
      - C(net, virtio, ide, sata, scsi). Per example updating C(net) update the MAC address and C(virtio) create always new disk...
    type: bool
    default: 'no'
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'no'
  vcpus:
    description:
      - Sets number of hotplugged vcpus.
  vga:
    description:
      - Select VGA type. If you want to use high resolution modes (>= 1280x1024x16) then you should use option 'std' or 'vmware'.
    choices: ['std', 'cirrus', 'vmware', 'qxl', 'serial0', 'serial1', 'serial2', 'serial3', 'qxl2', 'qxl3', 'qxl4']
    default: std
  virtio:
    description:
      - A hash/dictionary of volume used as VIRTIO hard disk. C(virtio='{"key":"value", "key":"value"}').
      - Keys allowed are - C(virto[n]) where 0 ≤ n ≤ 15.
      - Values allowed are -  C("storage:size,format=value").
      - C(storage) is the storage identifier where to create the disk.
      - C(size) is the size of the disk in GB.
      - C(format) is the drive's backing file's data format. C(qcow2|raw|subvol).
  vmid:
    description:
      - Specifies the VM ID. Instead use I(name) parameter.
      - If vmid is not set, the next available VM ID will be fetched from ProxmoxAPI.
  watchdog:
    description:
      - Creates a virtual hardware watchdog device.
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

# Clone VM with only source VM name
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    clone       : spynal   # The VM source
    name        : zavala  # The target VM name
    node        : sabrewulf
    storage     : VMs
    format      : qcow2
    timeout     : 500  # Note: The task can take a while. Adapt

# Clone VM with source vmid and target newid and raw format
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    clone       : arbitrary_name
    vmid        : 108
    newid       : 152
    name        : zavala  # The target VM name
    node        : sabrewulf
    storage     : LVM_STO
    format      : raw
    timeout     : 300  # Note: The task can take a while. Adapt

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

# Update VM configuration
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    cpu         : 8
    memory      : 16384
    update      : yes

# Delete QEMU parameters
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    delete      : 'args,template,cpulimit'

# Revert a pending change
- proxmox_kvm:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : spynal
    node        : sabrewulf
    revert      : 'template,cpulimit'
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
import re
import time
import traceback

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


VZ_TYPE = 'qemu'


def get_nextvmid(module, proxmox):
    try:
        vmid = proxmox.cluster.nextid.get()
        return vmid
    except Exception as e:
        module.fail_json(msg="Unable to get next vmid. Failed with exception: %s" % to_native(e),
                         exception=traceback.format_exc())


def get_vmid(proxmox, name):
    return [vm['vmid'] for vm in proxmox.cluster.resources.get(type='vm') if vm['name'] == name]


def get_vm(proxmox, vmid):
    return [vm for vm in proxmox.cluster.resources.get(type='vm') if vm['vmid'] == int(vmid)]


def node_check(proxmox, node):
    return [True for nd in proxmox.nodes.get() if nd['node'] == node]


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
    kwargs = dict((k, v) for k, v in kwargs.items() if v is not None)

    # Convert all dict in kwargs to elements. For hostpci[n], ide[n], net[n], numa[n], parallel[n], sata[n], scsi[n], serial[n], virtio[n]
    for k in kwargs.keys():
        if isinstance(kwargs[k], dict):
            kwargs.update(kwargs[k])
            del kwargs[k]

    # Split information by type
    for k, v in kwargs.items():
        if re.match(r'net[0-9]', k) is not None:
            interface = k
            k = vm[k]
            k = re.search('=(.*?),', k).group(1)
            mac[interface] = k
        if (re.match(r'virtio[0-9]', k) is not None or
                re.match(r'ide[0-9]', k) is not None or
                re.match(r'scsi[0-9]', k) is not None or
                re.match(r'sata[0-9]', k) is not None):
            device = k
            k = vm[k]
            k = re.search('(.*?),', k).group(1)
            devices[device] = k

    results['mac'] = mac
    results['devices'] = devices
    results['vmid'] = int(vmid)


def settings(module, proxmox, vmid, node, name, timeout, **kwargs):
    proxmox_node = proxmox.nodes(node)

    # Sanitize kwargs. Remove not defined args and ensure True and False converted to int.
    kwargs = dict((k, v) for k, v in kwargs.items() if v is not None)

    if getattr(proxmox_node, VZ_TYPE)(vmid).config.set(**kwargs) is None:
        return True
    else:
        return False


def create_vm(module, proxmox, vmid, newid, node, name, memory, cpu, cores, sockets, timeout, update, **kwargs):
    # Available only in PVE 4
    only_v4 = ['force', 'protection', 'skiplock']

    # valide clone parameters
    valid_clone_params = ['format', 'full', 'pool', 'snapname', 'storage', 'target']
    clone_params = {}
    # Default args for vm. Note: -args option is for experts only. It allows you to pass arbitrary arguments to kvm.
    vm_args = "-serial unix:/var/run/qemu-server/{}.serial,server,nowait".format(vmid)

    proxmox_node = proxmox.nodes(node)

    # Sanitize kwargs. Remove not defined args and ensure True and False converted to int.
    kwargs = dict((k, v) for k, v in kwargs.items() if v is not None)
    kwargs.update(dict([k, int(v)] for k, v in kwargs.items() if isinstance(v, bool)))

    # The features work only on PVE 4
    if PVE_MAJOR_VERSION < 4:
        for p in only_v4:
            if p in kwargs:
                del kwargs[p]

    # If update, don't update disk (virtio, ide, sata, scsi) and network interface
    if update:
        if 'virtio' in kwargs:
            del kwargs['virtio']
        if 'sata' in kwargs:
            del kwargs['sata']
        if 'scsi' in kwargs:
            del kwargs['scsi']
        if 'ide' in kwargs:
            del kwargs['ide']
        if 'net' in kwargs:
            del kwargs['net']

    # Convert all dict in kwargs to elements. For hostpci[n], ide[n], net[n], numa[n], parallel[n], sata[n], scsi[n], serial[n], virtio[n]
    for k in kwargs.keys():
        if isinstance(kwargs[k], dict):
            kwargs.update(kwargs[k])
            del kwargs[k]

    # Rename numa_enabled  to numa. According the API documentation
    if 'numa_enabled' in kwargs:
        kwargs['numa'] = kwargs['numa_enabled']
        del kwargs['numa_enabled']

    # -args and skiplock require root@pam user
    if module.params['api_user'] == "root@pam" and module.params['args'] is None:
        if not update:
            kwargs['args'] = vm_args
    elif module.params['api_user'] == "root@pam" and module.params['args'] is not None:
        kwargs['args'] = module.params['args']
    elif module.params['api_user'] != "root@pam" and module.params['args'] is not None:
        module.fail_json(msg='args parameter require root@pam user. ')

    if module.params['api_user'] != "root@pam" and module.params['skiplock'] is not None:
        module.fail_json(msg='skiplock parameter require root@pam user. ')

    if update:
        if getattr(proxmox_node, VZ_TYPE)(vmid).config.set(name=name, memory=memory, cpu=cpu, cores=cores, sockets=sockets, **kwargs) is None:
            return True
        else:
            return False
    elif module.params['clone'] is not None:
        for param in valid_clone_params:
            if module.params[param] is not None:
                clone_params[param] = module.params[param]
        clone_params.update(dict([k, int(v)] for k, v in clone_params.items() if isinstance(v, bool)))
        taskid = proxmox_node.qemu(vmid).clone.post(newid=newid, name=name, **clone_params)
    else:
        taskid = getattr(proxmox_node, VZ_TYPE).create(vmid=vmid, name=name, memory=memory, cpu=cpu, cores=cores, sockets=sockets, **kwargs)

    while timeout:
        if (proxmox_node.tasks(taskid).status.get()['status'] == 'stopped' and
                proxmox_node.tasks(taskid).status.get()['exitstatus'] == 'OK'):
            return True
        timeout = timeout - 1
        if timeout == 0:
            module.fail_json(msg='Reached timeout while waiting for creating VM. Last line in task before timeout: %s' %
                                 proxmox_node.tasks(taskid).log.get()[:1])
        time.sleep(1)
    return False


def start_vm(module, proxmox, vm, vmid, timeout):
    taskid = getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.start.post()
    while timeout:
        if (proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['status'] == 'stopped' and
                proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['exitstatus'] == 'OK'):
            return True
        timeout -= 1
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
        if (proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['status'] == 'stopped' and
                proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['exitstatus'] == 'OK'):
            return True
        timeout -= 1
        if timeout == 0:
            module.fail_json(msg='Reached timeout while waiting for stopping VM. Last line in task before timeout: %s'
                             % proxmox.nodes(vm[0]['node']).tasks(taskid).log.get()[:1])
        time.sleep(1)
    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            acpi=dict(type='bool', default='yes'),
            agent=dict(type='bool'),
            args=dict(type='str', default=None),
            api_host=dict(required=True),
            api_user=dict(required=True),
            api_password=dict(no_log=True),
            autostart=dict(type='bool', default='no'),
            balloon=dict(type='int', default=0),
            bios=dict(choices=['seabios', 'ovmf']),
            boot=dict(type='str', default='cnd'),
            bootdisk=dict(type='str'),
            clone=dict(type='str', default=None),
            cores=dict(type='int', default=1),
            cpu=dict(type='str', default='kvm64'),
            cpulimit=dict(type='int'),
            cpuunits=dict(type='int', default=1000),
            delete=dict(type='str', default=None),
            description=dict(type='str'),
            digest=dict(type='str'),
            force=dict(type='bool', default=None),
            format=dict(type='str', default='qcow2', choices=['cloop', 'cow', 'qcow', 'qcow2', 'qed', 'raw', 'vmdk']),
            freeze=dict(type='bool'),
            full=dict(type='bool', default='yes'),
            hostpci=dict(type='dict'),
            hotplug=dict(type='str'),
            hugepages=dict(choices=['any', '2', '1024']),
            ide=dict(type='dict', default=None),
            keyboard=dict(type='str'),
            kvm=dict(type='bool', default='yes'),
            localtime=dict(type='bool'),
            lock=dict(choices=['migrate', 'backup', 'snapshot', 'rollback']),
            machine=dict(type='str'),
            memory=dict(type='int', default=512),
            migrate_downtime=dict(type='int'),
            migrate_speed=dict(type='int'),
            name=dict(type='str'),
            net=dict(type='dict'),
            newid=dict(type='int', default=None),
            node=dict(),
            numa=dict(type='dict'),
            numa_enabled=dict(type='bool'),
            onboot=dict(type='bool', default='yes'),
            ostype=dict(default='l26', choices=['other', 'wxp', 'w2k', 'w2k3', 'w2k8', 'wvista', 'win7', 'win8', 'l24', 'l26', 'solaris']),
            parallel=dict(type='dict'),
            pool=dict(type='str'),
            protection=dict(type='bool'),
            reboot=dict(type='bool'),
            revert=dict(type='str', default=None),
            sata=dict(type='dict'),
            scsi=dict(type='dict'),
            scsihw=dict(choices=['lsi', 'lsi53c810', 'virtio-scsi-pci', 'virtio-scsi-single', 'megasas', 'pvscsi']),
            serial=dict(type='dict'),
            shares=dict(type='int'),
            skiplock=dict(type='bool'),
            smbios=dict(type='str'),
            snapname=dict(type='str'),
            sockets=dict(type='int', default=1),
            startdate=dict(type='str'),
            startup=dict(),
            state=dict(default='present', choices=['present', 'absent', 'stopped', 'started', 'restarted', 'current']),
            storage=dict(type='str'),
            tablet=dict(type='bool', default='no'),
            target=dict(type='str'),
            tdf=dict(type='bool'),
            template=dict(type='bool', default='no'),
            timeout=dict(type='int', default=30),
            update=dict(type='bool', default='no'),
            validate_certs=dict(type='bool', default='no'),
            vcpus=dict(type='int', default=None),
            vga=dict(default='std', choices=['std', 'cirrus', 'vmware', 'qxl', 'serial0', 'serial1', 'serial2', 'serial3', 'qxl2', 'qxl3', 'qxl4']),
            virtio=dict(type='dict', default=None),
            vmid=dict(type='int', default=None),
            watchdog=dict(),
        ),
        mutually_exclusive=[('delete', 'revert'), ('delete', 'update'), ('revert', 'update'), ('clone', 'update'), ('clone', 'delete'), ('clone', 'revert')],
        required_one_of=[('name', 'vmid',)],
        required_if=[('state', 'present', ['node'])]
    )

    if not HAS_PROXMOXER:
        module.fail_json(msg='proxmoxer required for this module')

    api_user = module.params['api_user']
    api_host = module.params['api_host']
    api_password = module.params['api_password']
    clone = module.params['clone']
    cpu = module.params['cpu']
    cores = module.params['cores']
    delete = module.params['delete']
    memory = module.params['memory']
    name = module.params['name']
    newid = module.params['newid']
    node = module.params['node']
    revert = module.params['revert']
    sockets = module.params['sockets']
    state = module.params['state']
    timeout = module.params['timeout']
    update = bool(module.params['update'])
    vmid = module.params['vmid']
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
    if not vmid:
        if state == 'present' and (not update and not clone) and (not delete and not revert):
            try:
                vmid = get_nextvmid(module, proxmox)
            except Exception as e:
                module.fail_json(msg="Can't get the next vimd for VM {} automatically. Ensure your cluster state is good".format(name))
        else:
            try:
                if not clone:
                    vmid = get_vmid(proxmox, name)[0]
                else:
                    vmid = get_vmid(proxmox, clone)[0]
            except Exception as e:
                if not clone:
                    module.fail_json(msg="VM {} does not exist in cluster.".format(name))
                else:
                    module.fail_json(msg="VM {} does not exist in cluster.".format(clone))

    if clone is not None:
        if get_vmid(proxmox, name):
            module.exit_json(changed=False, msg="VM with name <%s> already exists" % name)
        if vmid is not None:
            vm = get_vm(proxmox, vmid)
            if not vm:
                module.fail_json(msg='VM with vmid = %s does not exist in cluster' % vmid)
        if not newid:
            try:
                newid = get_nextvmid(module, proxmox)
            except Exception as e:
                module.fail_json(msg="Can't get the next vimd for VM {} automatically. Ensure your cluster state is good".format(name))
        else:
            vm = get_vm(proxmox, newid)
            if vm:
                module.exit_json(changed=False, msg="vmid %s with VM name %s already exists" % (newid, name))

    if delete is not None:
        try:
            settings(module, proxmox, vmid, node, name, timeout, delete=delete)
            module.exit_json(changed=True, msg="Settings has deleted on VM {} with vmid {}".format(name, vmid))
        except Exception as e:
            module.fail_json(msg='Unable to delete settings on VM {} with vimd {}: '.format(name, vmid) + str(e))
    elif revert is not None:
        try:
            settings(module, proxmox, vmid, node, name, timeout, revert=revert)
            module.exit_json(changed=True, msg="Settings has reverted on VM {} with vmid {}".format(name, vmid))
        except Exception as e:
            module.fail_json(msg='Unable to revert settings on VM {} with vimd {}: Maybe is not a pending task...   '.format(name, vmid) + str(e))

    if state == 'present':
        try:
            if get_vm(proxmox, vmid) and not (update or clone):
                module.exit_json(changed=False, msg="VM with vmid <%s> already exists" % vmid)
            elif get_vmid(proxmox, name) and not (update or clone):
                module.exit_json(changed=False, msg="VM with name <%s> already exists" % name)
            elif not (node, name):
                module.fail_json(msg='node, name is mandatory for creating/updating vm')
            elif not node_check(proxmox, node):
                module.fail_json(msg="node '%s' does not exist in cluster" % node)

            create_vm(module, proxmox, vmid, newid, node, name, memory, cpu, cores, sockets, timeout, update,
                      acpi=module.params['acpi'],
                      agent=module.params['agent'],
                      autostart=module.params['autostart'],
                      balloon=module.params['balloon'],
                      bios=module.params['bios'],
                      boot=module.params['boot'],
                      bootdisk=module.params['bootdisk'],
                      cpulimit=module.params['cpulimit'],
                      cpuunits=module.params['cpuunits'],
                      description=module.params['description'],
                      digest=module.params['digest'],
                      force=module.params['force'],
                      freeze=module.params['freeze'],
                      hostpci=module.params['hostpci'],
                      hotplug=module.params['hotplug'],
                      hugepages=module.params['hugepages'],
                      ide=module.params['ide'],
                      keyboard=module.params['keyboard'],
                      kvm=module.params['kvm'],
                      localtime=module.params['localtime'],
                      lock=module.params['lock'],
                      machine=module.params['machine'],
                      migrate_downtime=module.params['migrate_downtime'],
                      migrate_speed=module.params['migrate_speed'],
                      net=module.params['net'],
                      numa=module.params['numa'],
                      numa_enabled=module.params['numa_enabled'],
                      onboot=module.params['onboot'],
                      ostype=module.params['ostype'],
                      parallel=module.params['parallel'],
                      pool=module.params['pool'],
                      protection=module.params['protection'],
                      reboot=module.params['reboot'],
                      sata=module.params['sata'],
                      scsi=module.params['scsi'],
                      scsihw=module.params['scsihw'],
                      serial=module.params['serial'],
                      shares=module.params['shares'],
                      skiplock=module.params['skiplock'],
                      smbios1=module.params['smbios'],
                      snapname=module.params['snapname'],
                      startdate=module.params['startdate'],
                      startup=module.params['startup'],
                      tablet=module.params['tablet'],
                      target=module.params['target'],
                      tdf=module.params['tdf'],
                      template=module.params['template'],
                      vcpus=module.params['vcpus'],
                      vga=module.params['vga'],
                      virtio=module.params['virtio'],
                      watchdog=module.params['watchdog'])

            if not clone:
                get_vminfo(module, proxmox, node, vmid,
                           ide=module.params['ide'],
                           net=module.params['net'],
                           sata=module.params['sata'],
                           scsi=module.params['scsi'],
                           virtio=module.params['virtio'])
            if update:
                module.exit_json(changed=True, msg="VM %s with vmid %s updated" % (name, vmid))
            elif clone is not None:
                module.exit_json(changed=True, msg="VM %s with newid %s cloned from vm with vmid %s" % (name, newid, vmid))
            else:
                module.exit_json(changed=True, msg="VM %s with vmid %s deployed" % (name, vmid), **results)
        except Exception as e:
            if update:
                module.fail_json(msg="Unable to update vm {} with vimd {}=".format(name, vmid) + str(e))
            elif clone is not None:
                module.fail_json(msg="Unable to clone vm {} from vimd {}=".format(name, vmid) + str(e))
            else:
                module.fail_json(msg="creation of %s VM %s with vmid %s failed with exception=%s" % (VZ_TYPE, name, vmid, e))

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
            module.fail_json(msg="starting of VM %s failed with exception: %s" % (vmid, e))

    elif state == 'stopped':
        try:
            vm = get_vm(proxmox, vmid)
            if not vm:
                module.fail_json(msg='VM with vmid = %s does not exist in cluster' % vmid)

            if getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.current.get()['status'] == 'stopped':
                module.exit_json(changed=False, msg="VM %s is already stopped" % vmid)

            if stop_vm(module, proxmox, vm, vmid, timeout, force=module.params['force']):
                module.exit_json(changed=True, msg="VM %s is shutting down" % vmid)
        except Exception as e:
            module.fail_json(msg="stopping of VM %s failed with exception: %s" % (vmid, e))

    elif state == 'restarted':
        try:
            vm = get_vm(proxmox, vmid)
            if not vm:
                module.fail_json(msg='VM with vmid = %s does not exist in cluster' % vmid)
            if getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.current.get()['status'] == 'stopped':
                module.exit_json(changed=False, msg="VM %s is not running" % vmid)

            if stop_vm(module, proxmox, vm, vmid, timeout, force=module.params['force']) and start_vm(module, proxmox, vm, vmid, timeout):
                module.exit_json(changed=True, msg="VM %s is restarted" % vmid)
        except Exception as e:
            module.fail_json(msg="restarting of VM %s failed with exception: %s" % (vmid, e))

    elif state == 'absent':
        try:
            vm = get_vm(proxmox, vmid)
            if not vm:
                module.exit_json(changed=False, msg="VM %s does not exist" % vmid)

            if getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE)(vmid).status.current.get()['status'] == 'running':
                module.exit_json(changed=False, msg="VM %s is running. Stop it before deletion." % vmid)

            taskid = getattr(proxmox.nodes(vm[0]['node']), VZ_TYPE).delete(vmid)
            while timeout:
                if (proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['status'] == 'stopped' and
                        proxmox.nodes(vm[0]['node']).tasks(taskid).status.get()['exitstatus'] == 'OK'):
                    module.exit_json(changed=True, msg="VM %s removed" % vmid)
                timeout -= 1
                if timeout == 0:
                    module.fail_json(msg='Reached timeout while waiting for removing VM. Last line in task before timeout: %s'
                                     % proxmox.nodes(vm[0]['node']).tasks(taskid).log.get()[:1])

                time.sleep(1)
        except Exception as e:
            module.fail_json(msg="deletion of VM %s failed with exception: %s" % (vmid, e))

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


if __name__ == '__main__':
    main()
