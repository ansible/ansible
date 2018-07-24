#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vmware_guest_nic_manager
short_description: Manages virtual machines in vCenter
description: >
   This module can be used to configure VNICs on virtual machines,
   manage NIC state as connect , disconnect or delete.
version_added: '2.4'
author:
- Mohd Umar Mubeen (@mohdumar321) <umar.shiats@gmail.com>
requirements:
- python >= 2.6
- PyVmomi
- tools
notes:
    - Please make sure the user used for vmware_guest should have correct level of privileges.
    - For example, following is the list of minimum privileges required by users to create virtual machines.
    - "   DataStore > Allocate Space"
    - "   Virtual Machine > Configuration > Add New Disk"
    - "   Virtual Machine > Configuration > Add or Remove Device"
    - "   Virtual Machine > Inventory > Create New"
    - "   Network > Assign Network"
    - "   Resource > Assign Virtual Machine to Resource Pool"
    - "Module may require additional privileges as well, which may be required for gathering facts - e.g. ESXi configurations."
    - "For additional information please visit Ansible VMware community wiki - U(https://github.com/ansible/community/wiki/VMware)."
options:
  nic_state:
    description:
    - Specify state of the virtual machine be in.
    - 'If C(nic_state) is set to C(connect) and virtual machine exists, nic will be connected'
    - 'If C(nic_state) is set to C(disconnect) and virtual machine exists, then the specified virtual machine nic
      is disconnected from virtual machine.'
    - 'If C(nic_state) is set to C(delete) and virtual machine  exists, tthen the specified virtual machine nic
      is deleted from virtual machine.'
    default: connect
    choices: [ connect, disconnect , delete ]
  name:
    description:
    - Name of the virtual machine to work with.
    - This parameter is case sensitive.
    required: yes
  uuid:
    description:
    - UUID of the virtual machine to manage if known, this is VMware's unique identifier.
    - This is required if C(name) is not supplied.
    - If virtual machine does not exists, then this parameter is ignored.
    - Please note that a supplied UUID will be ignored on virtual machine creation, as VMware creates the UUID internally.
  
'''
EXAMPLES = '''
- name: configure the NIC's
  vmware_guest_nic_manager:
      hostname: "{{hostname}}" 
      username: "{{username}}"
      validate_certs: false
      password: "{{password}}"
      port: "{{port}}"
      name: "{{name}}"      
      uuid: "{{uuid}}"
      nic_state: "{{nic_state}}"
      nic_number: "{{nic_number}}"
'''
RETURN = r'''
instance:
    description: metadata about the virtual machine
    returned: always
    type: dict
    sample: None
'''



import atexit
import requests
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
from tools import tasks
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.vmware import (find_obj, gather_vm_facts, get_all_objs,
                                         compile_folder_path_for_object, serialize_spec,
                                         vmware_argument_spec, set_vm_power_state, PyVmomi,
                                         find_dvs_by_name, find_dvspg_by_name)

# disable  urllib3 warnings
if hasattr(requests.packages.urllib3, 'disable_warnings'):
    requests.packages.urllib3.disable_warnings

def update_virtual_nic_state(si, vm_obj, nic_number, new_nic_state):

    nic_prefix_label = 'Network adapter '
    nic_label = nic_prefix_label + str(nic_number)
    virtual_nic_device = None
    for dev in vm_obj.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard) \
                and dev.deviceInfo.label == nic_label:
            virtual_nic_device = dev
    if not virtual_nic_device:
        raise RuntimeError('Virtual {} could not be found.'.format(nic_label))

    virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
    virtual_nic_spec.operation = \
        vim.vm.device.VirtualDeviceSpec.Operation.remove \
        if new_nic_state == 'delete' \
        else vim.vm.device.VirtualDeviceSpec.Operation.edit
    virtual_nic_spec.device = virtual_nic_device
    virtual_nic_spec.device.key = virtual_nic_device.key
    virtual_nic_spec.device.macAddress = virtual_nic_device.macAddress
    virtual_nic_spec.device.backing = virtual_nic_device.backing
    virtual_nic_spec.device.wakeOnLanEnabled = \
        virtual_nic_device.wakeOnLanEnabled
    connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    if new_nic_state == 'connect':
        connectable.connected = True
        connectable.startConnected = True
    elif new_nic_state == 'disconnect':
        connectable.connected = False
        connectable.startConnected = False
    else:
        connectable = virtual_nic_device.connectable
    virtual_nic_spec.device.connectable = connectable
    dev_changes = []
    dev_changes.append(virtual_nic_spec)
    spec = vim.vm.ConfigSpec()
    spec.deviceChange = dev_changes
    task = vm_obj.ReconfigVM_Task(spec=spec)
    tasks.wait_for_tasks(si, [task])
    return True


def get_args():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(hostname=dict(type='str' , required=True), 
                              username=dict(type='str' , required=True), 
                              password=dict(type='str' , required=True), 
                              port=dict(type='int' , default='443'), 
                              name=dict(type='str' , required=True), 
                              uuid=dict(type='str' , required=True), 
                              nic_state=dict(type='str' , default='connect', choices=['connect', 'disconnect' , 'delete']),
                              nic_number=dict(type='str')))
    module = AnsibleModule(argument_spec=argument_spec)
    return module


def get_obj(content, vim_type, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vim_type, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def main():
    args = get_args()

    # connect to vc
    si = SmartConnect(
        host=args.params['hostname'],
        user=args.params['username'],
        pwd=args.params['password'],
        port=args.params['port'])
    # disconnect vc
    atexit.register(Disconnect, si)

    content = si.RetrieveContent()
    vm_obj = get_obj(content, [vim.VirtualMachine], args.params['name'])

    if vm_obj:
       
        update_virtual_nic_state(si, vm_obj, args.params['nic_number'], args.params['nic_state'])
        msg = ('VM NIC {} successfully' \
              ' state changed to {}').format(args.params['nic_number'], args.params['nic_state'])
        args.exit_json(msg=msg ,changed=True)
    else:
        msg = ("VM not found")
        args.fail_json(msg=msg ,changed=False)
# start
if __name__ == "__main__":
    main()
