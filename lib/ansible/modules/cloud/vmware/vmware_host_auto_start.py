#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, sky-joker
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: vmware_host_auto_start
short_description: Manage the auto power ON or OFF for vm on ESXi host
author:
  - sky-joker (@sky-joker)
version_added: '2.10'
description:
  - In this module, can set up automatic startup and shutdown of virtual machines according to host startup or shutdown.
requirements:
  - python >= 2.7
  - PyVmomi
options:
  esxi_hostname:
    description:
    - ESXi hostname where the VM to set auto power on or off exists.
    type: str
    required: True
  name:
    description:
    - VM name to set auto power on or off.
    - This is not necessary if change only system default VM settings for autoStart config.
    type: str
  uuid:
    description:
    - VM uuid to set auto power on or off, this is VMware's unique identifier.
    - This is required if C(name) is not supplied.
    - This is not necessary if change only system default VM settings for autoStart config.
    type: str
  use_instance_uuid:
    description:
    - Whether to use the VMware instance UUID rather than the BIOS UUID.
    type: bool
    default: no
  moid:
    description:
    - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
    - This is required if C(name) or C(uuid) is not supplied.
    type: str
  system_defaults:
    description:
    - System defaults for auto-start or auto-stop config for virtual machine.
    type: dict
    suboptions:
      enabled:
        description:
        - Enable automatically start or stop of virtual machines.
        type: bool
        default: False
      start_delay:
        description:
        - Default auto start delay in seconds.
        type: int
        default: 120
      stop_action:
        description:
        - Default stop action executed on the virtual machine when the system stops.
        type: str
        choices: ['none', 'guestShutdown', 'powerOff', 'suspend']
        default: powerOff
      stop_delay:
        description:
        - Default auto stop delay in seconds.
        type: int
        default: 120
      wait_for_heartbeat:
        description:
        - Continue power on processing when VMware Tools started.
        - If this parameter is enabled to powers on the next virtual machine without waiting for the delay to pass.
        - However, the virtual machine must have VMware Tools installed.
        type: bool
        default: False
  power_info:
    description:
    - Startup or shutdown settings of virtual machine.
    - This setting will override the system defaults.
    type: dict
    default:
      start_action: none
      start_delay: -1
      start_order: -1
      stop_action: systemDefault
      stop_delay: -1
      wait_for_heartbeat: systemDefault
    suboptions:
      start_action:
        description:
        - Whether to start the virtual machine when the host startup.
        type: str
        choices: ['none', 'powerOn']
        default: none
      start_delay:
        description:
        - Auto start delay in seconds of virtual machine.
        type: int
        default: -1
      start_order:
        description:
        - The autostart priority of virtual machine.
        - Virtual machines with a lower number are powered on first.
        - On host shutdown, the virtual machines are shut down in reverse order, meaning those with a higher number are powered off first.
        type: int
        default: -1
      stop_action:
        description:
        - Stop action executed on the virtual machine when the system stops of virtual machine.
        choices: ['none', 'systemDefault', 'powerOff', 'suspend']
        type: str
        default: systemDefault
      stop_delay:
        description:
        - Auto stop delay in seconds of virtual machine.
        type: int
        default: -1
      wait_for_heartbeat:
        description:
        - Continue power on processing when VMware Tools started.
        type: str
        choices: ['no', 'yes', 'systemDefault']
        default: systemDefault
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
---
- name: Update for system defaults config.
  vmware_host_auto_start:
    hostname: "{{ hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    validate_certs: no
    esxi_hostname: "{{ esxi_hostname }}"
    system_defaults:
      enabled: yes
      start_delay: 100
      stop_action: guestShutdown

- name: Update for powerInfo config of virtual machine.
  vmware_host_auto_start:
    hostname: "{{ hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    validate_certs: no
    esxi_hostname: "{{ esxi_hostname }}"
    name: "{{ vm_name }}"
    power_info:
      start_action: powerOn
      start_delay: 10
      start_order: 1
      stop_action: powerOff
      wait_for_heartbeat: yes
'''

RETURN = '''
system_defaults_config:
  description: Parameter return when system defaults config is changed.
  returned: changed
  type: dict
  sample: >-
    {
      "enabled": true,
      "start_delay": 120,
      "stop_action": "powerOff",
      "stop_delay": 120,
      "wait_for_heartbeat": false
    }
power_info_config:
  description: Parameter return when virtual machine power info config is changed.
  returned: changed
  type: dict
  sample: >-
    {
      "start_action": "powerOn",
      "start_delay": -1,
      "start_order": -1,
      "stop_action": "systemDefault",
      "stop_delay": -1,
      "wait_for_heartbeat": "systemDefault"
    }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

try:
    from collections import OrderedDict
except ImportError:
    try:
        from ordereddict import OrderedDict
    except ImportError:
        pass

from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils.basic import AnsibleModule


class VMwareHostAutoStartManager(PyVmomi):
    def __init__(self, module):
        super(VMwareHostAutoStartManager, self).__init__(module)
        self.esxi_hostname = self.params['esxi_hostname']
        self.name = self.params['name']
        self.uuid = self.params['uuid']
        self.moid = self.params['moid']
        self.system_defaults = self.params['system_defaults']
        self.power_info = self.params['power_info']

    def generate_system_defaults_config(self):
        system_defaults_config = vim.host.AutoStartManager.SystemDefaults()
        system_defaults_config.enabled = self.system_defaults['enabled']
        system_defaults_config.startDelay = self.system_defaults['start_delay']
        system_defaults_config.stopAction = self.system_defaults['stop_action']
        system_defaults_config.stopDelay = self.system_defaults['stop_delay']
        system_defaults_config.waitForHeartbeat = self.system_defaults['wait_for_heartbeat']

        return system_defaults_config

    def generate_power_info_config(self):
        power_info_config = vim.host.AutoStartManager.AutoPowerInfo()
        power_info_config.key = self.vm_obj
        power_info_config.startAction = self.power_info['start_action']
        power_info_config.startDelay = self.power_info['start_delay']
        power_info_config.startOrder = self.power_info['start_order']
        power_info_config.stopAction = self.power_info['stop_action']
        power_info_config.stopDelay = self.power_info['stop_delay']
        power_info_config.waitForHeartbeat = self.power_info['wait_for_heartbeat']

        return power_info_config

    def execute(self):
        result = dict(changed=False, diff={'before': {}, 'after': {}})

        host_obj = self.find_hostsystem_by_name(self.esxi_hostname)
        if not host_obj:
            self.module.fail_json(msg="Cannot find the specified ESXi host: %s" % self.esxi_hostname)

        self.vm_obj = None
        if self.name or self.uuid or self.moid:
            self.vm_obj = self.get_vm()
            if not self.vm_obj:
                self.module.fail_json(msg="Cannot find the specified VM: %s" % (self.name or self.uuid or self.moid))
            elif self.esxi_hostname != self.vm_obj.runtime.host.name:
                self.module.fail_json(msg="%s exists on another host: %s" % (self.name or self.uuid or self.moid, self.vm_obj.runtime.host.name))

        # Check the existing autoStart setting difference.
        system_defaults_config_difference = False
        existing_system_defaults = self.to_json(host_obj.config.autoStart.defaults)
        system_defaults_for_compare = dict(
            enabled=existing_system_defaults['enabled'],
            start_delay=existing_system_defaults['startDelay'],
            stop_action=existing_system_defaults['stopAction'],
            stop_delay=existing_system_defaults['stopDelay'],
            wait_for_heartbeat=existing_system_defaults['waitForHeartbeat']
        )
        if self.system_defaults:
            if 'guestshutdown' == system_defaults_for_compare['stop_action']:
                system_defaults_for_compare['stop_action'] = 'guestShutdown'

            if 'poweroff' == system_defaults_for_compare['stop_action']:
                system_defaults_for_compare['stop_action'] = 'powerOff'

            if system_defaults_for_compare != self.system_defaults:
                result['diff']['before']['system_defaults'] = OrderedDict(sorted(system_defaults_for_compare.items()))
                result['diff']['after']['system_defaults'] = OrderedDict(sorted(self.system_defaults.items()))
                system_defaults_config_difference = True

        # Check the existing autoStart powerInfo setting difference for VM.
        vm_power_info_config_difference = False
        existing_vm_power_info = {}
        if system_defaults_for_compare['enabled'] and self.vm_obj:
            for vm_power_info in host_obj.config.autoStart.powerInfo:
                if vm_power_info.key == self.vm_obj:
                    existing_vm_power_info = self.to_json(vm_power_info)
                    break

            if existing_vm_power_info:
                vm_power_info_for_compare = dict(
                    start_action=existing_vm_power_info['startAction'],
                    start_delay=existing_vm_power_info['startDelay'],
                    start_order=existing_vm_power_info['startOrder'],
                    stop_action=existing_vm_power_info['stopAction'],
                    stop_delay=existing_vm_power_info['stopDelay'],
                    wait_for_heartbeat=existing_vm_power_info['waitForHeartbeat']
                )
            else:
                vm_power_info_for_compare = dict(
                    start_action='none',
                    start_delay=-1,
                    start_order=-1,
                    stop_action='systemDefault',
                    stop_delay=-1,
                    wait_for_heartbeat='systemDefault'
                )

            if vm_power_info_for_compare != self.power_info:
                result['diff']['before']['power_info'] = OrderedDict(sorted(vm_power_info_for_compare.items()))
                result['diff']['after']['power_info'] = OrderedDict(sorted(self.power_info.items()))
                vm_power_info_config_difference = True

        auto_start_manager_config = vim.host.AutoStartManager.Config()
        auto_start_manager_config.powerInfo = []
        if system_defaults_config_difference or vm_power_info_config_difference:
            if system_defaults_config_difference:
                auto_start_manager_config.defaults = self.generate_system_defaults_config()
                result['system_defaults_config'] = self.system_defaults

            if vm_power_info_config_difference:
                auto_start_manager_config.powerInfo = [self.generate_power_info_config()]
                result['power_info_config'] = self.power_info

            if self.module.check_mode:
                result['changed'] = True
                self.module.exit_json(**result)

            try:
                host_obj.configManager.autoStartManager.ReconfigureAutostart(spec=auto_start_manager_config)
                result['changed'] = True
                self.module.exit_json(**result)
            except Exception as e:
                self.module.fail_json(msg=to_native(e))

            self.module.exit_json(**result)
        else:
            self.module.exit_json(**result)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(esxi_hostname=dict(type='str', required=True),
                         name=dict(type='str'),
                         uuid=dict(type='str'),
                         use_instance_uuid=dict(type='bool', default=False),
                         moid=dict(type='str'),
                         system_defaults=dict(type='dict',
                                              options=dict(
                                                  enabled=dict(type='bool', default=False),
                                                  start_delay=dict(type='int', default=120),
                                                  stop_action=dict(type='str', choices=['none', 'guestShutdown',
                                                                                        'powerOff', 'suspend'],
                                                                   default='powerOff'),
                                                  stop_delay=dict(type='int', default=120),
                                                  wait_for_heartbeat=dict(type='bool', default=False)),
                                              ),
                         power_info=dict(type='dict',
                                         options=dict(
                                             start_action=dict(type='str', choices=['none', 'powerOn'], default='none'),
                                             start_delay=dict(type='int', default=-1),
                                             start_order=dict(type='int', default=-1),
                                             stop_action=dict(type='str', choices=['none', 'systemDefault', 'powerOff',
                                                                                   'suspend'], default='systemDefault'),
                                             stop_delay=dict(type='int', default=-1),
                                             wait_for_heartbeat=dict(type='str', choices=['no', 'yes', 'systemDefault'],
                                                                     default='systemDefault')),
                                         default=dict(
                                             start_action='none',
                                             start_delay=-1,
                                             start_order=-1,
                                             stop_action='systemDefault',
                                             stop_delay=-1,
                                             wait_for_heartbeat='systemDefault'
                                         ))
                         )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    vmware_host_auto_start = VMwareHostAutoStartManager(module)
    vmware_host_auto_start.execute()


if __name__ == "__main__":
    main()
