#!/bin/python

DOCUMENTATION = '''
---
module: vmware_nic
short_description: Create, Update, or Remove a NIC from a VM
description:
     - Allows non-idempotent creation of VMs. Updates and removals are idempotent.
options:
  vm_path:
    description:
      - The fully qualified path of the VM such as /SomeFolder/SubFolder/VMname
    required: true
  label:
    description:
      - The label of the NIC you want to update or remove. This has no effect when trying to
        create a NIC due to a limitation in VMWare's API 
    required: false
  dvs:
    description:
      - Whether the NICs network should be standard or DVS. 
    default: false 
  state:
    description:
      - The action desired. If 'create', a new NIC will be created everytime. Update will check
        if a NIC with the same label exists, if it does then it will verify that the current network
        matches the settings supplied in the task.
    required: True
  type:
    description:
      - The type of NIC you wish to create 
    required: false
    default: vmxnet3 
    choices: ['vmxnet','vmxnet2','vmxnet3','e1000','e1000e','pcnet32']
  network_name:
    description:
      - The name label of the network you wish to associate the NIC with. 
        Valid for create and update states.
    required: False
  datacenter:
    description:
      - The datacenter name in which the VM resides
    required: True 
notes:
  - This module should run from a system that can access vSphere directly.
    Either by using local_action, or using delegate_to. 
author: "Jonathan Davila <jdavila@redhat.com>"
requirements:
  - "python >= 2.6"
  - pyvmomi
'''


EXAMPLES = '''
# Update the NIC 'Network adapter 1' on the 'SharekVM1' VM inside of /sharks/megladon/ 
# within the Ocean datacenter 

- name: Update NIC
  vmware_nic:
      vm_path: /sharks/megladon/SharkVM1
      state: update
      hostname: vcenter.domain.local
      username: administrator
      password: password
      datacenter: Ocean
      network_name: Servers
      label: Network adapter 1

# Create a new vmxnet3 NIC, associate with Servers network, and attach to SharkVM1.  
- name: Create NIC
  vmware_nic:
      vm_path: /sharks/megladon/SharkVM1
      state: create
      hostname: vcenter.domain.local
      username: administrator
      password: password
      datacenter: Ocean
      network_name: Servers
      type: vmxnet3
'''


try:
    from pyVmomi import vim
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def get_obj_by_name(content, vimtype, name):
    """
     Get the vsphere object associated with a given text name
    """    
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def objwalk(obj, path_elements):
    if hasattr(obj, 'parent'):
        new_obj = getattr(obj, 'parent')
        if new_obj:
            if new_obj.name != 'vm':
                # 'vm' is an invisible folder that exists at the datacenter root so we ignore it
                path_elements.append(new_obj.name)
            
            objwalk(new_obj, path_elements)

    return path_elements


def get_vm_object(module, conn, path, datacenter):

    all_vms = get_all_objs(conn, [vim.VirtualMachine])
    matching_vms = []
    path_list = filter(None, path.split('/'))
    name = path_list.pop()

    for vm_obj, label in all_vms.iteritems():
        if label == name:
            matching_vms.append(vm_obj)

    try:
        if len(matching_vms) > 1:
            
            for vm_obj in matching_vms:
                elements = []
                if set(path_list).issubset(set(objwalk(vm_obj, elements))):
                    return vm_obj

        elif len(matching_vms) == 0:
            module.fail_json(msg="VM: %s not found at path: %s" % (name, path))
        
        else:
            return matching_vms[0]

    except TypeError:
        module.fail_json(msg="Virtual Machine %s was not found inside datacenter: %s at path: %s" % (name, datacenter, path))


def get_nics(vm_obj):
    nics = []

    for device in vm_obj.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            nics.append(dict(
                network=device.deviceInfo.summary,
                type=device.__class__.__name__,
                key=device.key,
                label=device.deviceInfo.label,
                nic_obj=device
                ))

    return nics


def create_nic(module, conn, vm, desired_nic):
    vm_spec = vim.vm.ConfigSpec()
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    changes = []

    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic_spec.device = getattr(vim.vm.device, desired_nic['type'])()

    if desired_nic['dvs']:
        pg_obj = get_obj_by_name(conn, [vim.dvs.DistributedVirtualPortgroup], desired_nic['network'])
        dvs_port_connection = vim.dvs.PortConnection()
        dvs_port_connection.portgroupKey= pg_obj.key
        dvs_port_connection.switchUuid= pg_obj.config.distributedVirtualSwitch.uuid
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        nic_spec.device.backing.port = dvs_port_connection
    else:
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.network = get_obj_by_name(conn, [vim.Network], desired_nic['network'])
    
    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.connected = True
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.allowGuestControl = True
    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.deviceInfo.summary = desired_nic['network']     
    nic_spec.device.backing.deviceName = desired_nic['network']
    nic_spec.device.addressType = 'generated'


    # The two below do not work, label and key, they are ignored by the API
    # nic_spec.device.deviceInfo.label = desired_nic['label']
    # nic_spec.device.key = desired_nic['id']

    changes.append(nic_spec)
    vm_spec.deviceChange = changes
    task = vm.ReconfigVM_Task(spec=vm_spec)

    success, result = wait_for_task(task)

    if success:
        return desired_nic
    else:
        module.fail_json(msg="Failed to create nic: %s" % result)


def remove_nic(module, conn, vm, desired_nic, all_nics):
    vm_spec = vim.vm.ConfigSpec()
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    changes = []
    nic_obj = None
    matching_nics = []

    for nic in all_nics:
        if nic['nic_obj'].deviceInfo.label == desired_nic['label']:
            matching_nics.append(nic['nic_obj'])

    if len(matching_nics) == 1:
        nic_obj = matching_nics[0]
    elif len(matching_nics) > 1:
        module.fail_json(msg="One or more NICs with the label: %s have been found. You'll have to remove the proper NIC manually" % desired_nic['label'])
    elif len(matching_nics) == 0:
        module.exit_json(msg="No NIC with the name: %s was found" % desired_nic['label'])
    
    nic_obj = matching_nics[0]

    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
    nic_spec.device = nic_obj
    changes.append(nic_spec)
    vm_spec.deviceChange = changes
    task = vm.ReconfigVM_Task(spec=vm_spec)
    success, result = wait_for_task(task)

    if success:
        return desired_nic
    else:
        module.fail_json(msg="Failed to remove nic: %s" % result)


def update_nic(module, conn, vm, desired_nic, all_nics):
    vm_spec = vim.vm.ConfigSpec()
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    changes = []
    nic_obj = None
    matching_nics = []

    for nic in all_nics:
        if nic['nic_obj'].deviceInfo.label == desired_nic['label']:
            matching_nics.append(nic['nic_obj'])

    if len(matching_nics) == 1:
        nic_obj = matching_nics[0]
    elif len(matching_nics) > 1:
        module.fail_json(msg="One or more NICs with the label: %s have been found. You'll have to update the proper NIC manually. Or ensure the NICs have unique labels and try again." % desired_nic['label'])
    elif len(matching_nics) == 0:
        module.fail_json(msg="No NIC with the name: %s was found" % desired_nic['label'])

    nic_obj = matching_nics[0]

    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    nic_spec.device = nic_obj
    nic_spec.device.key = nic_obj.key
    nic_spec.device.macAddress = nic_obj.macAddress

    if desired_nic['dvs']:
        pg_obj = get_obj_by_name(conn, [vim.dvs.DistributedVirtualPortgroup], desired_nic['network'])
        dvs_port_connection = vim.dvs.PortConnection()
        dvs_port_connection.portgroupKey= pg_obj.key
        dvs_port_connection.switchUuid= pg_obj.config.distributedVirtualSwitch.uuid
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        nic_spec.device.backing.port = dvs_port_connection
    else:
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.network = get_obj_by_name(conn, [vim.Network], desired_nic['network'])
    
    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.connected = True
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.allowGuestControl = True
    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.deviceInfo.summary = desired_nic['network']     
    nic_spec.device.backing.deviceName = desired_nic['network']

    changes.append(nic_spec)
    vm_spec.deviceChange = changes
    task = vm.ReconfigVM_Task(spec=vm_spec)
    success, result = wait_for_task(task)

    if success:
        return desired_nic
    else:
        module.fail_json(msg="Failed to update nic: %s" % result)


def needs_update(module, desired_nic, all_nics):
    nic_obj = None
    all_nic_labels = []
    matching_nics = []

    for nic in all_nics:
        all_nic_labels.append(nic['nic_obj'].deviceInfo.label)

        if nic['nic_obj'].deviceInfo.label == desired_nic['label']:
            matching_nics.append(nic['nic_obj'])

    if len(matching_nics) == 1:
        nic_obj = matching_nics[0]
    elif len(matching_nics) > 1:
        module.fail_json(msg="One or more NICs with the label: %s have been found. You'll have to update the proper NIC manually. Or ensure the NICs have unique labels and try again." % desired_nic['label'])
    elif len(matching_nics) == 0:
        module.fail_json(msg="No NIC with the name: %s was found. Found: %s " % (desired_nic['label'], all_nic_labels))


    if nic_obj.backing.deviceName == desired_nic['network']:
        if desired_nic['dvs']:
            if 'Distrubted' in nic_obj.backing.__class__.__name__:
                return False
            else:
                pass
        else:
            if 'Network' in nic_obj.backing.__class__.__name__:
                return False
            else:
                pass

    return True


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
                vm_path=dict(required=True, type='str'),
                label=dict(required=False, type='str'),
                dvs=dict(required=False, type='bool', default=False),
                state=dict(required=True, choices=['create', 'absent', 'update'], type='str'),
                type=dict(required=False, type='str', default='vmxnet3', choices=['vmxnet','vmxnet2','vmxnet3','e1000','e1000e','pcnet32']),
                network_name=dict(required=False, type='str'),
                datacenter=dict(required=True, type='str'),
                )
        )
    
    module = AnsibleModule(argument_spec=argument_spec,
			required_if= [('state','create',['network_name']),
			              ('state','update',['network_name','label']),
			              ('state','absent',['label'])]
			)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    path = module.params.get('vm_path')
    label = module.params.get('label')
    dvs = module.params.get('dvs')
    network_name = module.params.get('network_name')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    nic_type = module.params.get('type')

    changed = False

    conn = connect_to_api(module)
    proper_vm = get_vm_object(module, conn, path, datacenter)
    all_nics = get_nics(proper_vm)

    nic_type_map = dict(
        vmxnet3 = 'VirtualVmxnet3',
        vmxnet2 = 'VirtualVmxnet2',
        vmxnet  = 'VirtualVmxnet',
        e1000   = 'VirtualE1000',
        e1000e  = 'VirtualE1000e',
        pcnet32 = 'VirtualPCNet32'
        )

    desired_nic = dict(
        network=network_name,
        type=nic_type_map[nic_type],
        dvs=dvs,
        label=label
        )

    if state == 'create':
        changed = True
        pre_nics = [nic['nic_obj'] for nic in all_nics]
        results = create_nic(module, conn, proper_vm, desired_nic)
        new_nics_list = [nic['nic_obj'] for nic in get_nics(proper_vm)]
        new_nic = set(new_nics_list).difference(pre_nics)
        nic = new_nic.pop()
        module.exit_json(changed=changed, nic=dict(label=nic.deviceInfo.label,
                                                   key=nic.key,
                                                   network=nic.backing.deviceName
                                                   )
        )
    
    elif state == 'absent':
        changed = True
        results = remove_nic(module, conn, proper_vm, desired_nic, all_nics)

        module.exit_json(changed=changed, msg="NIC removed")
    
    elif state == 'update':
        if needs_update(module, desired_nic, all_nics):
            changed=True
            update_nic(module, conn, proper_vm, desired_nic, all_nics)
        else:
            changed=False

        module.exit_json(changed=changed)



from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *

if __name__ == '__main__':
    main()
