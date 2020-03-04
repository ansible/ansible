#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Anusha Hegde <anushah@vmware.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_guest_serial_port

short_description: Manage serial ports on an existing VM

version_added: "2.10"

description:
  - "This module can be used to manage serial ports on an existing VM"

options:
  name:
    description:
      - Name of the virtual machine.
      - This is a required parameter, if parameter C(uuid) or C(moid) is not supplied.
    type: str
  uuid:
    description:
      - UUID of the instance to manage the serial ports, this is VMware's unique identifier.
      - This is a required parameter, if parameter C(name) or C(moid) is not supplied.
    type: str
  moid:
    description:
      - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
      - This is required if C(name) or C(uuid) is not supplied.
    type: str
  use_instance_uuid:
    description:
      - Whether to use the VMware instance UUID rather than the BIOS UUID.
    default: no
    type: bool
  backings:
    type: list
    description:
      - A list of backings for serial ports.
      - 'C(backing_type) (str): is required to add or reconfigure or remove an existing serial port.'
      - 'Valid attributes are:'
      - ' - C(backing_type) (str): Backing type is required for the serial ports to be added or reconfigured or removed.'
      - ' - C(state) (str): is required to identify whether we are adding, modifying or removing the serial port.
            - choices:
              - C(present): modify an existing serial port. C(backing_type) is required to determine the port.
                The first matching C(backing_type) and either of C(service_uri) or C(pipe_name) or C(device_name) or C(file_path) will be modified.
                If there is only one device with a backing type, the secondary details are not needed.
                We will match the last such device with the given backing type.
              - C(absent): remove an existing serial port. C(backing_type) is required to determine the port.
                The first matching C(backing_type) and either of C(service_uri) or C(pipe_name) or C(device_name) or C(file_path) will be removed.
                If there is only one device with a backing type, the secondary details are not needed.
                We will match the last such device with the given backing type.'
      - ' - C(yield_on_poll) (bool): Enables CPU yield behavior. Default value is true.'
      - ' - C(direction) (str): Required when I(backing_type=network).
            The direction of the connection.
            - choices:
              - client
              - server'
      - ' - C(service_uri) (str): Required when I(backing_type=network).
            Identifies the local host or a system on the network, depending on the value of I(direction).
            If you use the virtual machine as a server, the URI identifies the host on which the virtual machine runs.
                In this case, the host name part of the URI should be empty, or it should specify the address of the local host.
            If you use the virtual machine as a client, the URI identifies the remote system on the network.'
      - ' - C(endpoint) (str): Required when I(backing_type=pipe).
            When you use serial port pipe backing to connect a virtual machine to another process, you must define the endpoints.'
      - ' - C(no_rx_loss) (bool): Required when I(backing_type=pipe).
            Enables optimized data transfer over the pipe.
            - choices:
              - client
              - server'
      - ' - C(pipe_name) (str): Required when I(backing_type=pipe).'
      - ' - C(device_name) (str): Required when I(backing_type=device).'
      - ' - C(file_path) (str): Required when I(backing_type=file).
            File path for the host file used in this backing. Fully qualified path is required, like <datastore_name>/<file_name>'

extends_documentation_fragment:
  - vmware.documentation

author:
  - Anusha Hegde (@anusha94)
'''

EXAMPLES = '''
# Create serial ports
- name: Create multiple serial ports with Backing type - network, pipe, device and file
  vmware_guest_serial_port:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    name: "test_vm1"
    backings:
    - type: 'network'
      direction: 'client'
      service_uri: 'tcp://6000'
      yield_on_poll: True
    - type: 'pipe'
      pipe_name: 'serial_pipe'
      endpoint: 'client'
    - type: 'device'
      device_name: '/dev/char/serial/uart0'
    - type: 'file'
      file_path: '[datastore1]/file1'
      yield_on_poll:  True
    register: create_multiple_ports

# Modify existing serial port
- name: Modify Network backing type
  vmware_guest_serial_port:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    name: '{{ name }}'
    backings:
    - type: 'network'
      state: 'present'
      direction: 'server'
      service_uri: 'tcp://6000'
  delegate_to: localhost

# Remove serial port
- name: Remove pipe backing type
  vmware_guest_serial_port:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    name: '{{ name }}'
    backings:
    - type: 'pipe'
      state: 'absent'
  delegate_to: localhost

'''

RETURN = r'''
serial_port_data:
    description: metadata about the virtual machine's serial ports after managing them
    returned: always
    type: dict
    sample: [
        {
          "backing_type": "network",
          "direction": "client",
          "service_uri": "tcp://6000"
        },
        {
          "backing_type": "pipe",
          "direction": "server",
          "pipe_name": "serial pipe"
        },
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task
from ansible.module_utils._text import to_native
try:
    from pyVmomi import vim
except ImportError:
    pass


class PyVmomiHelper(PyVmomi):
    """ This class is a helper to create easily VMware Spec for PyVmomiHelper """

    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.change_applied = False   # a change was applied meaning at least one task succeeded
        self.config_spec = vim.vm.ConfigSpec()
        self.config_spec.deviceChange = []
        self.serial_ports = []

    def check_vm_state(self, vm_obj):
        """
        To add serial port, the VM must be in powered off state

        Input:
          - vm: Virtual Machine

        Output:
          - True if vm is in poweredOff state
          - module fails otherwise
        """
        if vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
            return True
        else:
            self.module.fail_json(msg="A serial device cannot be added to a VM in the current state(" + vm_obj.runtime.powerState + ")."
                                  + "Please use the vmware_guest_powerstate module to power off the VM")

    def get_serial_port_config_spec(self, vm_obj):
        """
        Variables changed:
          - self.config_spec
          - self.change_applied
        """
        # create serial config spec for adding, editing, removing
        for backing in self.params.get('backings'):
            backing_keys = backing.keys()
            serial_port = get_serial_port(vm_obj, backing)
            if serial_port is None and 'state' not in backing_keys:
                # if serial port is None and state is not mentioned
                # create a new serial port
                serial_port_spec = self.create_serial_port(backing)
                serial_port_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                self.serial_ports.append(serial_port_spec)
                self.change_applied = True
            else:
                if serial_port is not None and 'state' in backing_keys:
                    serial_spec = vim.vm.device.VirtualDeviceSpec()
                    serial_spec.device = serial_port
                    if backing['state'].lower() == 'present':
                        # modify existing serial port
                        serial_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                        serial_spec.device.backing = self.get_backing_info(serial_port, backing, backing['type'])
                        self.change_applied = True
                        self.config_spec.deviceChange.append(serial_spec)
                    elif backing['state'].lower() == 'absent':
                        # remove serial port
                        serial_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
                        self.change_applied = True
                        self.config_spec.deviceChange.append(serial_spec)
                else:
                    self.module.fail_json(msg='Unable to find the specified serial port: %s' % backing)

    def reconfigure_vm_serial_port(self, vm_obj):
        """
        Reconfigure vm with new or modified serial port config spec
        """
        self.get_serial_port_config_spec(vm_obj)
        try:
            # configure create tasks first
            if self.serial_ports:
                for serial_port in self.serial_ports:
                    # each type of serial port is of config_spec.device = vim.vm.device.VirtualSerialPort() object type
                    # because serial ports differ in the backing types and config_spec.device has to be unique,
                    # we are creating a new spec for every create port configuration
                    spec = vim.vm.ConfigSpec()
                    spec.deviceChange.append(serial_port)
                    task = vm_obj.ReconfigVM_Task(spec=spec)
                    wait_for_task(task)
            task = vm_obj.ReconfigVM_Task(spec=self.config_spec)
            wait_for_task(task)
        except vim.fault.InvalidDatastorePath as e:
            self.module.fail_json(msg="Failed to configure serial port on given virtual machine due to invalid path: %s" % to_native(e.msg))
        except vim.fault.RestrictedVersion as e:
            self.module.fail_json(msg="Failed to reconfigure virtual machine due to product versioning restrictions: %s" % to_native(e.msg))
        if task.info.state == 'error':
            results = {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg}
        else:
            serial_port_info = get_serial_port_info(vm_obj)
            results = {'changed': self.change_applied, 'failed': False, 'serial_port_info': serial_port_info}

        return results

    def set_network_backing(self, serial_port, backing_info):
        """
        Set the networking backing params
        """
        required_params = ['service_uri', 'direction']
        if set(required_params).issubset(backing_info.keys()):
            backing = serial_port.URIBackingInfo()
            backing.serviceURI = backing_info['service_uri']
            backing.direction = backing_info['direction']
        else:
            self.module.fail_json(msg="Failed to create a new serial port of network backing type due to insufficient parameters."
                                  + "The required parameters are service_uri and direction")
        return backing

    def set_pipe_backing(self, serial_port, backing_info):
        """
        Set the pipe backing params
        """
        required_params = ['pipe_name', 'endpoint']
        if set(required_params).issubset(backing_info.keys()):
            backing = serial_port.PipeBackingInfo()
            backing.pipeName = backing_info['pipe_name']
            backing.endpoint = backing_info['endpoint']
        else:
            self.module.fail_json(msg="Failed to create a new serial port of pipe backing type due to insufficient parameters."
                                  + "The required parameters are pipe_name and endpoint")

        # since no_rx_loss is an optional argument, so check if the key is present
        if 'no_rx_loss' in backing_info.keys() and backing_info['no_rx_loss']:
            backing.noRxLoss = backing_info['no_rx_loss']
        return backing

    def set_device_backing(self, serial_port, backing_info):
        """
        Set the device backing params
        """
        required_params = ['device_name']
        if set(required_params).issubset(backing_info.keys()):
            backing = serial_port.DeviceBackingInfo()
            backing.deviceName = backing_info['device_name']
        else:
            self.module.fail_json(msg="Failed to create a new serial port of device backing type due to insufficient parameters."
                                  + "The required parameters are device_name")
        return backing

    def set_file_backing(self, serial_port, backing_info):
        """
        Set the file backing params
        """
        required_params = ['file_path']
        if set(required_params).issubset(backing_info.keys()):
            backing = serial_port.FileBackingInfo()
            backing.fileName = backing_info['file_path']
        else:
            self.module.fail_json(msg="Failed to create a new serial port of file backing type due to insufficient parameters."
                                  + "The required parameters are file_path")
        return backing

    def get_backing_info(self, serial_port, backing, backing_type):
        """
        Returns the call to the appropriate backing function based on the backing type
        """
        switcher = {
            "network": self.set_network_backing,
            "pipe": self.set_pipe_backing,
            "device": self.set_device_backing,
            "file": self.set_file_backing
        }
        backing_func = switcher.get(backing_type, "Invalid Backing Info")
        return backing_func(serial_port, backing)

    def create_serial_port(self, backing):
        """
        Create a new serial port
        """
        serial_spec = vim.vm.device.VirtualDeviceSpec()
        serial_port = vim.vm.device.VirtualSerialPort()
        serial_port.yieldOnPoll = backing['yield_on_poll'] if 'yield_on_poll' in backing.keys() else True
        serial_port.backing = self.get_backing_info(serial_port, backing, backing['type'])
        serial_spec.device = serial_port
        return serial_spec


def get_serial_port(vm_obj, backing):
    """
    Return the serial port of specified backing type
    """
    serial_port = None
    backing_type_mapping = {
        'network': vim.vm.device.VirtualSerialPort.URIBackingInfo,
        'pipe': vim.vm.device.VirtualSerialPort.PipeBackingInfo,
        'device': vim.vm.device.VirtualSerialPort.DeviceBackingInfo,
        'file': vim.vm.device.VirtualSerialPort.FileBackingInfo
    }
    valid_params = backing.keys()
    for device in vm_obj.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualSerialPort):
            if isinstance(device.backing, backing_type_mapping[backing['type']]):
                if 'service_uri' in valid_params:
                    # network backing type
                    if device.backing.serviceURI == backing['service_uri']:
                        serial_port = device
                    break
                elif 'pipe_name' in valid_params:
                    # named pipe backing type
                    if device.backing.pipeName == backing['pipe_name']:
                        serial_port = device
                    break
                elif 'device_name' in valid_params:
                    # physical serial device backing type
                    if device.backing.deviceName == backing['device_name']:
                        serial_port = device
                    break
                elif 'file_path' in valid_params:
                    # file backing type
                    if device.backing.fileName == backing['file_path']:
                        serial_port = device
                    break
                # if there is a backing of only one type, user need not provide secondary details like service_uri, pipe_name, device_name or file_path
                # we will match the serial port with backing type only
                # in this case, the last matching serial port will be returned
                serial_port = device
    return serial_port


def get_serial_port_info(vm_obj):
    """
    Get the serial port info
    """
    serial_port_info = []
    if vm_obj is None:
        return serial_port_info
    for port in vm_obj.config.hardware.device:
        backing = dict()
        if isinstance(port, vim.vm.device.VirtualSerialPort):
            if isinstance(port.backing, vim.vm.device.VirtualSerialPort.URIBackingInfo):
                backing['backing_type'] = 'network'
                backing['direction'] = port.backing.direction
                backing['service_uri'] = port.backing.serviceURI
            elif isinstance(port.backing, vim.vm.device.VirtualSerialPort.PipeBackingInfo):
                backing['backing_type'] = 'pipe'
                backing['pipe_name'] = port.backing.pipeName
                backing['endpoint'] = port.backing.endpoint
                backing['no_rx_loss'] = port.backing.noRxLoss
            elif isinstance(port.backing, vim.vm.device.VirtualSerialPort.DeviceBackingInfo):
                backing['backing_type'] = 'device'
                backing['device_name'] = port.backing.deviceName
            elif isinstance(port.backing, vim.vm.device.VirtualSerialPort.FileBackingInfo):
                backing['backing_type'] = 'file'
                backing['file_path'] = port.backing.fileName
            else:
                continue
            serial_port_info.append(backing)
    return serial_port_info


def main():
    """
    Main method
    """
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        backings=dict(type='list', default=[])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'uuid', 'moid']
        ],
        mutually_exclusive=[
            ['name', 'uuid', 'moid']
        ],
    )
    result = {'failed': False, 'changed': False}

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm_obj = pyv.get_vm()

    if vm_obj:
        proceed = pyv.check_vm_state(vm_obj)
        if proceed:
            result = pyv.reconfigure_vm_serial_port(vm_obj)

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
