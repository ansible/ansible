#!/usr/bin/env python

import atexit
import requests
from tools import cli
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
from tools import tasks
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.vmware import (find_obj, gather_vm_facts, get_all_objs, compile_folder_path_for_object, serialize_spec,vmware_argument_spec, set_vm_power_state, PyVmomi)

# disable  urllib3 warnings
if hasattr(requests.packages.urllib3, 'disable_warnings'):
    requests.packages.urllib3.disable_warnings()


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
    argument_spec.update(dict(hostname=dict(type='str', required=True),
                              username=dict(type='str', required=True),
                              password=dict(type='str', required=True),
                              port=dict(type='int', default='443'),
                              name=dict(type='str', required=True),
                              uuid=dict(type='str', required=True),
                              nic_state=dict(type='str'),
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
    print ('Searching for VM {}').format(args.params['name'])
    vm_obj = get_obj(content, [vim.VirtualMachine], args.params['name'])

    if vm_obj:
        update_virtual_nic_state(si, vm_obj, args.params['nic_number'], args.params['nic_state'])
        print ('VM NIC {} successfully' \
              ' state changed to {}').format(args.params['nic_number'], args.params['nic_state'])
    else:
        print ("VM not found")
# start
if __name__ == "__main__":
    main()
