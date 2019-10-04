#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Anusha Hegde <anushah@vmware.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_serial_port

short_description: Create a serial port

version_added: "1.0"

description:
    - "Creates a serial port on an existing VM"

options:
    hostname:
        description:
            - The host name or IP of the VCenter Server
        required: true
    username:
        description:
            - Username required to login to the VCenter Server
        required: true
    password:
        description:
            - Password required to login to the VCenter Server
        required: true
    name:
        description:
            - The name of the Virtual Machine
        type: str
    vm_id:
        description:
            - The id of the Virtual Machine
        type: str
    uuid:
        description:
            - The UUID of the Virtual Machine
        type: str
    backing:
        description:
            - A virtual serial port uses one of the following backing types to specify how the virtual machine performs serial port operations
        type: str
        choices:
            - network
            - pipe
            - file
            - device
        required: true
    pipe_name:
        description:
            - Pipe name
            - Required when I(backing=pipe)
        type: str
    device_name:
        description:
            - Device name
            - Required when I(backing=device)
        type: str
    file_path:
        description:
            - File path for the host file used in this backing
            - Required when I(backing=file)
        type: str
    direction:
        description:
            - The direction of the connection
            - Required when I(backing=network)
        type: str
        choices:
            - client
            - server
    endpoint:
        description:
            - When you use serial port pipe backing to connect a virtual machine to another process, you must define the endpoints
            - Required when I(backing=pipe)
        type: str
        choices:
            - client
            - server
    service_uri:
        description:
            - Identifies the local host or a system on the network, depending on the value of I(direction)
            - If you use the virtual machine as a server, the URI identifies the host on which the virtual machine runs. In this case, the host name part of the URI should be empty, or it should specify the address of the local host
            - If you use the virtual machine as a client, the URI identifies the remote system on the network
            - Required when I(backing=network)
        type: str
    proxy_uri:
        description:
            - Identifies a proxy service that provides network access to the I(serviceURI)
            - If you specify a proxy URI, the virtual machine initiates a connection with the proxy service and forwards the I(serviceURI) and I(direction) to the proxy
            - Required when I(backing=network)
        type: str
    yield_on_poll:
        description:
            - Enables CPU yield behavior
        type: bool
        default: true
    no_rx_loss:
        description:
            - Enables optimized data transfer over the pipe
            - Optional when I(backing=pipe)
        type: bool
    force:
        description:
            - Forcefully power off the VM before creating a serial port
        type: bool
        default: false

extends_documentation_fragment:
    - vmware.documentation

author:
    - Anusha Hegde (@anusha94)
'''

EXAMPLES = '''
# Create serial ports
- name: Network backing type
  vmware_serial_port:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    name: '{{ name }}'
    backing: network
    service_uri: 'service_uri'
    direction: client
    yield_on_poll: true
  delegate_to: localhost

- name: Pipe backing type
  vmware_serial_port:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    name: '{{ name }}'
    backing: 'pipe'
    pipe_name: 'pipe_name'
    endpoint: client
    yield_on_poll: true
    no_rx_loss: true
  delegate_to: localhost

- name: Device backing type
  vmware_serial_port:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    name: '{{ name }}'
    backing: 'device'
    device_name: 'device_name'
    yield_on_poll: true
  delegate_to: localhost

- name: File backing type
  vmware_serial_port:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    name: '{{ name }}'
    backing: file
    file_path: 'file_path'
    yield_on_poll: true
  delegate_to: localhost

'''

RETURN = r'''
#
'''

import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, set_vm_power_state, wait_for_task, gather_vm_facts
from pyVmomi import vim


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.change_applied = False   # a change was applied meaning at least one task succeeded

    def check_vm_state(self, vm):
        """
        To add serial port, the VM must be in powered off state

        Input:
          - vm: Virtual Machine

        Output:
          - [proceed, current_state]
        """
        facts = gather_vm_facts(self.content, vm)
        current_state = facts['hw_power_status'].lower()
        if current_state == "poweredoff":
            return [True, current_state]
        elif self.params.get('force'):
            set_vm_power_state(self.content, vm, 'poweredoff', True)
            return [True, current_state]
        else:
            return [False, current_state]

    def create_serial_port(self, vm):
        """
        Input:
          - vm: Virtual Machine Object

        Return:
          - result object

        """
        spec = vim.vm.ConfigSpec()
        spec.deviceChange = []
        serial_spec = vim.vm.device.VirtualDeviceSpec()
        serial_spec.operation = 'add'
        serial_port = vim.vm.device.VirtualSerialPort()
        serial_port.yieldOnPoll = True
        serial_port.backing = self.get_backing_info(serial_port, self.params.get('backing'))
        serial_spec.device = serial_port
        spec.deviceChange.append(serial_spec)
        task = vm.ReconfigVM_Task(spec=spec)
        self.wait_for_task(task)
        if task.info.state == 'error':
            return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg}
        else:
            return {'changed': self.change_applied, 'failed': False, 'msg': "Serial port successfully created"}

    def wait_for_task(self, task, poll_interval=1):
        """
        Wait for a VMware task to complete.  Terminal states are 'error' and 'success'.

        Inputs:
          - task: the task to wait for
          - poll_interval: polling interval to check the task, in seconds

        Modifies:
          - self.change_applied
        """
        while task.info.state not in ['error', 'success']:
            time.sleep(poll_interval)
        self.change_applied = self.change_applied or task.info.state == 'success'

    def get_backing_info(self, serial_port, backing):
        switcher = {
            "network": self.set_network_backing,
            "pipe": self.set_pipe_backing,
            "device": self.set_device_backing,
            "file": self.set_file_backing
        }
        backing_func = switcher.get(backing, "Invalid Backing Info")
        return backing_func(serial_port)

    def set_network_backing(self, serial_port):
        backing = serial_port.URIBackingInfo()
        backing.serviceURI = self.params.get('service_uri')
        backing.direction = self.params.get('direction')
        backing.proxyURI = self.params.get('proxy_uri')
        return backing

    def set_pipe_backing(self, serial_port):
        backing = serial_port.PipeBackingInfo()
        backing.pipeName = self.params.get('pipe_name')
        backing.endpoint = self.params.get('endpoint')
        backing.noRxLoss = self.params.get('no_rx_loss')
        return backing

    def set_device_backing(self, serial_port):
        backing = serial_port.DeviceBackingInfo()
        backing.deviceName = self.params.get('device_name')
        return backing

    def set_file_backing(self, serial_port):
        backing = serial_port.FileBackingInfo()
        backing.fileName = self.params.get('file_path')
        return backing


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        uuid=dict(type='str'),
        vm_id=dict(type='str'),
        backing=dict(type='str', choices=['network', 'file', 'pipe', 'device']),
        service_uri=dict(type='str'),
        proxy_uri=dict(type='str'),
        yield_on_poll=dict(type='bool', default=True),
        no_rx_loss=dict(type='bool'),
        name=dict(type='str'),
        pipe_name=dict(type='str'),
        device_name=dict(type='str'),
        file_path=dict(type='str'),
        direction=dict(type='str', choices=['client', 'server']),
        endpoint=dict(type='str', choices=['client', 'server']),
        force=dict(type='bool', default=False)
        )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'uuid', 'vm_id']
        ]
    )
    result = {'failed': False, 'changed': False}

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    print("checking vm")
    vm = pyv.get_vm()

    if vm:
        print("creating port")
        proceed, current_state = pyv.check_vm_state(vm)
        if proceed:
            result = pyv.create_serial_port(vm)
        else:
            module.fail_json(msg="The attempted operation cannot be performed in the current state (" + current_state + "), use the force option to forcefully power off the VM")
            '''
            result.update(
                failed=True,
                msg="The attempted operation cannot be performed in the current state, use the force option to forcefully power off the VM"
            )
            '''

    else:
        # We are unable to find the virtual machine user specified
        # Bail out
        vm_id = (module.params.get('name') or module.params.get('uuid') or module.params.get('vm_id'))
        module.fail_json(msg="Unable to manage serial ports for non-existing"
                             " virtual machine '%s'." % vm_id)

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
