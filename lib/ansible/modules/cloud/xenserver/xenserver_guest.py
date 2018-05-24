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
short_description: Manages virtual machines running on Citrix XenServer host or pool
description:
- Create new virtual machines from templates or other virtual machines.
- Manage power state of virtual machine such as power on, power off, suspend, shutdown, reboot, restart etc.,.
- Modify, rename or remove a virtual machine.
version_added: '2.6'
author:
- Bojan Vitnik (@bvitnik) <bvitnik@mainstream.rs>
notes:
- Tested on XenServer 6.5 and 7.1
requirements:
- python >= 2.6
- XenAPI
options:
  state:
    description:
    - Specify the state VM should be in.
    - If C(state) is set to C(present) and VM exists, ensure the VM configuration conforms to task arguments.
    default: present
    choices: [ present, absent, poweredon, poweredoff, restarted, suspended, shutdownguest, rebootguest ]
  name:
    description:
    - Name of the VM to work with.
    - VMs running on XenServer do not necessarily have unique names. The module will fail if multiple VMs with same name are found.
    - In case of multiple VMs with same name, use C(uuid) to uniquely specify VM to manage.
    - This parameter is case sensitive.
    required: yes
    aliases: [ 'name_label' ]
  name_desc:
    description:
    - VM description.
  uuid:
    description:
    - UUID of the VM to manage if known, this is XenServer's unique identifier.
    - It is required if name is not unique.
    - Please note that a supplied UUID will be ignored on VM creation, as XenServer creates the UUID internally.
  template:
    description:
    - Name of a template, an existing VM (must be in shutdown state) or a snapshot that should be used to create VM.
    - Templates/VMs/snapshots on XenServer do not necessarily have unique names. The module will fail if multiple VMs with same name are found.
    - In case of multiple templates/VMs/snapshots with same name, use C(template_uuid) to uniquely specify source template.
    - If VM already exists, this setting will be ignored.
    - This parameter is case sensitive.
    aliases: [ 'template_src' ]
  template_uuid:
    description:
    - UUID of a template, an existing VM or a snapshot that should be used to create VM.
    - It is required if template name is not unique.
  is_template:
    description:
    - Convert VM to template.
    default: 'no'
    type: bool
  folder:
    description:
    - Destination folder for VM.
    - This parameter is case sensitive.
    - 'Example:'
    - '   folder: /folder1/folder2'
  hardware:
    description:
    - Manage VM's hardware attributes. VM needs to be shut down to reconfigure these parameters.
    - All parameters case sensitive.
    - 'Valid attributes are:'
    - ' - C(num_cpus) (integer): Number of CPUs.'
    - ' - C(num_cpu_cores_per_socket) (integer): Number of Cores Per Socket. C(num_cpus) has to be a multiple of C(num_cpu_cores_per_socket).'
    - ' - C(memory_mb) (integer): Amount of memory in MB.'
  disks:
    description:
    - A list of disks to add to VM.
    - This parameter is case sensitive.
    - Removing or detaching existing disks of VM is not supported.
    - 'Required attributes are:'
    - ' - C(size_[tb,gb,mb,kb,b]) (integer): Disk storage size in specified unit. VM needs to be shut down to reconfigure this parameter'
    - 'Optional attributes are:'
    - ' - C(name) (string): Disk name. You can also use C(name_label) as an alias.'
    - ' - C(name_desc) (string): Disk description.'
    - ' - C(sr) (string): Storage Repository to create disk on. If not specified, will use default SR. Can not be used for moving disk to other SR.'
    - ' - C(sr_uuid) (string): UUID of a SR to create disk on. Use if SR name is not unique.'
    aliases: [ 'disk' ]
  cdrom:
    description:
    - A CD-ROM configuration for the VM.
    - 'Valid attributes are:'
    - ' - C(type) (string): The type of CD-ROM, valid options are C(none), C(host) or C(iso). With C(none) the CD-ROM device will be present but empty.'
    - ' - C(iso) (string): The file name of the ISO image from one of the XenServer ISO Libraries. Required if type is set to C(iso).'
  networks:
    description:
    - A list of networks (in the order of the NICs).
    - All parameters and XenServer object names are case sensetive.
    - 'Required atributes are:'
    - ' - C(name) (string): Name of a XenServer network to attach the network interface to. You can also use C(name_label) as an alias.'
    - 'Optional attributes are:'
    - ' - C(mac) (string): Customize MAC address of the interface.'
    aliases: [ 'network' ]
  home_server:
    description:
    - Name of a XenServer host that will be a Home Server for the VM.
    - This parameter is case sensitive.
  custom_params:
    description:
    - Define a list of custom VM params to set on VM.
    - A custom value object takes two fields C(key) and C(value).
    - Incorrect key and values will be ignored.
  wait_for_ip_address:
    description:
    - Wait until XenServer detects an IP address for the VM.
    - This requires XenServer Tools preinstaled on VM to properly work.
    default: 'no'
    type: bool
  state_change_timeout:
    description:
    - By default, module will wait indefinitely for VM to reach poweredoff state if C(state=shutdownguest)), poweredon state if C(state=rebootguest)
    - and for an IP address if C(wait_for_ip_address=yes).
    - If this attribute is set to positive value, the module will instead wait specified number of seconds for the state change.
    - In case of timeout, module will generate an error message.
    default: 0
  linked_clone:
    description:
    - Whether to create a Linked Clone from the template, existing VM or snapshot. If no, will create a full copy.
    default: 'no'
    type: bool
  force:
    description:
    - Ignore warnings and complete the actions.
    - This parameter is useful for removing VM in poweredon state or reconfiguring VM params that require VM to be in poweredoff state.
    default: 'no'
    type: bool
extends_documentation_fragment: xenserver.documentation
'''

EXAMPLES = r'''
- name: Create a VM from a template
  xenserver_guest:
    hostname: 192.0.2.44
    username: root
    password: xenserver
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
      iso: guest-tools.iso
    networks:
    - name: VM Network
      mac: aa:bb:dd:aa:00:14
    wait_for_ip_address: yes
  delegate_to: localhost
  register: deploy

- name: Create a VM template
  xenserver_guest:
    hostname: 192.0.2.88
    username: root
    password: xenserver
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

- name: Rename a VM (requires the VM's uuid)
  xenserver_guest:
    hostname: 192.168.1.209
    username: root
    password: xenserver
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    name: new_name
    state: present
  delegate_to: localhost

- name: Remove a VM by uuid
  xenserver_guest:
    hostname: 192.168.1.209
    username: root
    password: xenserver
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    state: absent
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

HAS_XENAPI = False
try:
    import XenAPI
    HAS_XENAPI = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils import six
from ansible.module_utils.xenserver import xenserver_common_argument_spec, XAPI, XenServerObject, gather_vm_params, gather_vm_facts, wait_for_task


class XenServerVM(XenServerObject):
    def __init__(self, module):
        super(XenServerVM, self).__init__(module)

        self.vm_ref = None
        self.vm_params = None
        self.vm_searched = False

        self.exists()

    def exists(self):
        if not self.vm_searched:
            try:
                # UUID has precendence over name.
                if self.module.params['uuid']:
                    # Find VM by UUID. If no VM is found using given UUID, an
                    # exception will be generated and module will fail with
                    # an error message.
                    self.vm_ref = self.xapi_session.xenapi.VM.get_by_uuid(self.module.params['uuid'])
                else:
                    # Find VM by name (name_label).
                    vm_ref_list = self.xapi_session.xenapi.VM.get_by_name_label(self.module.params['name'])

                    # If vm_ref_list is empty.
                    if not vm_ref_list:
                        self.vm_ref = None
                    # If vm_ref_list contains multiple VM references.
                    elif len(vm_ref_list) > 1:
                        self.module.fail_json(msg="Multiple VMs with same name found but uuid not specified!")
                    # The vm_ref_list contains only one VM reference.
                    else:
                        self.vm_ref = vm_ref_list[0]

                # If we at this point have a valid vm_ref, gather the VM params.
                if self.vm_ref is not None:
                    self.gather_params()
            except XenAPI.Failure as f:
                self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

            self.vm_searched = True

        if self.vm_ref is not None:
            return True
        else:
            return False

    def gather_params(self):
        self.vm_params = gather_vm_params(self.module, self.vm_ref)

    def gather_facts(self):
        return gather_vm_facts(self.module, self.vm_params)

    def deploy(self):
        # Safety check.
        if self.exists():
            self.module.fail_json(msg="Called deploy on existing VM!")

        try:
            # UUID has precendence over name.
            if self.module.params['template_uuid']:
                # Find template by UUID. If no template is found using given
                # UUID, XAPI exception will be generated and module will fail
                # with an error message.
                templ_ref = self.xapi_session.xenapi.VM.get_by_uuid(self.module.params['template_uuid'])
            elif self.module.params['template']:
                # Find template by name (name_label).
                templ_ref_list = self.xapi_session.xenapi.VM.get_by_name_label(self.module.params['template'])

                # If templ_ref_list is empty.
                if not templ_ref_list:
                    self.module.fail_json(msg="Template not found!")
                # If templ_ref_list contains multiple template references.
                elif len(templ_ref_list) > 1:
                    self.module.fail_json(msg="Multiple templates with same name found! Please use template_uuid.")
                # The templ_ref_list contains only one template reference.
                else:
                    templ_ref = templ_ref_list[0]
            else:
                self.module.fail_json(msg="Either template or template_uuid has to be specified when deploying a VM!")

            # Is this an existing running VM?
            if self.xapi_session.xenapi.VM.get_power_state(templ_ref).lower() != 'halted':
                self.module.fail_json(msg="Running VM can't be used as a template!")

            # Find a SR we can use for VM.copy. We use SR of the first disk if
            # specified or default SR if not specified.
            disk_param_list = self.module.params['disks']

            sr_ref = None

            if disk_param_list:
                disk_param = disk_param_list[0]

                if "sr_uuid" in disk_param:
                    sr_ref = self.xapi_session.xenapi.SR.get_by_uuid(disk_param['sr_uuid'])
                elif "sr" in disk_param:
                    sr_ref_list = self.xapi_session.xenapi.SR.get_by_name_label(disk_param['sr'])

                    # If sr_ref_list is empty.
                    if not sr_ref_list:
                        self.module.fail_json(msg="disks[0]: specified SR %s not found!" % disk_param['sr'])
                    # If sr_ref_list contains multiple sr references.
                    elif len(sr_ref_list) > 1:
                        self.module.fail_json(msg="disks[0]: multiple SRs with name %s found! Please use sr_uuid." % disk_param['sr'])
                    # The sr_ref_list contains only one sr reference.
                    else:
                        sr_ref = sr_ref_list[0]

            if not sr_ref:
                if self.default_sr_ref != "OpaqueRef:NULL":
                    sr_ref = self.default_sr_ref
                else:
                    self.module.fail_json(msg="disks[0]: no default SR found! You must specify SR explicitely.")

            # Support for ansible check mode.
            if self.module.check_mode:
                return

            # VM name could be an empty string which is bad.
            if self.module.params['name'] is not None and not self.module.params['name']:
                self.module.fail_json(msg="VM name can't be an empty string!")

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
            # Note: for some reason, VM.get_is_default_template() does not work.
            #       We get MESSAGE_METHOD_UNKNOWN error from XAPI so we use
            #       an alternative way.
            templ_other_config = self.xapi_session.xenapi.VM.get_other_config(templ_ref)

            if "default_template" in templ_other_config and templ_other_config['default_template']:
                # other_config of built-in XenServer templates have a key called
                # disks with the following content:
                #   disks: <provision><disk bootable="true" device="0" size="10737418240" sr="" type="system"/></provision>
                # This value oof other_data is copied to cloned or copied VM and
                # it prevents provisioning of VM because sr is not specified and
                # XAPI returns an error. To get around this, we remove the
                # disks key and add disks to VM later ourselves.
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
                self.poweron()

        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

    def reconfigure(self):
        # Safety check.
        if not self.exists():
            self.module.fail_json(msg="Called reconfigure on non existing VM!")

        config_changes = self.get_changes()

        vm_power_state = self.vm_params['power_state'].lower()

        if "need_poweredoff" in config_changes and vm_power_state != 'halted':
            if self.module.params['force']:
                self.shutdownguest()
            else:
                self.module.fail_json(msg="VM has to be in powered off state to reconfigure but force was not specified!")

        # Support for ansible check mode.
        if self.module.check_mode:
            return config_changes

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
                                num_cpus = int(self.module.params['hardware'].get('num_cpus'))

                                if num_cpus < int(self.vm_params['VCPUs_at_startup']):
                                    self.xapi_session.xenapi.VM.set_VCPUs_at_startup(self.vm_ref, str(self.module.params['hardware'].get('num_cpus')))
                                    self.xapi_session.xenapi.VM.set_VCPUs_max(self.vm_ref, str(self.module.params['hardware'].get('num_cpus')))
                                else:
                                    self.xapi_session.xenapi.VM.set_VCPUs_max(self.vm_ref, str(self.module.params['hardware'].get('num_cpus')))
                                    self.xapi_session.xenapi.VM.set_VCPUs_at_startup(self.vm_ref, str(self.module.params['hardware'].get('num_cpus')))
                            elif hardware_change == "num_cpu_cores_per_socket":
                                self.xapi_session.xenapi.VM.remove_from_platform(self.vm_ref, 'cores-per-socket')
                                num_cpu_cores_per_socket = self.module.params['hardware'].get('num_cpu_cores_per_socket')

                                if int(num_cpu_cores_per_socket) > 1:
                                    self.xapi_session.xenapi.VM.add_to_platform(self.vm_ref, 'cores-per-socket', str(num_cpu_cores_per_socket))
                            elif hardware_change == "memory_mb":
                                memory_b = str(int(self.module.params['hardware'].get('memory_mb')) * 1048576)
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
                                    self.xapi_session.xenapi.VDI.resize(vdi_ref, str(self.get_normalized_disk_size(self.module.params['disks'], position)))

                            position += 1
                    elif change.get('disks_new'):
                        for position, disk_userdevice in change['disks_new']:
                            disk_params = self.module.params['disks'][position]

                            if "sr_uuid" in disk_params:
                                sr_ref = self.xapi_session.xenapi.SR.get_by_uuid(disk_params['sr_uuid'])
                            elif "sr" in disk_params:
                                sr_ref = self.xapi_session.xenapi.SR.get_by_name_label(disk_params['sr'])[0]
                            else:
                                sr_ref = self.default_sr_ref

                            new_disk_vdi = {
                                "name_label": disk_params.get('name', "%s-%s" % (self.vm_params['name_label'], position)),
                                "name_description": disk_params.get('name_desc', ""),
                                "SR": sr_ref,
                                "virtual_size": str(self.get_normalized_disk_size(self.module.params['disks'], position)),
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
                            self.xapi_session.xenapi.VBD.create(new_disk_vbd)
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

                            elif cdrom_change == "iso":
                                if not cdrom_is_empty:
                                    self.xapi_session.xenapi.VBD.eject(cdrom_vbd_ref)

                                cdrom_vdi_ref = self.xapi_session.xenapi.VDI.get_by_name_label(self.module.params['cdrom']['iso'])[0]
                                self.xapi_session.xenapi.VBD.insert(cdrom_vbd_ref, cdrom_vdi_ref)
                    elif change.get('networks_changed'):
                        position = 0

                        for network_change_list in change['networks_changed']:
                            vm_vif_params = self.vm_params['VIFs'][position]
                            vif_ref = self.xapi_session.xenapi.VIF.get_by_uuid(vm_vif_params['uuid'])
                            network_ref = self.xapi_session.xenapi.network.get_by_uuid(vm_vif_params['network']['uuid'])

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

                            for network_change in network_change_list:

                                if network_change == "name":
                                    network_ref_new = self.xapi_session.xenapi.network.get_by_name_label(self.module.params['networks'][position]['name'])[0]
                                    vif['network'] = network_ref_new
                                    vif['MTU'] = self.xapi_session.xenapi.network.get_MTU(network_ref_new)
                                elif network_change == "mac":
                                    vif['MAC'] = self.module.params['networks'][position]['mac'].lower()

                            if network_change_list:
                                # We destroy old VIF and then create a new one
                                # with changed parameters. That's how XenCenter
                                # does it.
                                self.xapi_session.xenapi.VIF.destroy(vif_ref)
                                self.xapi_session.xenapi.VIF.create(vif)

                            position += 1
                    elif change.get('networks_new'):
                        for position, vif_device in change['networks_new']:
                            network_ref = self.xapi_session.xenapi.network.get_by_name_label(self.module.params['networks'][position]['name'])[0]

                            vif = {
                                "device": vif_device,
                                "network": network_ref,
                                "VM": self.vm_ref,
                                "MAC": self.module.params['networks'][position].get('mac', ''),
                                "MTU": self.xapi_session.xenapi.network.get_MTU(network_ref),
                                "other_config": {},
                                "qos_algorithm_type": "",
                                "qos_algorithm_params": {},
                            }

                            self.xapi_session.xenapi.VIF.create(vif)
                    elif change.get('custom_params'):
                        for position in change['custom_params']:
                            custom_param_key = self.module.params['custom_params'][position]['key']
                            custom_param_value = self.module.params['custom_params'][position]['value']
                            self.xapi_session.xenapi_request("VM.set_%s" % custom_param_key, (self.vm_ref, custom_param_value))

            if self.module.params.get('is_template'):
                self.xapi_session.xenapi.VM.set_is_a_template(self.vm_ref, True)
            elif "need_poweredoff" in config_changes and self.module.params['force'] and vm_power_state != 'halted':
                self.poweron()

            # Gather new params after reconfiguration.
            self.gather_params()

        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

        return config_changes

    def destroy(self):
        # Safety check.
        if not self.exists():
            self.module.fail_json(msg="Called destroy on non existing VM!")

        if self.vm_params['power_state'].lower() != 'halted':
            if self.module.params['force']:
                self.poweroff()
            else:
                self.module.fail_json(msg="VM has to be in powered off state to destroy but force was not specified!")

        # Support for ansible check mode.
        if self.module.check_mode:
            return

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

        self.vm_params['power_state'] == "halted"

    def get_changes(self):
        # Safety check.
        if not self.exists():
            self.module.fail_json(msg="Called get_changes on non existing VM!")

        need_poweredoff = False

        if self.module.params.get('is_template'):
            need_poweredoff = True

        try:
            # This VM could be a template or a snapshot. In that case we fail
            # because we can't reconfigure them or it would just be too
            # dangerous.
            if self.vm_params['is_a_template'] and not self.vm_params['is_a_snapshot']:
                self.module.fail_json(msg="Targeted VM is a template. Template reconfiguration is not supported!")

            if self.vm_params['is_a_snapshot']:
                self.module.fail_json(msg="Targeted VM is a snapshot. Snapshot reconfiguration is not supported!")

            # Let's build a list of parameters that changed.
            config_changes = []

            # Name could only differ if we found an existing VM by uuid.
            if self.module.params['name'] is not None and self.module.params['name'] != self.vm_params['name_label']:
                if self.module.params['name']:
                    config_changes.append('name')
                else:
                    self.module.fail_json(msg="VM name can't be an empty string!")

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
                    host_ref_list = self.xapi_session.xenapi.host.get_by_name_label(self.module.params['home_server'])

                    # If host_ref_list is empty.
                    if not host_ref_list:
                        self.module.fail_json(msg="Specified home server '%s' not found!" % self.module.params['home_server'])
                    # If host_ref_list contains multiple network references.
                    elif len(host_ref_list) > 1:
                        self.module.fail_json(msg="Multiple home servers with name '%s' found!" % self.module.params['home_server'])

                    config_changes.append('home_server')
                elif not self.module.params['home_server'] and self.vm_params['affinity']:
                    config_changes.append('home_server')

            config_changes_hardware = []

            if self.module.params['hardware']:
                num_cpus = self.module.params['hardware'].get('num_cpus')

                if num_cpus is not None:
                    try:
                        num_cpus = int(num_cpus)
                    except ValueError as e:
                        self.module.fail_json(msg="hardware.num_cpus attribute should be an integer value!")

                    if num_cpus < 1:
                        self.module.fail_json(msg="hardware.num_cpus attribute should be greater than zero!")

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
                    try:
                        num_cpu_cores_per_socket = int(num_cpu_cores_per_socket)
                    except ValueError as e:
                        self.module.fail_json(msg="hardware.num_cpu_cores_per_socket attribute should be an integer value.")

                    if num_cpu_cores_per_socket < 1:
                        self.module.fail_json(msg="hardware.num_cpu_cores_per_socket attribute should be greater than zero!")

                    if num_cpus and num_cpus % num_cpu_cores_per_socket != 0:
                        self.module.fail_json(msg="hardware.num_cpus attribute should be a multiple of hardware.num_cpu_cores_per_socket.")

                    vm_platform = self.vm_params['platform']
                    vm_cores_per_socket = int(vm_platform.get('cores-per-socket', 1))

                    if num_cpu_cores_per_socket != vm_cores_per_socket:
                        config_changes_hardware.append('num_cpu_cores_per_socket')
                        # For now, we don't support hotpluging so VM has to be
                        # in poweredoff state to reconfigure.
                        need_poweredoff = True

                memory_mb = self.module.params['hardware'].get('memory_mb')

                if memory_mb is not None:
                    try:
                        memory_mb = int(memory_mb)
                    except ValueError as e:
                        self.module.fail_json(msg="hardware.memory_mb attribute should be an integer value.")

                    if memory_mb < 1:
                        self.module.fail_json(msg="hardware.memory_mb attribute should be greater than zero!")

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
                    if memory_mb != max(int(self.vm_params['memory_dynamic_max']), int(self.vm_params['memory_static_max'])) / 1048576:
                        config_changes_hardware.append('memory_mb')
                        # For now, we don't support hotpluging so VM has to be in
                        # poweredoff state to reconfigure.
                        need_poweredoff = True

            if config_changes_hardware:
                config_changes.append({"hardware": config_changes_hardware})

            config_changes_disks = []
            config_new_disks = []

            if self.module.params['disks']:
                # Get the list of all disk. Filter out any CDs found.
                vm_disk_params_list = [disk_params for disk_params in self.vm_params['VBDs'] if disk_params['type'] == "Disk"]

                # Number of disks defined in module params have to be same or
                # higher than a number of existing disks attached to the VM.
                # We don't support removal or detachment of disks.
                if len(self.module.params['disks']) < len(vm_disk_params_list):
                    self.module.fail_json(msg="Provided disks configuration has less disks than the target VM (%d vs %d)!" %
                                          (len(self.module.params['disks']), len(vm_disk_params_list)))

                # Iterate over existing disks.
                for position in range(len(vm_disk_params_list)):
                    vm_disk_params = vm_disk_params_list[position]
                    disk_params = self.module.params['disks'][position]

                    disk_changes = []

                    if "name_label" in disk_params:
                        disk_params['name'] = disk_params['name_label']

                    disk_name = disk_params.get('name')

                    if disk_name is not None and not disk_name:
                        self.module.fail_json(msg="disks[%s]: disk name can't be an empty string!" % position)
                    elif disk_name and vm_disk_params['VDI'] and disk_name != vm_disk_params['VDI']['name_label']:
                        disk_changes.append('name')

                    disk_name_desc = disk_params.get('name_desc')

                    if disk_name_desc is not None and vm_disk_params['VDI'] and disk_name_desc != vm_disk_params['VDI']['name_description']:
                        disk_changes.append('name_desc')

                    disk_size = self.get_normalized_disk_size(self.module.params['disks'], position)

                    if disk_size and vm_disk_params['VDI']:
                        if disk_size > int(vm_disk_params['VDI']['virtual_size']):
                            disk_changes.append('size')
                            need_poweredoff = True
                        elif disk_size < int(vm_disk_params['VDI']['virtual_size']):
                            self.module.fail_json(msg="disks[%s]: disk size is smaller than existing (%d bytes < %s bytes). "
                                                  "Reducing disk size is not allowed!" % (position, disk_size, vm_disk_params['VDI']['virtual_size']))

                    config_changes_disks.append(disk_changes)

                disk_userdevices_allowed = self.xapi_session.xenapi.VM.get_allowed_VBD_devices(self.vm_ref)

                # Find the highest occupied userdevice.
                if not self.vm_params['VBDs']:
                    vbd_userdevice_highest = "-1"
                else:
                    vbd_userdevice_highest = self.vm_params['VBDs'][-1]['userdevice']

                # Iterate over new disks.
                for position in range(len(vm_disk_params_list), len(self.module.params['disks'])):
                    disk_params = self.module.params['disks'][position]

                    if "name_label" in disk_params:
                        disk_params['name'] = disk_params['name_label']

                    disk_name = disk_params.get('name')

                    if disk_name is not None and not disk_name:
                        self.module.fail_json(msg="disks[%s]: disk name can't be an empty string!" % position)

                    # For new disks we only need to check if disk size is
                    # correctly specified and if sr exits.
                    disk_size = self.get_normalized_disk_size(self.module.params['disks'], position)

                    if not disk_size:
                        self.module.fail_json(msg="disks[%s]: no valid disk size specification found!" % position)

                    # If sr_uuid is specified, we ignore sr. We don't check for
                    # existance of SR with sr_uuid here. We will check it when
                    # creating disks.
                    if "sr_uuid" not in disk_params:
                        disk_sr = disk_params.get('sr')

                        if disk_sr is not None:
                            sr_ref_list = self.xapi_session.xenapi.SR.get_by_name_label(disk_sr)

                            # If sr_ref_list is empty.
                            if not sr_ref_list:
                                self.module.fail_json(msg="disks[%s]: specified SR '%s' not found!" % (position, disk_sr))
                            # If sr_ref_list contains multiple sr references.
                            elif len(sr_ref_list) > 1:
                                self.module.fail_json(msg="disks[%s]: multiple SRs with name '%s' found! Please use sr_uuid." % (position, disk_sr))

                        elif self.default_sr_ref == 'OpaqueRef:NULL':
                            self.module.fail_json(msg="disks[%s]: no default SR found! You must specify SR explicitely." % position)

                    # We need to place a new disk right above the highest placed
                    # existing disk to maintain relative disk positions pairable
                    # with disk specifications in module params.
                    disk_userdevice = str(int(vbd_userdevice_highest) + 1)

                    if disk_userdevice not in disk_userdevices_allowed:
                        self.module.fail_json(msg="disks[%s]: new disk position %s is out of bounds!" % (position, disk_userdevice))

                    vbd_userdevice_highest = disk_userdevice

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
                if "type" not in self.module.params['cdrom']:
                    self.module.fail_json(msg="cdrom.type attribute not specified!")
                elif self.module.params['cdrom']['type'] not in ['none', 'host', 'iso']:
                    self.module.fail_json(msg="cdrom.type '%s' not valid! Valid types are ['none', 'host', 'iso']." % self.module.params['cdrom']['type'])
                elif self.module.params['cdrom']['type'] == "iso" and "iso" not in self.module.params['cdrom']:
                    self.module.fail_json(msg="cdrom.type is iso but no cdrom.iso attribute specified!")

                # Get the list of all CDROMs. Filter out any regular disks
                # found. If we found no existing CDROM, we will create it
                # later else take the first one found.
                vm_cdrom_params_list = [cdrom_params for cdrom_params in self.vm_params['VBDs'] if cdrom_params['type'] == "CD"]

                # If no existing CDROM is found, we will need to add one.
                # We need to check if there is any userdevice allowed.
                if not vm_cdrom_params_list:
                    cdrom_userdevices_allowed = self.xapi_session.xenapi.VM.get_allowed_VBD_devices(self.vm_ref)

                    if not cdrom_userdevices_allowed:
                        self.module.fail_json(msg="No allowed position found for new CDROM!")

                # If type changed.
                if not vm_cdrom_params_list or self.module.params['cdrom']['type'] != self.get_cdrom_type(vm_cdrom_params_list[0]):
                    config_changes_cdrom.append('type')

                # Is ISO image changed?
                if (self.module.params['cdrom']['type'] == "iso" and
                        (not vm_cdrom_params_list[0]['VDI'] or self.module.params['cdrom']['iso'] != vm_cdrom_params_list[0]['VDI']['name_label'])):
                    config_changes_cdrom.append('iso')

                # Check if ISO exists.
                if self.module.params['cdrom']['type'] == "iso":
                    vdi_ref_list = self.xapi_session.xenapi.VDI.get_by_name_label(self.module.params['cdrom']['iso'])

                    # If vdi_ref_list is empty.
                    if not vdi_ref_list:
                        self.module.fail_json(msg="Specified ISO image '%s' not found!" % self.module.params['cdrom']['iso'])
                    # If sr_ref_list contains multiple sr references.
                    elif len(vdi_ref_list) > 1:
                        self.module.fail_json(msg="Multiple ISO images with name '%s' found!" % self.module.params['cdrom']['iso'])

            if config_changes_cdrom:
                config_changes.append({"cdrom": config_changes_cdrom})

            config_changes_networks = []
            config_new_networks = []

            if self.module.params['networks']:
                # Number of VIFs defined in module params have to be same or
                # higher than a number of existing VIFs attached to the VM.
                # We don't support removal of VIFs.
                if len(self.module.params['networks']) < len(self.vm_params['VIFs']):
                    self.module.fail_json(msg="Provided networks configuration has less interfaces than the target VM (%d vs %d)!" %
                                          (len(self.module.params['networks']), len(self.vm_params['VIFs'])))

                # Iterate over existing VIFs.
                for position in range(len(self.vm_params['VIFs'])):
                    vm_vif_params = self.vm_params['VIFs'][position]
                    network_params = self.module.params['networks'][position]

                    network_changes = []

                    if "name_label" in network_params:
                        network_params['name'] = network_params['name_label']

                    network_name = network_params.get('name')

                    if network_name is not None and vm_vif_params['network'] and network_name != vm_vif_params['network']['name_label']:
                        network_ref_list = self.xapi_session.xenapi.network.get_by_name_label(network_name)

                        # If network_ref_list is empty.
                        if not network_ref_list:
                            self.module.fail_json(msg="networks[%s]: specified network name '%s' not found!" % (position, network_name))
                        # If network_ref_list contains multiple network references.
                        elif len(network_ref_list) > 1:
                            self.module.fail_json(msg="networks[%s]: multiple networks with name '%s' found!" % (position, network_name))

                        network_changes.append('name')

                    network_mac = network_params.get('mac')

                    if network_mac is not None:
                        network_mac = network_mac.lower()

                        if not self.is_valid_mac_addr(network_mac):
                            self.module.fail_json(msg="networks[%s]: specified MAC address '%s' not valid!" % (position, network_mac))

                        if network_mac != vm_vif_params['MAC'].lower():
                            network_changes.append('mac')

                    config_changes_networks.append(network_changes)

                vif_devices_allowed = self.xapi_session.xenapi.VM.get_allowed_VIF_devices(self.vm_ref)

                # Find the highest occupied device.
                if not self.vm_params['VIFs']:
                    vif_device_highest = "-1"
                else:
                    vif_device_highest = self.vm_params['VIFs'][-1]['device']

                # Iterate over new VIFs.
                for position in range(len(self.vm_params['VIFs']), len(self.module.params['networks'])):
                    network_params = self.module.params['networks'][position]

                    if "name_label" in network_params:
                        network_params['name'] = network_params['name_label']

                    network_name = network_params.get('name')

                    if network_name is not None:
                        network_ref_list = self.xapi_session.xenapi.network.get_by_name_label(network_name)

                        # If network_ref_list is empty.
                        if not network_ref_list:
                            self.module.fail_json(msg="networks[%s]: specified network name '%s' not found!" % (position, network_name))
                        # If network_ref_list contains multiple network references.
                        elif len(network_ref_list) > 1:
                            self.module.fail_json(msg="networks[%s]: multiple networks with name '%s' found!" % (position, network_name))
                    else:
                        self.module.fail_json(msg="networks[%s]: name or name_label missing!" % position)

                    network_mac = network_params.get('mac')

                    if network_mac is not None:
                        network_mac = network_mac.lower()

                        if not self.is_valid_mac_addr(network_mac):
                            self.module.fail_json(msg="networks[%s]: specified MAC address '%s' not valid!" % (position, network_mac))

                    # We need to place a new network interface right above the
                    # highest placed existing interface to maintain relative
                    # positions pairable with network interface specifications
                    # in module params.
                    vif_device = str(int(vif_device_highest) + 1)

                    if vif_device not in vif_devices_allowed:
                        self.module.fail_json(msg="networks[%s]: new network interface position %s is out of bounds!" % (position, vif_device))

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

                    if "key" not in custom_param:
                        self.module.fail_json(msg="custom_params[%s]: key not found!" % position)
                    elif "value" not in custom_param:
                        self.module.fail_json(msg="custom_params[%s]: value not found!" % position)

                    custom_param_key = custom_param['key']
                    custom_param_value = custom_param['value']

                    if custom_param_key not in self.vm_params:
                        self.module.fail_json(msg="custom_params[%s]: unknown VM param '%s'!" % (position, custom_param_key))

                    if custom_param_value != self.vm_params[custom_param_key]:
                        # We only need to track custom param posutuin.
                        config_changes_custom_params.append(position)

            if config_changes_custom_params:
                config_changes.append({"custom_params": config_changes_custom_params})

            if need_poweredoff:
                config_changes.append('need_poweredoff')

            return config_changes

        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

    def get_normalized_disk_size(self, disk_params_list, position):
        disk_params = disk_params_list[position]

        # There could be multiple size specs. We give a priority to size but if not
        # found, we check for size_tb, size_gb, size_mb etc. and use first one found.
        disk_size_spec = [x for x in disk_params.keys() if x.startswith('size_') or x == 'size']

        if disk_size_spec:
            try:
                # size
                if "size" in disk_params:
                    size_regex = re.compile(r'(\d+(?:\.\d+)?)\s*([tgmkTGMK]?[bB]?)')
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

                if not size:
                    raise ValueError

            except (TypeError, ValueError, NameError):
                # Common failure
                self.module.fail_json(msg="disks[%s]: failed to parse disk size. Please review value provided using documentation." % position)

            disk_units = dict(tb=4, gb=3, mb=2, kb=1, b=0)

            if unit in disk_units:
                return int(size * (1024 ** disk_units[unit]))
            else:
                self.module.fail_json(msg="disks[%s]: '%s' is not a supported unit for disk size. Supported units are ['%s']." %
                                      (position, unit, "', '".join(sorted(disk_units.keys(), key=lambda key: disk_units[key]))))
        else:
            return None

    @staticmethod
    def get_cdrom_type(vm_cdrom_params):
        # TODO: implement support for detecting type host. No server to test
        # this on at the moment.
        if vm_cdrom_params['empty']:
            return "none"
        else:
            return "iso"

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

    def poweron(self):
        # Safety check.
        if self.vm_ref is None:
            self.module.fail_json(msg="Called poweron on non existing VM!")

        changed_state = False

        try:
            # First check the current state of the VM.
            vm_power_state = self.vm_params['power_state'].lower()

            # Support for ansible check mode.
            if vm_power_state != "running" and self.module.check_mode:
                return True

            # VM can be in either halted, suspended, paused or running state.
            # For VM to be in running state, start has to be called on halted,
            # resume on suspended and unpause on paused VM. If VM is already
            # in running state, we don't do anything.
            if vm_power_state == "halted":
                self.xapi_session.xenapi.VM.start(self.vm_ref, False, False)
                self.vm_params['power_state'] = "running"
                changed_state = True
            elif vm_power_state == "suspended":
                self.xapi_session.xenapi.VM.resume(self.vm_ref, False, False)
                self.vm_params['power_state'] = "running"
                changed_state = True
            elif vm_power_state == "paused":
                self.xapi_session.xenapi.VM.unpause(self.vm_ref)
                self.vm_params['power_state'] = "running"
                changed_state = True
        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

        return changed_state

    def poweroff(self):
        # Safety check.
        if self.vm_ref is None:
            self.module.fail_json(msg="Called poweroff on non existing VM!")

        changed_state = False

        try:
            # First check the current state of the VM.
            vm_power_state = self.vm_params['power_state'].lower()

            # Support for ansible check mode.
            if vm_power_state != "halted" and self.module.check_mode:
                return True

            # hard_shutdown will halt VM regardless of current state.
            if vm_power_state != "halted":
                self.xapi_session.xenapi.VM.hard_shutdown(self.vm_ref)
                self.vm_params['power_state'] = "halted"
                changed_state = True
        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

        return changed_state

    def restart(self):
        # Safety check.
        if self.vm_ref is None:
            self.module.fail_json(msg="Called restart on non existing VM!")

        changed_state = False

        try:
            # First check the current state of the VM.
            vm_power_state = self.vm_params['power_state'].lower()

            # Support for ansible check mode.
            if vm_power_state in ["paused", "running"] and self.module.check_mode:
                return True

            # hard_restart will restart VM regardless of current state.
            if vm_power_state in ["paused", "running"]:
                self.xapi_session.xenapi.VM.hard_reboot(self.vm_ref)
                self.vm_params['power_state'] = "running"
                changed_state = True
            else:
                self.module.fail_json(msg="Cannot restart VM in state '%s'!" % vm_power_state)
        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

        return changed_state

    def shutdownguest(self):
        # Safety check.
        if self.vm_ref is None:
            self.module.fail_json(msg="Called shutdownguest on non existing VM!")

        changed_state = False

        try:
            # First check the current state of the VM.
            vm_power_state = self.vm_params['power_state'].lower()

            # Support for ansible check mode.
            if vm_power_state == "running" and self.module.check_mode:
                return True

            # running state is required for guest shutdown.
            if vm_power_state == "running":
                if self.module.params['state_change_timeout'] == 0:
                    self.xapi_session.xenapi.VM.clean_shutdown(self.vm_ref)
                else:
                    task_ref = self.xapi_session.xenapi.Async.VM.clean_shutdown(self.vm_ref)
                    task_result = wait_for_task(self.module, task_ref, self.module.params['state_change_timeout'])

                    if task_result:
                        self.module.fail_json(msg="Guest shutdown task failed - '%s'!" % task_result)

                self.vm_params['power_state'] = "halted"
                changed_state = True
            else:
                self.module.fail_json(msg="VM must be in running state for guest shutdown! Current VM state is '%s'." % vm_power_state)
        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

        return changed_state

    def rebootguest(self):
        # Safety check.
        if self.vm_ref is None:
            self.module.fail_json(msg="Called rebootguest on non existing VM!")

        changed_state = False

        try:
            # First check the current state of the VM.
            vm_power_state = self.vm_params['power_state'].lower()

            # Support for ansible check mode.
            if vm_power_state == "running" and self.module.check_mode:
                return True

            # running state is required for guest reboot.
            if vm_power_state == "running":
                if self.module.params['state_change_timeout'] == 0:
                    self.xapi_session.xenapi.VM.clean_reboot(self.vm_ref)
                else:
                    task_ref = self.xapi_session.xenapi.Async.VM.clean_reboot(self.vm_ref)
                    task_result = wait_for_task(self.module, task_ref, self.module.params['state_change_timeout'])

                    if task_result:
                        self.module.fail_json(msg="Guest reboot task failed - '%s'!" % task_result)

                changed_state = True
            else:
                self.module.fail_json(msg="VM must be in running state for guest reboot! Current VM state is '%s'." % vm_power_state)
        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

        return changed_state

    def suspend(self):
        # Safety check.
        if self.vm_ref is None:
            self.module.fail_json(msg="Called suspend on non existing VM!")

        changed_state = False

        try:
            # First check the current state of the VM.
            vm_power_state = self.vm_params['power_state'].lower()

            # Support for ansible check mode.
            if vm_power_state == "running" and self.module.check_mode:
                return True

            # running state is required for guest reboot.
            if vm_power_state == "running":
                self.xapi_session.xenapi.VM.suspend(self.vm_ref)
                self.vm_params['power_state'] = "suspended"
                changed_state = True
            else:
                self.module.fail_json(msg="Cannot suspend VM in state '%s'!" % vm_power_state)
        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)

        return changed_state

    def wait_for_ip_address(self):
        # Safety check.
        if self.vm_ref is None:
            self.module.fail_json(msg="Called wait_for_ip_address on non existing VM!")

        vm_power_state = self.vm_params['power_state'].lower()

        if vm_power_state != 'running':
            self.module.fail_json(msg="VM must be in running state to wait for IP address! Current VM state is '%s'." % vm_power_state)

        interval = 2

        if self.module.params['state_change_timeout'] == 0:
            timeout = 1
        else:
            timeout = self.module.params['state_change_timeout']

        try:
            while timeout > 0:
                vm_guest_metrics_ref = self.xapi_session.xenapi.VM.get_guest_metrics(self.vm_ref)

                if vm_guest_metrics_ref != "OpaqueRef:NULL":
                    vm_ips = self.xapi_session.xenapi.VM_guest_metrics.get_networks(vm_guest_metrics_ref)

                    if "0/ip" in vm_ips:
                        # We update guest_metrics in vm_params so that
                        # gather_facts() have fresh params.
                        self.vm_params['guest_metrics'] = self.xapi_session.xenapi.VM_guest_metrics.get_record(vm_guest_metrics_ref)
                        break

                time.sleep(interval)

                if self.module.params['state_change_timeout'] != 0:
                    timeout -= interval
            else:
                # We timed out.
                self.module.fail_json(msg="Timed out waiting for IP address!")

        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)


def main():
    argument_spec = xenserver_common_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present',
                   choices=['absent', 'poweredoff', 'poweredon', 'present', 'rebootguest', 'restarted', 'shutdownguest', 'suspended']),
        name=dict(type='str', aliases=['name_label']),
        name_desc=dict(type='str'),
        uuid=dict(type='str'),
        template=dict(type='str', aliases=['template_src']),
        template_uuid=dict(type='str'),
        is_template=dict(type='bool', default=False),
        folder=dict(type='str'),
        hardware=dict(type='dict', default={}),
        disks=dict(type='list', default=[], aliases=['disk']),
        cdrom=dict(type='dict', default={}),
        networks=dict(type='list', default=[], aliases=['network']),
        home_server=dict(type='str'),
        custom_params=dict(type='list', default=[]),
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

            if module.check_mode:
                result['changes'] = config_changes

            result['instance'] = vm.gather_facts()
        elif module.params['state'] == "poweredon":
            changed = vm.poweron()
            result['changed'] = changed
        elif module.params['state'] == "poweredoff":
            changed = vm.poweroff()
            result['changed'] = changed
        elif module.params['state'] == "restarted":
            changed = vm.restart()
            result['changed'] = changed
        elif module.params['state'] == "shutdownguest":
            changed = vm.shutdownguest()
            result['changed'] = changed
        elif module.params['state'] == "rebootguest":
            changed = vm.rebootguest()
            result['changed'] = changed
        elif module.params['state'] == "suspended":
            changed = vm.suspend()
            result['changed'] = changed
    elif module.params['state'] != "absent":
        vm.deploy()
        result['changed'] = True

    if module.params['wait_for_ip_address']:
        vm.wait_for_ip_address()

    result['instance'] = vm.gather_facts()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)

if __name__ == '__main__':
    main()
