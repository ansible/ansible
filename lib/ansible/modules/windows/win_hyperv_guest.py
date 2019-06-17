#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Wilmar den Ouden <wilmaro@intermax.nl>
# Copyright: (c) 2018, Intermax Cloudsourcing
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = r'''
---
module: win_hyperv_guest
version_added: "2.9"
author:
  - Wilmar den Ouden (@wilmardo) <wilmaro@intermax.nl>
short_description: Manages virtual machines in Hyper-V
description:
    - This module manages VM's on a Hyper-V host. It creates, destroys and performs powerfunctions.
    - Hyper-V Module for Windows PowerShell needs to be installed
options:
  name:
    description:
      - Name of VM
    type: str
    required: true
  state:
    description:
      - State of VM, for started, stopped, restarted and shutdown the VM needs to exist
      - Poweroperations are performed after state updates!
      - Important to notice for generation 1 VM's and disk updates, stopping the VM and the disk updates are seperate tasks
    type: str
    required: false
    choices:
      - present
      - absent
      - created
      - started
      - stopped
      - restarted
    default: present
  force_stop:
    description:
      - When true the virtual plug is pulled on the VM instead of a gentle shutdown (poweroff instead of shutdown)
    type: bool
    required: false
    default: false
  hostserver:
    description:
      - Server to host VM
    type: str
    required: false
    default: null
  generation:
    description:
      - Specifies the generation of the VM, cannot be updated without recreating the VM
    type: int
    required: false
    choices:
      - 1
      - 2
    default: 1
  cpu:
    description:
      - Sets the amount of cores of the VM
    type: int
    required: false
    default: 1
  memory:
    description:
      - Sets the amount of memory for the VM.
    type: str
    required: false
    default: 512MB
  disks:
    description:
      - Specifies the disks for the VM, of not specified no VHD will be created or added
      - If the path exists the existing VHD will be attached
      - 'If disks is specified with state: absent the disks will be deleted from the disk'
      - If the size differs it will try to resize the VHD
      - Resizing disks of running VM is only supported on a SCSI controller with VHDX disks
      - 'The the following options are required per entry:'
      - ' - C(path) (string): The path for the new or existing VHD'
      - ' - C(size) (string): Size of the VHD specified as 1GB or 200MB'
      - 'The following options are optional:'
      - ' - C(parent_path) (string): If set a parent of the disk to create a differencing disk (available since Server 2012)'
      - ' - C(first_boot_device) (bool): If set this disk will be set first boot device, only supported on a generarion 2 VM!'
    type: list
    required: false
    default: null
  network_adapters:
    description:
      - Specifies the network adapters for the VM,
        if not specified one adapter will be created by Hyper-V (Network Adapter) but not connected to a switch
      - Network Adapters are matched by name, when an adapter with a matching name is found but the switch_name differs
        it connects the adapter to the specified switch.
      - Therefore names must be unique!
      - 'The below parameters are required per entry:'
      - ' - C(name) (string): The name of the network adapter'
      - 'The following options are optional'
      - ' - C(switch_name) (string): Name of the switch to connect the adapter to'
    type: list
    required: false
    default: null
  secure_boot:
    description: Enables or disables secure_boot
    type: bool
    required: false
    default: false
  secure_boot_template:
    description:
      - Set the name of the Secure Boot template
      - Can't be changed when VM is running!
      - Only valid for generation 2 machines with secure_boot enabled
    choices:
      - MicrosoftWindows
      - MicrosoftUEFICertificateAuthority
    type: str
    required: false
    default: null
  wait_for_ip:
    description:
      - When true waits until an IP address is set on the first network interface after starting or restarting
    type: bool
    required: false
    default: false
  timeout:
    description:
      - Timeout in seconds for waiting on IPV4 address
    type: int
    required: false
    default: 30
'''

EXAMPLES = r'''
  - name: Create and start VM with default values
    win_hyperv_guest:
      name: Test

  - name: Delete a VM without removing the disk from the host
    win_hyperv_guest:
      name: Test
      state: absent

  - name: Delete a VM and remove the disk from the host
    win_hyperv_guest:
      name: Test
      disks:
        - path: V:\hyper-v\disks\CentOS7-disk0.vhdx
      state: absent

  - name: Create generation 1 VM with 256MB memory and the default adapter (Network Adapter) connected to Internal Switch
    win_hyperv_guest:
      name: Test
      generation: 1
      memory: 256MB
      network_adapters:
        - name: Network Adapter
          switch_name: Internal Switch

  - name: >
      Create generation 2 VM based of a parent disk and set as first boot device,
      Sets MicrosoftUEFICertificateAuthority as secure boot template
      and wait for an IP on the first network adapter.
    win_hyperv_guest:
      name: Test
      cpu: 2
      memory: 2048MB
      disks:
        - path: V:\hyper-v\disks\CentOS7-disk0.vhdx"
          size: 20GB
          parent_path: V:\hyper-v\parents\CentOS_7_template-disk1.vhdx
          first_boot_device: true
        - path: V:\hyper-v\disks\CentOS7-disk1.vhdx
          size: 20GB
      network_adapters:
        - name: Network Adapter
          switch_name: NATSwitch
      secure_boot_template: MicrosoftUEFICertificateAuthority
      wait_for_ip: true
'''

RETURN = r'''
instance:
  description: metadata about the new virtual machine
  returned: always
  type: dict
  sample: None
invocation:
  description: parameters passed to the module
  returned: always
  type: dict
  sample: None
'''
