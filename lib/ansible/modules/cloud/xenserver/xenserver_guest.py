#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: xenserver_guest
short_description: Manages virtual machines running on Citrix Hypervisor/XenServer host or pool
description: >
   This module can be used to create new virtual machines from templates or other virtual machines,
   modify various virtual machine components like network and disk, rename a virtual machine and
   remove a virtual machine with associated components.
version_added: '2.8'
author:
- Bojan Vitnik (@bvitnik) <bvitnik@mainstream.rs>
notes:
- Minimal supported version of XenServer is 5.6.
- Module was tested with XenServer 6.5, 7.1, 7.2, 7.6, Citrix Hypervisor 8.0, XCP-ng 7.6 and 8.0.
- 'To acquire XenAPI Python library, just run C(pip install XenAPI) on your Ansible Control Node. The library can also be found inside
   Citrix Hypervisor/XenServer SDK (downloadable from Citrix website). Copy the XenAPI.py file from the SDK to your Python site-packages on your
   Ansible Control Node to use it. Latest version of the library can also be acquired from GitHub:
   https://raw.githubusercontent.com/xapi-project/xen-api/master/scripts/examples/python/XenAPI.py'
- 'If no scheme is specified in C(hostname), module defaults to C(http://) because C(https://) is problematic in most setups. Make sure you are
   accessing XenServer host in trusted environment or use C(https://) scheme explicitly.'
- 'To use C(https://) scheme for C(hostname) you have to either import host certificate to your OS certificate store or use C(validate_certs: no)
   which requires XenAPI library from XenServer 7.2 SDK or newer and Python 2.7.9 or newer.'
- 'Network configuration inside a guest OS, by using C(networks.type), C(networks.ip), C(networks.gateway) etc. parameters, is supported on
  XenServer 7.0 or newer for Windows guests by using official XenServer Guest agent support for network configuration. The module will try to
  detect if such support is available and utilize it, else it will use a custom method of configuration via xenstore. Since XenServer Guest
  agent only support None and Static types of network configuration, where None means DHCP configured interface, C(networks.type) and C(networks.type6)
  values C(none) and C(dhcp) have same effect. More info here:
  https://www.citrix.com/community/citrix-developer/citrix-hypervisor-developer/citrix-hypervisor-developing-products/citrix-hypervisor-staticip.html'
- 'On platforms without official support for network configuration inside a guest OS, network parameters will be written to xenstore
  C(vm-data/networks/<vif_device>) key. Parameters can be inspected by using C(xenstore ls) and C(xenstore read) tools on \*nix guests or trough
  WMI interface on Windows guests. They can also be found in VM facts C(instance.xenstore_data) key as returned by the module. It is up to the user
  to implement a boot time scripts or custom agent that will read the parameters from xenstore and configure network with given parameters.
  Take note that for xenstore data to become available inside a guest, a VM restart is needed hence module will require VM restart if any
  parameter is changed. This is a limitation of XenAPI and xenstore. Considering these limitations, network configuration trough xenstore is most
  useful for bootstraping newly deployed VMs, much less for reconfiguring existing ones. More info here:
  https://support.citrix.com/article/CTX226713'
requirements:
- python >= 2.6
- XenAPI
options:
  state:
    description:
    - Specify the state VM should be in.
    - If C(state) is set to C(present) and VM exists, ensure the VM configuration conforms to given parameters.
    - If C(state) is set to C(present) and VM does not exist, then VM is deployed with given parameters.
    - If C(state) is set to C(absent) and VM exists, then VM is removed with its associated components.
    - If C(state) is set to C(poweredon) and VM does not exist, then VM is deployed with given parameters and powered on automatically.
    type: str
    default: present
    choices: [ present, absent, poweredon ]
  name:
    description:
    - Name of the VM to work with.
    - VMs running on XenServer do not necessarily have unique names. The module will fail if multiple VMs with same name are found.
    - In case of multiple VMs with same name, use C(uuid) to uniquely specify VM to manage.
    - This parameter is case sensitive.
    type: str
    required: yes
    aliases: [ name_label ]
  name_desc:
    description:
    - VM description.
    type: str
  uuid:
    description:
    - UUID of the VM to manage if known. This is XenServer's unique identifier.
    - It is required if name is not unique.
    - Please note that a supplied UUID will be ignored on VM creation, as XenServer creates the UUID internally.
    type: str
  template:
    description:
    - Name of a template, an existing VM (must be shut down) or a snapshot that should be used to create VM.
    - Templates/VMs/snapshots on XenServer do not necessarily have unique names. The module will fail if multiple templates with same name are found.
    - In case of multiple templates/VMs/snapshots with same name, use C(template_uuid) to uniquely specify source template.
    - If VM already exists, this setting will be ignored.
    - This parameter is case sensitive.
    type: str
    aliases: [ template_src ]
  template_uuid:
    description:
    - UUID of a template, an existing VM or a snapshot that should be used to create VM.
    - It is required if template name is not unique.
    type: str
  is_template:
    description:
    - Convert VM to template.
    type: bool
    default: no
  folder:
    description:
    - Destination folder for VM.
    - This parameter is case sensitive.
    - 'Example:'
    - '  folder: /folder1/folder2'
    type: str
  hardware:
    description:
    - Manage VM's hardware parameters. VM needs to be shut down to reconfigure these parameters.
    - 'Valid parameters are:'
    - ' - C(num_cpus) (integer): Number of CPUs.'
    - ' - C(num_cpu_cores_per_socket) (integer): Number of Cores Per Socket. C(num_cpus) has to be a multiple of C(num_cpu_cores_per_socket).'
    - ' - C(memory_mb) (integer): Amount of memory in MB.'
    type: dict
  disks:
    description:
    - A list of disks to add to VM.
    - All parameters are case sensitive.
    - Removing or detaching existing disks of VM is not supported.
    - 'Required parameters per entry:'
    - ' - C(size_[tb,gb,mb,kb,b]) (integer): Disk storage size in specified unit. VM needs to be shut down to reconfigure this parameter.'
    - 'Optional parameters per entry:'
    - ' - C(name) (string): Disk name. You can also use C(name_label) as an alias.'
    - ' - C(name_desc) (string): Disk description.'
    - ' - C(sr) (string): Storage Repository to create disk on. If not specified, will use default SR. Cannot be used for moving disk to other SR.'
    - ' - C(sr_uuid) (string): UUID of a SR to create disk on. Use if SR name is not unique.'
    type: list
    aliases: [ disk ]
  cdrom:
    description:
    - A CD-ROM configuration for the VM.
    - All parameters are case sensitive.
    - 'Valid parameters are:'
    - ' - C(type) (string): The type of CD-ROM, valid options are C(none) or C(iso). With C(none) the CD-ROM device will be present but empty.'
    - ' - C(iso_name) (string): The file name of an ISO image from one of the XenServer ISO Libraries (implies C(type: iso)).
          Required if C(type) is set to C(iso).'
    type: dict
  networks:
    description:
    - A list of networks (in the order of the NICs).
    - All parameters are case sensitive.
    - 'Required parameters per entry:'
    - ' - C(name) (string): Name of a XenServer network to attach the network interface to. You can also use C(name_label) as an alias.'
    - 'Optional parameters per entry (used for VM hardware):'
    - ' - C(mac) (string): Customize MAC address of the interface.'
    - 'Optional parameters per entry (used for OS customization):'
    - ' - C(type) (string): Type of IPv4 assignment, valid options are C(none), C(dhcp) or C(static). Value C(none) means whatever is default for OS.
          On some operating systems it could be DHCP configured (e.g. Windows) or unconfigured interface (e.g. Linux).'
    - ' - C(ip) (string): Static IPv4 address (implies C(type: static)). Can include prefix in format <IPv4 address>/<prefix> instead of using C(netmask).'
    - ' - C(netmask) (string): Static IPv4 netmask required for C(ip) if prefix is not specified.'
    - ' - C(gateway) (string): Static IPv4 gateway.'
    - ' - C(type6) (string): Type of IPv6 assignment, valid options are C(none), C(dhcp) or C(static). Value C(none) means whatever is default for OS.
          On some operating systems it could be DHCP configured (e.g. Windows) or unconfigured interface (e.g. Linux).'
    - ' - C(ip6) (string): Static IPv6 address (implies C(type6: static)) with prefix in format <IPv6 address>/<prefix>.'
    - ' - C(gateway6) (string): Static IPv6 gateway.'
    type: list
    aliases: [ network ]
  home_server:
    description:
    - Name of a XenServer host that will be a Home Server for the VM.
    - This parameter is case sensitive.
    type: str
  custom_params:
    description:
    - Define a list of custom VM params to set on VM.
    - Useful for advanced users familiar with managing VM params trough xe CLI.
    - A custom value object takes two fields C(key) and C(value) (see example below).
    type: list
  wait_for_ip_address:
    description:
    - Wait until XenServer detects an IP address for the VM. If C(state) is set to C(absent), this parameter is ignored.
    - This requires XenServer Tools to be preinstalled on the VM to work properly.
    type: bool
    default: no
  state_change_timeout:
    description:
    - 'By default, module will wait indefinitely for VM to accquire an IP address if C(wait_for_ip_address: yes).'
    - If this parameter is set to positive value, the module will instead wait specified number of seconds for the state change.
    - In case of timeout, module will generate an error message.
    type: int
    default: 0
  linked_clone:
    description:
    - Whether to create a Linked Clone from the template, existing VM or snapshot. If no, will create a full copy.
    - This is equivalent to C(Use storage-level fast disk clone) option in XenCenter.
    type: bool
    default: no
  force:
    description:
    - Ignore warnings and complete the actions.
    - This parameter is useful for removing VM in running state or reconfiguring VM params that require VM to be shut down.
    type: bool
    default: no
extends_documentation_fragment: xenserver.documentation
'''

EXAMPLES = r'''
- name: Create a VM from a template
  xenserver_guest:
    hostname: "{{ xenserver_hostname }}"
    username: "{{ xenserver_username }}"
    password: "{{ xenserver_password }}"
    validate_certs: no
    folder: /testvms
    name: testvm_2
    state: poweredon
    template: CentOS 7
    disks:
    - size_gb: 10
      sr: my_sr
    hardware:
      num_cpus: 6
      num_cpu_cores_per_socket: 3
      memory_mb: 512
    cdrom:
      type: iso
      iso_name: guest-tools.iso
    networks:
    - name: VM Network
      mac: aa:bb:dd:aa:00:14
    wait_for_ip_address: yes
  delegate_to: localhost
  register: deploy

- name: Create a VM template
  xenserver_guest:
    hostname: "{{ xenserver_hostname }}"
    username: "{{ xenserver_username }}"
    password: "{{ xenserver_password }}"
    validate_certs: no
    folder: /testvms
    name: testvm_6
    is_template: yes
    disk:
    - size_gb: 10
      sr: my_sr
    hardware:
      memory_mb: 512
      num_cpus: 1
  delegate_to: localhost
  register: deploy

- name: Rename a VM (requires the VM's UUID)
  xenserver_guest:
    hostname: "{{ xenserver_hostname }}"
    username: "{{ xenserver_username }}"
    password: "{{ xenserver_password }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    name: new_name
    state: present
  delegate_to: localhost

- name: Remove a VM by UUID
  xenserver_guest:
    hostname: "{{ xenserver_hostname }}"
    username: "{{ xenserver_username }}"
    password: "{{ xenserver_password }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    state: absent
  delegate_to: localhost

- name: Modify custom params (boot order)
  xenserver_guest:
    hostname: "{{ xenserver_hostname }}"
    username: "{{ xenserver_username }}"
    password: "{{ xenserver_password }}"
    name: testvm_8
    state: present
    custom_params:
    - key: HVM_boot_params
      value: { "order": "ndc" }
  delegate_to: localhost

- name: Customize network parameters
  xenserver_guest:
    hostname: "{{ xenserver_hostname }}"
    username: "{{ xenserver_username }}"
    password: "{{ xenserver_password }}"
    name: testvm_10
    networks:
    - name: VM Network
      ip: 192.168.1.100/24
      gateway: 192.168.1.1
    - type: dhcp
  delegate_to: localhost
'''

RETURN = r'''
instance:
    description: Metadata about the VM
    returned: always
    type: dict
    sample: {
        "cdrom": {
            "type": "none"
        },
        "customization_agent": "native",
        "disks": [
            {
                "name": "testvm_11-0",
                "name_desc": "",
                "os_device": "xvda",
                "size": 42949672960,
                "sr": "Local storage",
                "sr_uuid": "0af1245e-bdb0-ba33-1446-57a962ec4075",
                "vbd_userdevice": "0"
            },
            {
                "name": "testvm_11-1",
                "name_desc": "",
                "os_device": "xvdb",
                "size": 42949672960,
                "sr": "Local storage",
                "sr_uuid": "0af1245e-bdb0-ba33-1446-57a962ec4075",
                "vbd_userdevice": "1"
            }
        ],
        "domid": "56",
        "folder": "",
        "hardware": {
            "memory_mb": 8192,
            "num_cpu_cores_per_socket": 2,
            "num_cpus": 4
        },
        "home_server": "",
        "is_template": false,
        "name": "testvm_11",
        "name_desc": "",
        "networks": [
            {
                "gateway": "192.168.0.254",
                "gateway6": "fc00::fffe",
                "ip": "192.168.0.200",
                "ip6": [
                    "fe80:0000:0000:0000:e9cb:625a:32c5:c291",
                    "fc00:0000:0000:0000:0000:0000:0000:0001"
                ],
                "mac": "ba:91:3a:48:20:76",
                "mtu": "1500",
                "name": "Pool-wide network associated with eth1",
                "netmask": "255.255.255.128",
                "prefix": "25",
                "prefix6": "64",
                "vif_device": "0"
            }
        ],
        "other_config": {
            "base_template_name": "Windows Server 2016 (64-bit)",
            "import_task": "OpaqueRef:e43eb71c-45d6-5351-09ff-96e4fb7d0fa5",
            "install-methods": "cdrom",
            "instant": "true",
            "mac_seed": "f83e8d8a-cfdc-b105-b054-ef5cb416b77e"
        },
        "platform": {
            "acpi": "1",
            "apic": "true",
            "cores-per-socket": "2",
            "device_id": "0002",
            "hpet": "true",
            "nx": "true",
            "pae": "true",
            "timeoffset": "-25200",
            "vga": "std",
            "videoram": "8",
            "viridian": "true",
            "viridian_reference_tsc": "true",
            "viridian_time_ref_count": "true"
        },
        "state": "poweredon",
        "uuid": "e3c0b2d5-5f05-424e-479c-d3df8b3e7cda",
        "xenstore_data": {
            "vm-data": ""
        }
    }
changes:
    description: Detected or made changes to VM
    returned: always
    type: list
    sample: [
        {
            "hardware": [
                "num_cpus"
            ]
        },
        {
            "disks_changed": [
                [],
                [
                    "size"
                ]
            ]
        },
        {
            "disks_new": [
                {
                    "name": "new-disk",
                    "name_desc": "",
                    "position": 2,
                    "size_gb": "4",
                    "vbd_userdevice": "2"
                }
            ]
        },
        {
            "cdrom": [
                "type",
                "iso_name"
            ]
        },
        {
            "networks_changed": [
                [
                    "mac"
                ],
            ]
        },
        {
            "networks_new": [
                {
                    "name": "Pool-wide network associated with eth2",
                    "position": 1,
                    "vif_device": "1"
                }
            ]
        },
        "need_poweredoff"
    ]
'''

import re

HAS_XENAPI = False
try:
    import XenAPI
    HAS_XENAPI = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.network import is_mac
from ansible.module_utils import six
from ansible.module_utils.xenserver import (xenserver_common_argument_spec, XAPI, XenServerObject, get_object_ref,
                                            gather_vm_params, gather_vm_facts, set_vm_power_state, wait_for_vm_ip_address,
                                            is_valid_ip_addr, is_valid_ip_netmask, is_valid_ip_prefix,
                                            ip_prefix_to_netmask, ip_netmask_to_prefix,
                                            is_valid_ip6_addr, is_valid_ip6_prefix)


class XenServerVM(XenServerObject):
    """Class for managing XenServer VM.

    Attributes:
        vm_ref (str): XAPI reference to VM.
        vm_params (dict): A dictionary with VM parameters as returned
            by gather_vm_params() function.
    """

    def __init__(self, module):
        """Inits XenServerVM using module parameters.

        Args:
            module: Reference to Ansible module object.
        """
        super(XenServerVM, self).__init__(module)

        self.vm_ref = get_object_ref(self.module, self.module.params['name'], self.module.params['uuid'], obj_type="VM", fail=False, msg_prefix="VM search: ")
        self.gather_params()

    def exists(self):
        """Returns True if VM exists, else False."""
        return True if self.vm_ref is not None else False

    def gather_params(self):
        """Gathers all VM parameters available in XAPI database."""
        self.vm_params = gather_vm_params(self.module, self.vm_ref)

    def gather_facts(self):
        """Gathers and returns VM facts."""
        return gather_vm_facts(self.module, self.vm_params)

    def set_power_state(self, power_state):
        """Controls VM power state."""
        state_changed, current_state = set_vm_power_state(self.module, self.vm_ref, power_state, self.module.params['state_change_timeout'])

        # If state has changed, update vm_params.
        if state_changed:
            self.vm_params['power_state'] = current_state.capitalize()

        return state_changed

    def wait_for_ip_address(self):
        """Waits for VM to acquire an IP address."""
        self.vm_params['guest_metrics'] = wait_for_vm_ip_address(self.module, self.vm_ref, self.module.params['state_change_timeout'])

    def deploy(self):
        """Deploys new VM from template."""
        # Safety check.
        if self.exists():
            self.module.fail_json(msg="Called deploy on existing VM!")

        try:
            templ_ref = get_object_ref(self.module, self.module.params['template'], self.module.params['template_uuid'], obj_type="template", fail=True,
                                       msg_prefix="VM deploy: ")

            # Is this an existing running VM?
            if self.xapi_session.xenapi.VM.get_power_state(templ_ref).lower() != 'halted':
                self.module.fail_json(msg="VM deploy: running VM cannot be used as a template!")

            # Find a SR we can use for VM.copy(). We use SR of the first disk
            # if specified or default SR if not specified.
            disk_params_list = self.module.params['disks']

            sr_ref = None

            if disk_params_list:
                disk_params = disk_params_list[0]

                disk_sr_uuid = disk_params.get('sr_uuid')
                disk_sr = disk_params.get('sr')

                if disk_sr_uuid is not None or disk_sr is not None:
                    sr_ref = get_object_ref(self.module, disk_sr, disk_sr_uuid, obj_type="SR", fail=True,
                                            msg_prefix="VM deploy disks[0]: ")

            if not sr_ref:
                if self.default_sr_ref != "OpaqueRef:NULL":
                    sr_ref = self.default_sr_ref
                else:
                    self.module.fail_json(msg="VM deploy disks[0]: no default SR found! You must specify SR explicitly.")

            # VM name could be an empty string which is bad.
            if self.module.params['name'] is not None and not self.module.params['name']:
                self.module.fail_json(msg="VM deploy: VM name must not be an empty string!")

            # Support for Ansible check mode.
            if self.module.check_mode:
                return

            # Now we can instantiate VM. We use VM.clone for linked_clone and
            # VM.copy for non linked_clone.
            if self.module.params['linked_clone']:
                self.vm_ref = self.xapi_session.xenapi.VM.clone(templ_ref, self.module.params['name'])
            else:
                self.vm_ref = self.xapi_session.xenapi.VM.copy(templ_ref, self.module.params['name'], sr_ref)

            # Description is copied over from template so we reset it.
            self.xapi_session.xenapi.VM.set_name_description(self.vm_ref, "")

            # If template is one of built-in XenServer templates, we have to
            # do some additional steps.
            # Note: VM.get_is_default_template() is supported from XenServer 7.2
            #       onward so we use an alternative way.
            templ_other_config = self.xapi_session.xenapi.VM.get_other_config(templ_ref)

            if "default_template" in templ_other_config and templ_other_config['default_template']:
                # other_config of built-in XenServer templates have a key called
                # 'disks' with the following content:
                #   disks: <provision><disk bootable="true" device="0" size="10737418240" sr="" type="system"/></provision>
                # This value of other_data is copied to cloned or copied VM and
                # it prevents provisioning of VM because sr is not specified and
                # XAPI returns an error. To get around this, we remove the
                # 'disks' key and add disks to VM later ourselves.
                vm_other_config = self.xapi_session.xenapi.VM.get_other_config(self.vm_ref)

                if "disks" in vm_other_config:
                    del vm_other_config['disks']

                self.xapi_session.xenapi.VM.set_other_config(self.vm_ref, vm_other_config)

            # At this point we have VM ready for provisioning.
            self.xapi_session.xenapi.VM.provision(self.vm_ref)

            # After provisioning we can prepare vm_params for reconfigure().
            self.gather_params()

            # VM is almost ready. We just need to reconfigure it...
            self.reconfigure()

            # Power on VM if needed.
            if self.module.params['state'] == "poweredon":
                self.set_power_state("poweredon")

        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

    def reconfigure(self):
        """Reconfigures an existing VM.

        Returns:
            list: parameters that were reconfigured.
        """
        # Safety check.
        if not self.exists():
            self.module.fail_json(msg="Called reconfigure on non existing VM!")

        config_changes = self.get_changes()

        vm_power_state_save = self.vm_params['power_state'].lower()

        if "need_poweredoff" in config_changes and vm_power_state_save != 'halted' and not self.module.params['force']:
            self.module.fail_json(msg="VM reconfigure: VM has to be in powered off state to reconfigure but force was not specified!")

        # Support for Ansible check mode.
        if self.module.check_mode:
            return config_changes

        if "need_poweredoff" in config_changes and vm_power_state_save != 'halted' and self.module.params['force']:
            self.set_power_state("shutdownguest")

        try:
            for change in config_changes:
                if isinstance(change, six.string_types):
                    if change == "name":
                        self.xapi_session.xenapi.VM.set_name_label(self.vm_ref, self.module.params['name'])
                    elif change == "name_desc":
                        self.xapi_session.xenapi.VM.set_name_description(self.vm_ref, self.module.params['name_desc'])
                    elif change == "folder":
                        self.xapi_session.xenapi.VM.remove_from_other_config(self.vm_ref, 'folder')

                        if self.module.params['folder']:
                            self.xapi_session.xenapi.VM.add_to_other_config(self.vm_ref, 'folder', self.module.params['folder'])
                    elif change == "home_server":
                        if self.module.params['home_server']:
                            host_ref = self.xapi_session.xenapi.host.get_by_name_label(self.module.params['home_server'])[0]
                        else:
                            host_ref = "OpaqueRef:NULL"

                        self.xapi_session.xenapi.VM.set_affinity(self.vm_ref, host_ref)
                elif isinstance(change, dict):
                    if change.get('hardware'):
                        for hardware_change in change['hardware']:
                            if hardware_change == "num_cpus":
                                num_cpus = int(self.module.params['hardware']['num_cpus'])

                                if num_cpus < int(self.vm_params['VCPUs_at_startup']):
                                    self.xapi_session.xenapi.VM.set_VCPUs_at_startup(self.vm_ref, str(num_cpus))
                                    self.xapi_session.xenapi.VM.set_VCPUs_max(self.vm_ref, str(num_cpus))
                                else:
                                    self.xapi_session.xenapi.VM.set_VCPUs_max(self.vm_ref, str(num_cpus))
                                    self.xapi_session.xenapi.VM.set_VCPUs_at_startup(self.vm_ref, str(num_cpus))
                            elif hardware_change == "num_cpu_cores_per_socket":
                                self.xapi_session.xenapi.VM.remove_from_platform(self.vm_ref, 'cores-per-socket')
                                num_cpu_cores_per_socket = int(self.module.params['hardware']['num_cpu_cores_per_socket'])

                                if num_cpu_cores_per_socket > 1:
                                    self.xapi_session.xenapi.VM.add_to_platform(self.vm_ref, 'cores-per-socket', str(num_cpu_cores_per_socket))
                            elif hardware_change == "memory_mb":
                                memory_b = str(int(self.module.params['hardware']['memory_mb']) * 1048576)
                                vm_memory_static_min_b = str(min(int(memory_b), int(self.vm_params['memory_static_min'])))

                                self.xapi_session.xenapi.VM.set_memory_limits(self.vm_ref, vm_memory_static_min_b, memory_b, memory_b, memory_b)
                    elif change.get('disks_changed'):
                        vm_disk_params_list = [disk_params for disk_params in self.vm_params['VBDs'] if disk_params['type'] == "Disk"]
                        position = 0

                        for disk_change_list in change['disks_changed']:
                            for disk_change in disk_change_list:
                                vdi_ref = self.xapi_session.xenapi.VDI.get_by_uuid(vm_disk_params_list[position]['VDI']['uuid'])

                                if disk_change == "name":
                                    self.xapi_session.xenapi.VDI.set_name_label(vdi_ref, self.module.params['disks'][position]['name'])
                                elif disk_change == "name_desc":
                                    self.xapi_session.xenapi.VDI.set_name_description(vdi_ref, self.module.params['disks'][position]['name_desc'])
                                elif disk_change == "size":
                                    self.xapi_session.xenapi.VDI.resize(vdi_ref, str(self.get_normalized_disk_size(self.module.params['disks'][position],
                                                                                                                   "VM reconfigure disks[%s]: " % position)))

                            position += 1
                    elif change.get('disks_new'):
                        for position, disk_userdevice in change['disks_new']:
                            disk_params = self.module.params['disks'][position]

                            disk_name = disk_params['name'] if disk_params.get('name') else "%s-%s" % (self.vm_params['name_label'], position)
                            disk_name_desc = disk_params['name_desc'] if disk_params.get('name_desc') else ""

                            if disk_params.get('sr_uuid'):
                                sr_ref = self.xapi_session.xenapi.SR.get_by_uuid(disk_params['sr_uuid'])
                            elif disk_params.get('sr'):
                                sr_ref = self.xapi_session.xenapi.SR.get_by_name_label(disk_params['sr'])[0]
                            else:
                                sr_ref = self.default_sr_ref

                            disk_size = str(self.get_normalized_disk_size(self.module.params['disks'][position], "VM reconfigure disks[%s]: " % position))

                            new_disk_vdi = {
                                "name_label": disk_name,
                                "name_description": disk_name_desc,
                                "SR": sr_ref,
                                "virtual_size": disk_size,
                                "type": "user",
                                "sharable": False,
                                "read_only": False,
                                "other_config": {},
                            }

                            new_disk_vbd = {
                                "VM": self.vm_ref,
                                "VDI": None,
                                "userdevice": disk_userdevice,
                                "bootable": False,
                                "mode": "RW",
                                "type": "Disk",
                                "empty": False,
                                "other_config": {},
                                "qos_algorithm_type": "",
                                "qos_algorithm_params": {},
                            }

                            new_disk_vbd['VDI'] = self.xapi_session.xenapi.VDI.create(new_disk_vdi)
                            vbd_ref_new = self.xapi_session.xenapi.VBD.create(new_disk_vbd)

                            if self.vm_params['power_state'].lower() == "running":
                                self.xapi_session.xenapi.VBD.plug(vbd_ref_new)

                    elif change.get('cdrom'):
                        vm_cdrom_params_list = [cdrom_params for cdrom_params in self.vm_params['VBDs'] if cdrom_params['type'] == "CD"]

                        # If there is no CD present, we have to create one.
                        if not vm_cdrom_params_list:
                            # We will try to place cdrom at userdevice position
                            # 3 (which is default) if it is not already occupied
                            # else we will place it at first allowed position.
                            cdrom_userdevices_allowed = self.xapi_session.xenapi.VM.get_allowed_VBD_devices(self.vm_ref)

                            if "3" in cdrom_userdevices_allowed:
                                cdrom_userdevice = "3"
                            else:
                                cdrom_userdevice = cdrom_userdevices_allowed[0]

                            cdrom_vbd = {
                                "VM": self.vm_ref,
                                "VDI": "OpaqueRef:NULL",
                                "userdevice": cdrom_userdevice,
                                "bootable": False,
                                "mode": "RO",
                                "type": "CD",
                                "empty": True,
                                "other_config": {},
                                "qos_algorithm_type": "",
                                "qos_algorithm_params": {},
                            }

                            cdrom_vbd_ref = self.xapi_session.xenapi.VBD.create(cdrom_vbd)
                        else:
                            cdrom_vbd_ref = self.xapi_session.xenapi.VBD.get_by_uuid(vm_cdrom_params_list[0]['uuid'])

                        cdrom_is_empty = self.xapi_session.xenapi.VBD.get_empty(cdrom_vbd_ref)

                        for cdrom_change in change['cdrom']:
                            if cdrom_change == "type":
                                cdrom_type = self.module.params['cdrom']['type']

                                if cdrom_type == "none" and not cdrom_is_empty:
                                    self.xapi_session.xenapi.VBD.eject(cdrom_vbd_ref)
                                elif cdrom_type == "host":
                                    # Unimplemented!
                                    pass

                            elif cdrom_change == "iso_name":
                                if not cdrom_is_empty:
                                    self.xapi_session.xenapi.VBD.eject(cdrom_vbd_ref)

                                cdrom_vdi_ref = self.xapi_session.xenapi.VDI.get_by_name_label(self.module.params['cdrom']['iso_name'])[0]
                                self.xapi_session.xenapi.VBD.insert(cdrom_vbd_ref, cdrom_vdi_ref)
                    elif change.get('networks_changed'):
                        position = 0

                        for network_change_list in change['networks_changed']:
                            if network_change_list:
                                vm_vif_params = self.vm_params['VIFs'][position]
                                network_params = self.module.params['networks'][position]

                                vif_ref = self.xapi_session.xenapi.VIF.get_by_uuid(vm_vif_params['uuid'])
                                network_ref = self.xapi_session.xenapi.network.get_by_uuid(vm_vif_params['network']['uuid'])

                                vif_recreated = False

                                if "name" in network_change_list or "mac" in network_change_list:
                                    # To change network or MAC, we destroy old
                                    # VIF and then create a new one with changed
                                    # parameters. That's how XenCenter does it.

                                    # Copy all old parameters to new VIF record.
                                    vif = {
                                        "device": vm_vif_params['device'],
                                        "network": network_ref,
                                        "VM": vm_vif_params['VM'],
                                        "MAC": vm_vif_params['MAC'],
                                        "MTU": vm_vif_params['MTU'],
                                        "other_config": vm_vif_params['other_config'],
                                        "qos_algorithm_type": vm_vif_params['qos_algorithm_type'],
                                        "qos_algorithm_params": vm_vif_params['qos_algorithm_params'],
                                        "locking_mode": vm_vif_params['locking_mode'],
                                        "ipv4_allowed": vm_vif_params['ipv4_allowed'],
                                        "ipv6_allowed": vm_vif_params['ipv6_allowed'],
                                    }

                                    if "name" in network_change_list:
                                        network_ref_new = self.xapi_session.xenapi.network.get_by_name_label(network_params['name'])[0]
                                        vif['network'] = network_ref_new
                                        vif['MTU'] = self.xapi_session.xenapi.network.get_MTU(network_ref_new)

                                    if "mac" in network_change_list:
                                        vif['MAC'] = network_params['mac'].lower()

                                    if self.vm_params['power_state'].lower() == "running":
                                        self.xapi_session.xenapi.VIF.unplug(vif_ref)

                                    self.xapi_session.xenapi.VIF.destroy(vif_ref)
                                    vif_ref_new = self.xapi_session.xenapi.VIF.create(vif)

                                    if self.vm_params['power_state'].lower() == "running":
                                        self.xapi_session.xenapi.VIF.plug(vif_ref_new)

                                    vif_ref = vif_ref_new
                                    vif_recreated = True

                                if self.vm_params['customization_agent'] == "native":
                                    vif_reconfigure_needed = False

                                    if "type" in network_change_list:
                                        network_type = network_params['type'].capitalize()
                                        vif_reconfigure_needed = True
                                    else:
                                        network_type = vm_vif_params['ipv4_configuration_mode']

                                    if "ip" in network_change_list:
                                        network_ip = network_params['ip']
                                        vif_reconfigure_needed = True
                                    elif vm_vif_params['ipv4_addresses']:
                                        network_ip = vm_vif_params['ipv4_addresses'][0].split('/')[0]
                                    else:
                                        network_ip = ""

                                    if "prefix" in network_change_list:
                                        network_prefix = "/%s" % network_params['prefix']
                                        vif_reconfigure_needed = True
                                    elif vm_vif_params['ipv4_addresses'] and vm_vif_params['ipv4_addresses'][0]:
                                        network_prefix = "/%s" % vm_vif_params['ipv4_addresses'][0].split('/')[1]
                                    else:
                                        network_prefix = ""

                                    if "gateway" in network_change_list:
                                        network_gateway = network_params['gateway']
                                        vif_reconfigure_needed = True
                                    else:
                                        network_gateway = vm_vif_params['ipv4_gateway']

                                    if vif_recreated or vif_reconfigure_needed:
                                        self.xapi_session.xenapi.VIF.configure_ipv4(vif_ref, network_type,
                                                                                    "%s%s" % (network_ip, network_prefix), network_gateway)

                                    vif_reconfigure_needed = False

                                    if "type6" in network_change_list:
                                        network_type6 = network_params['type6'].capitalize()
                                        vif_reconfigure_needed = True
                                    else:
                                        network_type6 = vm_vif_params['ipv6_configuration_mode']

                                    if "ip6" in network_change_list:
                                        network_ip6 = network_params['ip6']
                                        vif_reconfigure_needed = True
                                    elif vm_vif_params['ipv6_addresses']:
                                        network_ip6 = vm_vif_params['ipv6_addresses'][0].split('/')[0]
                                    else:
                                        network_ip6 = ""

                                    if "prefix6" in network_change_list:
                                        network_prefix6 = "/%s" % network_params['prefix6']
                                        vif_reconfigure_needed = True
                                    elif vm_vif_params['ipv6_addresses'] and vm_vif_params['ipv6_addresses'][0]:
                                        network_prefix6 = "/%s" % vm_vif_params['ipv6_addresses'][0].split('/')[1]
                                    else:
                                        network_prefix6 = ""

                                    if "gateway6" in network_change_list:
                                        network_gateway6 = network_params['gateway6']
                                        vif_reconfigure_needed = True
                                    else:
                                        network_gateway6 = vm_vif_params['ipv6_gateway']

                                    if vif_recreated or vif_reconfigure_needed:
                                        self.xapi_session.xenapi.VIF.configure_ipv6(vif_ref, network_type6,
                                                                                    "%s%s" % (network_ip6, network_prefix6), network_gateway6)

                                elif self.vm_params['customization_agent'] == "custom":
                                    vif_device = vm_vif_params['device']

                                    # A user could have manually changed network
                                    # or mac e.g. trough XenCenter and then also
                                    # make those changes in playbook manually.
                                    # In that case, module will not detect any
                                    # changes and info in xenstore_data will
                                    # become stale. For that reason we always
                                    # update name and mac in xenstore_data.

                                    # Since we handle name and mac differently,
                                    # we have to remove them from
                                    # network_change_list.
                                    network_change_list_tmp = [net_chg for net_chg in network_change_list if net_chg not in ['name', 'mac']]

                                    for network_change in network_change_list_tmp + ['name', 'mac']:
                                        self.xapi_session.xenapi.VM.remove_from_xenstore_data(self.vm_ref,
                                                                                              "vm-data/networks/%s/%s" % (vif_device, network_change))

                                    if network_params.get('name'):
                                        network_name = network_params['name']
                                    else:
                                        network_name = vm_vif_params['network']['name_label']

                                    self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref,
                                                                                     "vm-data/networks/%s/%s" % (vif_device, 'name'), network_name)

                                    if network_params.get('mac'):
                                        network_mac = network_params['mac'].lower()
                                    else:
                                        network_mac = vm_vif_params['MAC'].lower()

                                    self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref,
                                                                                     "vm-data/networks/%s/%s" % (vif_device, 'mac'), network_mac)

                                    for network_change in network_change_list_tmp:
                                        self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref,
                                                                                         "vm-data/networks/%s/%s" % (vif_device, network_change),
                                                                                         network_params[network_change])

                            position += 1
                    elif change.get('networks_new'):
                        for position, vif_device in change['networks_new']:
                            network_params = self.module.params['networks'][position]

                            network_ref = self.xapi_session.xenapi.network.get_by_name_label(network_params['name'])[0]

                            network_name = network_params['name']
                            network_mac = network_params['mac'] if network_params.get('mac') else ""
                            network_type = network_params.get('type')
                            network_ip = network_params['ip'] if network_params.get('ip') else ""
                            network_prefix = network_params['prefix'] if network_params.get('prefix') else ""
                            network_netmask = network_params['netmask'] if network_params.get('netmask') else ""
                            network_gateway = network_params['gateway'] if network_params.get('gateway') else ""
                            network_type6 = network_params.get('type6')
                            network_ip6 = network_params['ip6'] if network_params.get('ip6') else ""
                            network_prefix6 = network_params['prefix6'] if network_params.get('prefix6') else ""
                            network_gateway6 = network_params['gateway6'] if network_params.get('gateway6') else ""

                            vif = {
                                "device": vif_device,
                                "network": network_ref,
                                "VM": self.vm_ref,
                                "MAC": network_mac,
                                "MTU": self.xapi_session.xenapi.network.get_MTU(network_ref),
                                "other_config": {},
                                "qos_algorithm_type": "",
                                "qos_algorithm_params": {},
                            }

                            vif_ref_new = self.xapi_session.xenapi.VIF.create(vif)

                            if self.vm_params['power_state'].lower() == "running":
                                self.xapi_session.xenapi.VIF.plug(vif_ref_new)

                            if self.vm_params['customization_agent'] == "native":
                                if network_type and network_type == "static":
                                    self.xapi_session.xenapi.VIF.configure_ipv4(vif_ref_new, "Static",
                                                                                "%s/%s" % (network_ip, network_prefix), network_gateway)

                                if network_type6 and network_type6 == "static":
                                    self.xapi_session.xenapi.VIF.configure_ipv6(vif_ref_new, "Static",
                                                                                "%s/%s" % (network_ip6, network_prefix6), network_gateway6)
                            elif self.vm_params['customization_agent'] == "custom":
                                # We first have to remove any existing data
                                # from xenstore_data because there could be
                                # some old leftover data from some interface
                                # that once occupied same device location as
                                # our new interface.
                                for network_param in ['name', 'mac', 'type', 'ip', 'prefix', 'netmask', 'gateway', 'type6', 'ip6', 'prefix6', 'gateway6']:
                                    self.xapi_session.xenapi.VM.remove_from_xenstore_data(self.vm_ref, "vm-data/networks/%s/%s" % (vif_device, network_param))

                                self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref, "vm-data/networks/%s/name" % vif_device, network_name)

                                # We get MAC from VIF itself instead of
                                # networks.mac because it could be
                                # autogenerated.
                                vm_vif_mac = self.xapi_session.xenapi.VIF.get_MAC(vif_ref_new)
                                self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref, "vm-data/networks/%s/mac" % vif_device, vm_vif_mac)

                                if network_type:
                                    self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref, "vm-data/networks/%s/type" % vif_device, network_type)

                                    if network_type == "static":
                                        self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref,
                                                                                         "vm-data/networks/%s/ip" % vif_device, network_ip)
                                        self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref,
                                                                                         "vm-data/networks/%s/prefix" % vif_device, network_prefix)
                                        self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref,
                                                                                         "vm-data/networks/%s/netmask" % vif_device, network_netmask)
                                        self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref,
                                                                                         "vm-data/networks/%s/gateway" % vif_device, network_gateway)

                                if network_type6:
                                    self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref, "vm-data/networks/%s/type6" % vif_device, network_type6)

                                    if network_type6 == "static":
                                        self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref,
                                                                                         "vm-data/networks/%s/ip6" % vif_device, network_ip6)
                                        self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref,
                                                                                         "vm-data/networks/%s/prefix6" % vif_device, network_prefix6)
                                        self.xapi_session.xenapi.VM.add_to_xenstore_data(self.vm_ref,
                                                                                         "vm-data/networks/%s/gateway6" % vif_device, network_gateway6)

                    elif change.get('custom_params'):
                        for position in change['custom_params']:
                            custom_param_key = self.module.params['custom_params'][position]['key']
                            custom_param_value = self.module.params['custom_params'][position]['value']
                            self.xapi_session.xenapi_request("VM.set_%s" % custom_param_key, (self.vm_ref, custom_param_value))

            if self.module.params['is_template']:
                self.xapi_session.xenapi.VM.set_is_a_template(self.vm_ref, True)
            elif "need_poweredoff" in config_changes and self.module.params['force'] and vm_power_state_save != 'halted':
                self.set_power_state("poweredon")

            # Gather new params after reconfiguration.
            self.gather_params()

        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

        return config_changes

    def destroy(self):
        """Removes an existing VM with associated disks"""
        # Safety check.
        if not self.exists():
            self.module.fail_json(msg="Called destroy on non existing VM!")

        if self.vm_params['power_state'].lower() != 'halted' and not self.module.params['force']:
            self.module.fail_json(msg="VM destroy: VM has to be in powered off state to destroy but force was not specified!")

        # Support for Ansible check mode.
        if self.module.check_mode:
            return

        # Make sure that VM is poweredoff before we can destroy it.
        self.set_power_state("poweredoff")

        try:
            # Destroy VM!
            self.xapi_session.xenapi.VM.destroy(self.vm_ref)

            vm_disk_params_list = [disk_params for disk_params in self.vm_params['VBDs'] if disk_params['type'] == "Disk"]

            # Destroy all VDIs associated with VM!
            for vm_disk_params in vm_disk_params_list:
                vdi_ref = self.xapi_session.xenapi.VDI.get_by_uuid(vm_disk_params['VDI']['uuid'])

                self.xapi_session.xenapi.VDI.destroy(vdi_ref)

        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

    def get_changes(self):
        """Finds VM parameters that differ from specified ones.

        This method builds a dictionary with hierarchy of VM parameters
        that differ from those specified in module parameters.

        Returns:
            list: VM parameters that differ from those specified in
            module parameters.
        """
        # Safety check.
        if not self.exists():
            self.module.fail_json(msg="Called get_changes on non existing VM!")

        need_poweredoff = False

        if self.module.params['is_template']:
            need_poweredoff = True

        try:
            # This VM could be a template or a snapshot. In that case we fail
            # because we can't reconfigure them or it would just be too
            # dangerous.
            if self.vm_params['is_a_template'] and not self.vm_params['is_a_snapshot']:
                self.module.fail_json(msg="VM check: targeted VM is a template! Template reconfiguration is not supported.")

            if self.vm_params['is_a_snapshot']:
                self.module.fail_json(msg="VM check: targeted VM is a snapshot! Snapshot reconfiguration is not supported.")

            # Let's build a list of parameters that changed.
            config_changes = []

            # Name could only differ if we found an existing VM by uuid.
            if self.module.params['name'] is not None and self.module.params['name'] != self.vm_params['name_label']:
                if self.module.params['name']:
                    config_changes.append('name')
                else:
                    self.module.fail_json(msg="VM check name: VM name cannot be an empty string!")

            if self.module.params['name_desc'] is not None and self.module.params['name_desc'] != self.vm_params['name_description']:
                config_changes.append('name_desc')

            # Folder parameter is found in other_config.
            vm_other_config = self.vm_params['other_config']
            vm_folder = vm_other_config.get('folder', '')

            if self.module.params['folder'] is not None and self.module.params['folder'] != vm_folder:
                config_changes.append('folder')

            if self.module.params['home_server'] is not None:
                if (self.module.params['home_server'] and
                        (not self.vm_params['affinity'] or self.module.params['home_server'] != self.vm_params['affinity']['name_label'])):

                    # Check existance only. Ignore return value.
                    get_object_ref(self.module, self.module.params['home_server'], uuid=None, obj_type="home server", fail=True,
                                   msg_prefix="VM check home_server: ")

                    config_changes.append('home_server')
                elif not self.module.params['home_server'] and self.vm_params['affinity']:
                    config_changes.append('home_server')

            config_changes_hardware = []

            if self.module.params['hardware']:
                num_cpus = self.module.params['hardware'].get('num_cpus')

                if num_cpus is not None:
                    # Kept for compatibility with older Ansible versions that
                    # do not support subargument specs.
                    try:
                        num_cpus = int(num_cpus)
                    except ValueError as e:
                        self.module.fail_json(msg="VM check hardware.num_cpus: parameter should be an integer value!")

                    if num_cpus < 1:
                        self.module.fail_json(msg="VM check hardware.num_cpus: parameter should be greater than zero!")

                    # We can use VCPUs_at_startup or VCPUs_max parameter. I'd
                    # say the former is the way to go but this needs
                    # confirmation and testing.
                    if num_cpus != int(self.vm_params['VCPUs_at_startup']):
                        config_changes_hardware.append('num_cpus')
                        # For now, we don't support hotpluging so VM has to be in
                        # poweredoff state to reconfigure.
                        need_poweredoff = True

                num_cpu_cores_per_socket = self.module.params['hardware'].get('num_cpu_cores_per_socket')

                if num_cpu_cores_per_socket is not None:
                    # Kept for compatibility with older Ansible versions that
                    # do not support subargument specs.
                    try:
                        num_cpu_cores_per_socket = int(num_cpu_cores_per_socket)
                    except ValueError as e:
                        self.module.fail_json(msg="VM check hardware.num_cpu_cores_per_socket: parameter should be an integer value!")

                    if num_cpu_cores_per_socket < 1:
                        self.module.fail_json(msg="VM check hardware.num_cpu_cores_per_socket: parameter should be greater than zero!")

                    if num_cpus and num_cpus % num_cpu_cores_per_socket != 0:
                        self.module.fail_json(msg="VM check hardware.num_cpus: parameter should be a multiple of hardware.num_cpu_cores_per_socket!")

                    vm_platform = self.vm_params['platform']
                    vm_cores_per_socket = int(vm_platform.get('cores-per-socket', 1))

                    if num_cpu_cores_per_socket != vm_cores_per_socket:
                        config_changes_hardware.append('num_cpu_cores_per_socket')
                        # For now, we don't support hotpluging so VM has to be
                        # in poweredoff state to reconfigure.
                        need_poweredoff = True

                memory_mb = self.module.params['hardware'].get('memory_mb')

                if memory_mb is not None:
                    # Kept for compatibility with older Ansible versions that
                    # do not support subargument specs.
                    try:
                        memory_mb = int(memory_mb)
                    except ValueError as e:
                        self.module.fail_json(msg="VM check hardware.memory_mb: parameter should be an integer value!")

                    if memory_mb < 1:
                        self.module.fail_json(msg="VM check hardware.memory_mb: parameter should be greater than zero!")

                    # There are multiple memory parameters:
                    #     - memory_dynamic_max
                    #     - memory_dynamic_min
                    #     - memory_static_max
                    #     - memory_static_min
                    #     - memory_target
                    #
                    # memory_target seems like a good candidate but it returns 0 for
                    # halted VMs so we can't use it.
                    #
                    # I decided to use memory_dynamic_max and memory_static_max
                    # and use whichever is larger. This strategy needs validation
                    # and testing.
                    #
                    # XenServer stores memory size in bytes so we need to divide
                    # it by 1024*1024 = 1048576.
                    if memory_mb != int(max(int(self.vm_params['memory_dynamic_max']), int(self.vm_params['memory_static_max'])) / 1048576):
                        config_changes_hardware.append('memory_mb')
                        # For now, we don't support hotpluging so VM has to be in
                        # poweredoff state to reconfigure.
                        need_poweredoff = True

            if config_changes_hardware:
                config_changes.append({"hardware": config_changes_hardware})

            config_changes_disks = []
            config_new_disks = []

            # Find allowed userdevices.
            vbd_userdevices_allowed = self.xapi_session.xenapi.VM.get_allowed_VBD_devices(self.vm_ref)

            if self.module.params['disks']:
                # Get the list of all disk. Filter out any CDs found.
                vm_disk_params_list = [disk_params for disk_params in self.vm_params['VBDs'] if disk_params['type'] == "Disk"]

                # Number of disks defined in module params have to be same or
                # higher than a number of existing disks attached to the VM.
                # We don't support removal or detachment of disks.
                if len(self.module.params['disks']) < len(vm_disk_params_list):
                    self.module.fail_json(msg="VM check disks: provided disks configuration has less disks than the target VM (%d < %d)!" %
                                          (len(self.module.params['disks']), len(vm_disk_params_list)))

                # Find the highest disk occupied userdevice.
                if not vm_disk_params_list:
                    vm_disk_userdevice_highest = "-1"
                else:
                    vm_disk_userdevice_highest = vm_disk_params_list[-1]['userdevice']

                for position in range(len(self.module.params['disks'])):
                    if position < len(vm_disk_params_list):
                        vm_disk_params = vm_disk_params_list[position]
                    else:
                        vm_disk_params = None

                    disk_params = self.module.params['disks'][position]

                    disk_size = self.get_normalized_disk_size(self.module.params['disks'][position], "VM check disks[%s]: " % position)

                    disk_name = disk_params.get('name')

                    if disk_name is not None and not disk_name:
                        self.module.fail_json(msg="VM check disks[%s]: disk name cannot be an empty string!" % position)

                    # If this is an existing disk.
                    if vm_disk_params and vm_disk_params['VDI']:
                        disk_changes = []

                        if disk_name and disk_name != vm_disk_params['VDI']['name_label']:
                            disk_changes.append('name')

                        disk_name_desc = disk_params.get('name_desc')

                        if disk_name_desc is not None and disk_name_desc != vm_disk_params['VDI']['name_description']:
                            disk_changes.append('name_desc')

                        if disk_size:
                            if disk_size > int(vm_disk_params['VDI']['virtual_size']):
                                disk_changes.append('size')
                                need_poweredoff = True
                            elif disk_size < int(vm_disk_params['VDI']['virtual_size']):
                                self.module.fail_json(msg="VM check disks[%s]: disk size is smaller than existing (%d bytes < %s bytes). "
                                                      "Reducing disk size is not allowed!" % (position, disk_size, vm_disk_params['VDI']['virtual_size']))

                        config_changes_disks.append(disk_changes)
                    # If this is a new disk.
                    else:
                        if not disk_size:
                            self.module.fail_json(msg="VM check disks[%s]: no valid disk size specification found!" % position)

                        disk_sr_uuid = disk_params.get('sr_uuid')
                        disk_sr = disk_params.get('sr')

                        if disk_sr_uuid is not None or disk_sr is not None:
                            # Check existance only. Ignore return value.
                            get_object_ref(self.module, disk_sr, disk_sr_uuid, obj_type="SR", fail=True,
                                           msg_prefix="VM check disks[%s]: " % position)
                        elif self.default_sr_ref == 'OpaqueRef:NULL':
                            self.module.fail_json(msg="VM check disks[%s]: no default SR found! You must specify SR explicitly." % position)

                        if not vbd_userdevices_allowed:
                            self.module.fail_json(msg="VM check disks[%s]: maximum number of devices reached!" % position)

                        disk_userdevice = None

                        # We need to place a new disk right above the highest
                        # placed existing disk to maintain relative disk
                        # positions pairable with disk specifications in
                        # module params. That place must not be occupied by
                        # some other device like CD-ROM.
                        for userdevice in vbd_userdevices_allowed:
                            if int(userdevice) > int(vm_disk_userdevice_highest):
                                disk_userdevice = userdevice
                                vbd_userdevices_allowed.remove(userdevice)
                                vm_disk_userdevice_highest = userdevice
                                break

                        # If no place was found.
                        if disk_userdevice is None:
                            # Highest occupied place could be a CD-ROM device
                            # so we have to include all devices regardless of
                            # type when calculating out-of-bound position.
                            disk_userdevice = str(int(self.vm_params['VBDs'][-1]['userdevice']) + 1)
                            self.module.fail_json(msg="VM check disks[%s]: new disk position %s is out of bounds!" % (position, disk_userdevice))

                        # For new disks we only track their position.
                        config_new_disks.append((position, disk_userdevice))

            # We should append config_changes_disks to config_changes only
            # if there is at least one changed disk, else skip.
            for disk_change in config_changes_disks:
                if disk_change:
                    config_changes.append({"disks_changed": config_changes_disks})
                    break

            if config_new_disks:
                config_changes.append({"disks_new": config_new_disks})

            config_changes_cdrom = []

            if self.module.params['cdrom']:
                # Get the list of all CD-ROMs. Filter out any regular disks
                # found. If we found no existing CD-ROM, we will create it
                # later else take the first one found.
                vm_cdrom_params_list = [cdrom_params for cdrom_params in self.vm_params['VBDs'] if cdrom_params['type'] == "CD"]

                # If no existing CD-ROM is found, we will need to add one.
                # We need to check if there is any userdevice allowed.
                if not vm_cdrom_params_list and not vbd_userdevices_allowed:
                    self.module.fail_json(msg="VM check cdrom: maximum number of devices reached!")

                cdrom_type = self.module.params['cdrom'].get('type')
                cdrom_iso_name = self.module.params['cdrom'].get('iso_name')

                # If cdrom.iso_name is specified but cdrom.type is not,
                # then set cdrom.type to 'iso', unless cdrom.iso_name is
                # an empty string, in that case set cdrom.type to 'none'.
                if not cdrom_type:
                    if cdrom_iso_name:
                        cdrom_type = "iso"
                    elif cdrom_iso_name is not None:
                        cdrom_type = "none"

                    self.module.params['cdrom']['type'] = cdrom_type

                # If type changed.
                if cdrom_type and (not vm_cdrom_params_list or cdrom_type != self.get_cdrom_type(vm_cdrom_params_list[0])):
                    config_changes_cdrom.append('type')

                if cdrom_type == "iso":
                    # Check if ISO exists.
                    # Check existance only. Ignore return value.
                    get_object_ref(self.module, cdrom_iso_name, uuid=None, obj_type="ISO image", fail=True,
                                   msg_prefix="VM check cdrom.iso_name: ")

                    # Is ISO image changed?
                    if (cdrom_iso_name and
                            (not vm_cdrom_params_list or
                             not vm_cdrom_params_list[0]['VDI'] or
                             cdrom_iso_name != vm_cdrom_params_list[0]['VDI']['name_label'])):
                        config_changes_cdrom.append('iso_name')

            if config_changes_cdrom:
                config_changes.append({"cdrom": config_changes_cdrom})

            config_changes_networks = []
            config_new_networks = []

            # Find allowed devices.
            vif_devices_allowed = self.xapi_session.xenapi.VM.get_allowed_VIF_devices(self.vm_ref)

            if self.module.params['networks']:
                # Number of VIFs defined in module params have to be same or
                # higher than a number of existing VIFs attached to the VM.
                # We don't support removal of VIFs.
                if len(self.module.params['networks']) < len(self.vm_params['VIFs']):
                    self.module.fail_json(msg="VM check networks: provided networks configuration has less interfaces than the target VM (%d < %d)!" %
                                          (len(self.module.params['networks']), len(self.vm_params['VIFs'])))

                # Find the highest occupied device.
                if not self.vm_params['VIFs']:
                    vif_device_highest = "-1"
                else:
                    vif_device_highest = self.vm_params['VIFs'][-1]['device']

                for position in range(len(self.module.params['networks'])):
                    if position < len(self.vm_params['VIFs']):
                        vm_vif_params = self.vm_params['VIFs'][position]
                    else:
                        vm_vif_params = None

                    network_params = self.module.params['networks'][position]

                    network_name = network_params.get('name')

                    if network_name is not None and not network_name:
                        self.module.fail_json(msg="VM check networks[%s]: network name cannot be an empty string!" % position)

                    if network_name:
                        # Check existance only. Ignore return value.
                        get_object_ref(self.module, network_name, uuid=None, obj_type="network", fail=True,
                                       msg_prefix="VM check networks[%s]: " % position)

                    network_mac = network_params.get('mac')

                    if network_mac is not None:
                        network_mac = network_mac.lower()

                        if not is_mac(network_mac):
                            self.module.fail_json(msg="VM check networks[%s]: specified MAC address '%s' is not valid!" % (position, network_mac))

                    # IPv4 reconfiguration.
                    network_type = network_params.get('type')
                    network_ip = network_params.get('ip')
                    network_netmask = network_params.get('netmask')
                    network_prefix = None

                    # If networks.ip is specified and networks.type is not,
                    # then set networks.type to 'static'.
                    if not network_type and network_ip:
                        network_type = "static"

                    # XenServer natively supports only 'none' and 'static'
                    # type with 'none' being the same as 'dhcp'.
                    if self.vm_params['customization_agent'] == "native" and network_type and network_type == "dhcp":
                        network_type = "none"

                    if network_type and network_type == "static":
                        if network_ip is not None:
                            network_ip_split = network_ip.split('/')
                            network_ip = network_ip_split[0]

                            if network_ip and not is_valid_ip_addr(network_ip):
                                self.module.fail_json(msg="VM check networks[%s]: specified IPv4 address '%s' is not valid!" % (position, network_ip))

                            if len(network_ip_split) > 1:
                                network_prefix = network_ip_split[1]

                                if not is_valid_ip_prefix(network_prefix):
                                    self.module.fail_json(msg="VM check networks[%s]: specified IPv4 prefix '%s' is not valid!" % (position, network_prefix))

                        if network_netmask is not None:
                            if not is_valid_ip_netmask(network_netmask):
                                self.module.fail_json(msg="VM check networks[%s]: specified IPv4 netmask '%s' is not valid!" % (position, network_netmask))

                            network_prefix = ip_netmask_to_prefix(network_netmask, skip_check=True)
                        elif network_prefix is not None:
                            network_netmask = ip_prefix_to_netmask(network_prefix, skip_check=True)

                    # If any parameter is overridden at this point, update it.
                    if network_type:
                        network_params['type'] = network_type

                    if network_ip:
                        network_params['ip'] = network_ip

                    if network_netmask:
                        network_params['netmask'] = network_netmask

                    if network_prefix:
                        network_params['prefix'] = network_prefix

                    network_gateway = network_params.get('gateway')

                    # Gateway can be an empty string (when removing gateway
                    # configuration) but if it is not, it should be validated.
                    if network_gateway and not is_valid_ip_addr(network_gateway):
                        self.module.fail_json(msg="VM check networks[%s]: specified IPv4 gateway '%s' is not valid!" % (position, network_gateway))

                    # IPv6 reconfiguration.
                    network_type6 = network_params.get('type6')
                    network_ip6 = network_params.get('ip6')
                    network_prefix6 = None

                    # If networks.ip6 is specified and networks.type6 is not,
                    # then set networks.type6 to 'static'.
                    if not network_type6 and network_ip6:
                        network_type6 = "static"

                    # XenServer natively supports only 'none' and 'static'
                    # type with 'none' being the same as 'dhcp'.
                    if self.vm_params['customization_agent'] == "native" and network_type6 and network_type6 == "dhcp":
                        network_type6 = "none"

                    if network_type6 and network_type6 == "static":
                        if network_ip6 is not None:
                            network_ip6_split = network_ip6.split('/')
                            network_ip6 = network_ip6_split[0]

                            if network_ip6 and not is_valid_ip6_addr(network_ip6):
                                self.module.fail_json(msg="VM check networks[%s]: specified IPv6 address '%s' is not valid!" % (position, network_ip6))

                            if len(network_ip6_split) > 1:
                                network_prefix6 = network_ip6_split[1]

                                if not is_valid_ip6_prefix(network_prefix6):
                                    self.module.fail_json(msg="VM check networks[%s]: specified IPv6 prefix '%s' is not valid!" % (position, network_prefix6))

                    # If any parameter is overridden at this point, update it.
                    if network_type6:
                        network_params['type6'] = network_type6

                    if network_ip6:
                        network_params['ip6'] = network_ip6

                    if network_prefix6:
                        network_params['prefix6'] = network_prefix6

                    network_gateway6 = network_params.get('gateway6')

                    # Gateway can be an empty string (when removing gateway
                    # configuration) but if it is not, it should be validated.
                    if network_gateway6 and not is_valid_ip6_addr(network_gateway6):
                        self.module.fail_json(msg="VM check networks[%s]: specified IPv6 gateway '%s' is not valid!" % (position, network_gateway6))

                    # If this is an existing VIF.
                    if vm_vif_params and vm_vif_params['network']:
                        network_changes = []

                        if network_name and network_name != vm_vif_params['network']['name_label']:
                            network_changes.append('name')

                        if network_mac and network_mac != vm_vif_params['MAC'].lower():
                            network_changes.append('mac')

                        if self.vm_params['customization_agent'] == "native":
                            if network_type and network_type != vm_vif_params['ipv4_configuration_mode'].lower():
                                network_changes.append('type')

                            if network_type and network_type == "static":
                                if network_ip and (not vm_vif_params['ipv4_addresses'] or
                                                   not vm_vif_params['ipv4_addresses'][0] or
                                                   network_ip != vm_vif_params['ipv4_addresses'][0].split('/')[0]):
                                    network_changes.append('ip')

                                if network_prefix and (not vm_vif_params['ipv4_addresses'] or
                                                       not vm_vif_params['ipv4_addresses'][0] or
                                                       network_prefix != vm_vif_params['ipv4_addresses'][0].split('/')[1]):
                                    network_changes.append('prefix')
                                    network_changes.append('netmask')

                                if network_gateway is not None and network_gateway != vm_vif_params['ipv4_gateway']:
                                    network_changes.append('gateway')

                            if network_type6 and network_type6 != vm_vif_params['ipv6_configuration_mode'].lower():
                                network_changes.append('type6')

                            if network_type6 and network_type6 == "static":
                                if network_ip6 and (not vm_vif_params['ipv6_addresses'] or
                                                    not vm_vif_params['ipv6_addresses'][0] or
                                                    network_ip6 != vm_vif_params['ipv6_addresses'][0].split('/')[0]):
                                    network_changes.append('ip6')

                                if network_prefix6 and (not vm_vif_params['ipv6_addresses'] or
                                                        not vm_vif_params['ipv6_addresses'][0] or
                                                        network_prefix6 != vm_vif_params['ipv6_addresses'][0].split('/')[1]):
                                    network_changes.append('prefix6')

                                if network_gateway6 is not None and network_gateway6 != vm_vif_params['ipv6_gateway']:
                                    network_changes.append('gateway6')

                        elif self.vm_params['customization_agent'] == "custom":
                            vm_xenstore_data = self.vm_params['xenstore_data']

                            if network_type and network_type != vm_xenstore_data.get('vm-data/networks/%s/type' % vm_vif_params['device'], "none"):
                                network_changes.append('type')
                                need_poweredoff = True

                            if network_type and network_type == "static":
                                if network_ip and network_ip != vm_xenstore_data.get('vm-data/networks/%s/ip' % vm_vif_params['device'], ""):
                                    network_changes.append('ip')
                                    need_poweredoff = True

                                if network_prefix and network_prefix != vm_xenstore_data.get('vm-data/networks/%s/prefix' % vm_vif_params['device'], ""):
                                    network_changes.append('prefix')
                                    network_changes.append('netmask')
                                    need_poweredoff = True

                                if network_gateway is not None and network_gateway != vm_xenstore_data.get('vm-data/networks/%s/gateway' %
                                                                                                           vm_vif_params['device'], ""):
                                    network_changes.append('gateway')
                                    need_poweredoff = True

                            if network_type6 and network_type6 != vm_xenstore_data.get('vm-data/networks/%s/type6' % vm_vif_params['device'], "none"):
                                network_changes.append('type6')
                                need_poweredoff = True

                            if network_type6 and network_type6 == "static":
                                if network_ip6 and network_ip6 != vm_xenstore_data.get('vm-data/networks/%s/ip6' % vm_vif_params['device'], ""):
                                    network_changes.append('ip6')
                                    need_poweredoff = True

                                if network_prefix6 and network_prefix6 != vm_xenstore_data.get('vm-data/networks/%s/prefix6' % vm_vif_params['device'], ""):
                                    network_changes.append('prefix6')
                                    need_poweredoff = True

                                if network_gateway6 is not None and network_gateway6 != vm_xenstore_data.get('vm-data/networks/%s/gateway6' %
                                                                                                             vm_vif_params['device'], ""):
                                    network_changes.append('gateway6')
                                    need_poweredoff = True

                        config_changes_networks.append(network_changes)
                    # If this is a new VIF.
                    else:
                        if not network_name:
                            self.module.fail_json(msg="VM check networks[%s]: network name is required for new network interface!" % position)

                        if network_type and network_type == "static" and network_ip and not network_netmask:
                            self.module.fail_json(msg="VM check networks[%s]: IPv4 netmask or prefix is required for new network interface!" % position)

                        if network_type6 and network_type6 == "static" and network_ip6 and not network_prefix6:
                            self.module.fail_json(msg="VM check networks[%s]: IPv6 prefix is required for new network interface!" % position)

                        # Restart is needed if we are adding new network
                        # interface with IP/gateway parameters specified
                        # and custom agent is used.
                        if self.vm_params['customization_agent'] == "custom":
                            for parameter in ['type', 'ip', 'prefix', 'gateway', 'type6', 'ip6', 'prefix6', 'gateway6']:
                                if network_params.get(parameter):
                                    need_poweredoff = True
                                    break

                        if not vif_devices_allowed:
                            self.module.fail_json(msg="VM check networks[%s]: maximum number of network interfaces reached!" % position)

                        # We need to place a new network interface right above the
                        # highest placed existing interface to maintain relative
                        # positions pairable with network interface specifications
                        # in module params.
                        vif_device = str(int(vif_device_highest) + 1)

                        if vif_device not in vif_devices_allowed:
                            self.module.fail_json(msg="VM check networks[%s]: new network interface position %s is out of bounds!" % (position, vif_device))

                        vif_devices_allowed.remove(vif_device)
                        vif_device_highest = vif_device

                        # For new VIFs we only track their position.
                        config_new_networks.append((position, vif_device))

            # We should append config_changes_networks to config_changes only
            # if there is at least one changed network, else skip.
            for network_change in config_changes_networks:
                if network_change:
                    config_changes.append({"networks_changed": config_changes_networks})
                    break

            if config_new_networks:
                config_changes.append({"networks_new": config_new_networks})

            config_changes_custom_params = []

            if self.module.params['custom_params']:
                for position in range(len(self.module.params['custom_params'])):
                    custom_param = self.module.params['custom_params'][position]

                    custom_param_key = custom_param['key']
                    custom_param_value = custom_param['value']

                    if custom_param_key not in self.vm_params:
                        self.module.fail_json(msg="VM check custom_params[%s]: unknown VM param '%s'!" % (position, custom_param_key))

                    if custom_param_value != self.vm_params[custom_param_key]:
                        # We only need to track custom param position.
                        config_changes_custom_params.append(position)

            if config_changes_custom_params:
                config_changes.append({"custom_params": config_changes_custom_params})

            if need_poweredoff:
                config_changes.append('need_poweredoff')

            return config_changes

        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

    def get_normalized_disk_size(self, disk_params, msg_prefix=""):
        """Parses disk size parameters and returns disk size in bytes.

        This method tries to parse disk size module parameters. It fails
        with an error message if size cannot be parsed.

        Args:
            disk_params (dist): A dictionary with disk parameters.
            msg_prefix (str): A string error messages should be prefixed
                with (default: "").

        Returns:
            int: disk size in bytes if disk size is successfully parsed or
            None if no disk size parameters were found.
        """
        # There should be only single size spec but we make a list of all size
        # specs just in case. Priority is given to 'size' but if not found, we
        # check for 'size_tb', 'size_gb', 'size_mb' etc. and use first one
        # found.
        disk_size_spec = [x for x in disk_params.keys() if disk_params[x] is not None and (x.startswith('size_') or x == 'size')]

        if disk_size_spec:
            try:
                # size
                if "size" in disk_size_spec:
                    size_regex = re.compile(r'(\d+(?:\.\d+)?)\s*(.*)')
                    disk_size_m = size_regex.match(disk_params['size'])

                    if disk_size_m:
                        size = disk_size_m.group(1)
                        unit = disk_size_m.group(2)
                    else:
                        raise ValueError
                # size_tb, size_gb, size_mb, size_kb, size_b
                else:
                    size = disk_params[disk_size_spec[0]]
                    unit = disk_size_spec[0].split('_')[-1]

                if not unit:
                    unit = "b"
                else:
                    unit = unit.lower()

                if re.match(r'\d+\.\d+', size):
                    # We found float value in string, let's typecast it.
                    if unit == "b":
                        # If we found float but unit is bytes, we get the integer part only.
                        size = int(float(size))
                    else:
                        size = float(size)
                else:
                    # We found int value in string, let's typecast it.
                    size = int(size)

                if not size or size < 0:
                    raise ValueError

            except (TypeError, ValueError, NameError):
                # Common failure
                self.module.fail_json(msg="%sfailed to parse disk size! Please review value provided using documentation." % msg_prefix)

            disk_units = dict(tb=4, gb=3, mb=2, kb=1, b=0)

            if unit in disk_units:
                return int(size * (1024 ** disk_units[unit]))
            else:
                self.module.fail_json(msg="%s'%s' is not a supported unit for disk size! Supported units are ['%s']." %
                                      (msg_prefix, unit, "', '".join(sorted(disk_units.keys(), key=lambda key: disk_units[key]))))
        else:
            return None

    @staticmethod
    def get_cdrom_type(vm_cdrom_params):
        """Returns VM CD-ROM type."""
        # TODO: implement support for detecting type host. No server to test
        # this on at the moment.
        if vm_cdrom_params['empty']:
            return "none"
        else:
            return "iso"


def main():
    argument_spec = xenserver_common_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present',
                   choices=['present', 'absent', 'poweredon']),
        name=dict(type='str', aliases=['name_label']),
        name_desc=dict(type='str'),
        uuid=dict(type='str'),
        template=dict(type='str', aliases=['template_src']),
        template_uuid=dict(type='str'),
        is_template=dict(type='bool', default=False),
        folder=dict(type='str'),
        hardware=dict(
            type='dict',
            options=dict(
                num_cpus=dict(type='int'),
                num_cpu_cores_per_socket=dict(type='int'),
                memory_mb=dict(type='int'),
            ),
        ),
        disks=dict(
            type='list',
            elements='dict',
            options=dict(
                size=dict(type='str'),
                size_tb=dict(type='str'),
                size_gb=dict(type='str'),
                size_mb=dict(type='str'),
                size_kb=dict(type='str'),
                size_b=dict(type='str'),
                name=dict(type='str', aliases=['name_label']),
                name_desc=dict(type='str'),
                sr=dict(type='str'),
                sr_uuid=dict(type='str'),
            ),
            aliases=['disk'],
            mutually_exclusive=[
                ['size', 'size_tb', 'size_gb', 'size_mb', 'size_kb', 'size_b'],
                ['sr', 'sr_uuid'],
            ],
        ),
        cdrom=dict(
            type='dict',
            options=dict(
                type=dict(type='str', choices=['none', 'iso']),
                iso_name=dict(type='str'),
            ),
            required_if=[
                ['type', 'iso', ['iso_name']],
            ],
        ),
        networks=dict(
            type='list',
            elements='dict',
            options=dict(
                name=dict(type='str', aliases=['name_label']),
                mac=dict(type='str'),
                type=dict(type='str', choices=['none', 'dhcp', 'static']),
                ip=dict(type='str'),
                netmask=dict(type='str'),
                gateway=dict(type='str'),
                type6=dict(type='str', choices=['none', 'dhcp', 'static']),
                ip6=dict(type='str'),
                gateway6=dict(type='str'),
            ),
            aliases=['network'],
            required_if=[
                ['type', 'static', ['ip']],
                ['type6', 'static', ['ip6']],
            ],
        ),
        home_server=dict(type='str'),
        custom_params=dict(
            type='list',
            elements='dict',
            options=dict(
                key=dict(type='str', required=True),
                value=dict(type='raw', required=True),
            ),
        ),
        wait_for_ip_address=dict(type='bool', default=False),
        state_change_timeout=dict(type='int', default=0),
        linked_clone=dict(type='bool', default=False),
        force=dict(type='bool', default=False),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=[
                               ['name', 'uuid'],
                           ],
                           mutually_exclusive=[
                               ['template', 'template_uuid'],
                           ],
                           )

    result = {'failed': False, 'changed': False}

    vm = XenServerVM(module)

    # Find existing VM
    if vm.exists():
        if module.params['state'] == "absent":
            vm.destroy()
            result['changed'] = True
        elif module.params['state'] == "present":
            config_changes = vm.reconfigure()

            if config_changes:
                result['changed'] = True

                # Make new disk and network changes more user friendly
                # and informative.
                for change in config_changes:
                    if isinstance(change, dict):
                        if change.get('disks_new'):
                            disks_new = []

                            for position, userdevice in change['disks_new']:
                                disk_new_params = {"position": position, "vbd_userdevice": userdevice}
                                disk_params = module.params['disks'][position]

                                for k in disk_params.keys():
                                    if disk_params[k] is not None:
                                        disk_new_params[k] = disk_params[k]

                                disks_new.append(disk_new_params)

                            if disks_new:
                                change['disks_new'] = disks_new

                        elif change.get('networks_new'):
                            networks_new = []

                            for position, device in change['networks_new']:
                                network_new_params = {"position": position, "vif_device": device}
                                network_params = module.params['networks'][position]

                                for k in network_params.keys():
                                    if network_params[k] is not None:
                                        network_new_params[k] = network_params[k]

                                networks_new.append(network_new_params)

                            if networks_new:
                                change['networks_new'] = networks_new

            result['changes'] = config_changes

        elif module.params['state'] in ["poweredon", "poweredoff", "restarted", "shutdownguest", "rebootguest", "suspended"]:
            result['changed'] = vm.set_power_state(module.params['state'])
    elif module.params['state'] != "absent":
        vm.deploy()
        result['changed'] = True

    if module.params['wait_for_ip_address'] and module.params['state'] != "absent":
        vm.wait_for_ip_address()

    result['instance'] = vm.gather_facts()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
