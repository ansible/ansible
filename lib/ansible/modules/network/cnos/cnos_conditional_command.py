#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2017 Lenovo, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
# Module to send Conditional CLI commands to Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_conditional_command
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Execute a single command based on condition on devices running Lenovo CNOS
description:
   - This module allows you to modify the running configuration of a switch. It provides a way to
    execute a single CNOS command on a network device by evaluating the current running configuration
    and executing the command only if the specific settings have not been already configured.
    The CNOS command is passed as an argument of the method.
    This module functions the same as the cnos_command module.
    The only exception is that the following inventory variable can be specified
    ["condition = <flag string>"]
    When this inventory variable is specified as the variable of a task, the command is executed for
    the network element that matches the flag string. Usually, commands are executed across a group
    of network devices. When there is a requirement to skip the execution of the command on one or
    more devices, it is recommended to use this module.
    This module uses SSH to manage network device configuration.
    For more information about this module from Lenovo and customizing it usage for your
    use cases, please visit U(http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_conditional_command.html)
version_added: "2.3"
extends_documentation_fragment: cnos
options:
    clicommand:
        description:
            - This specifies the CLI command as an attribute to this method. The command is passed using
             double quotes. The variables can be placed directly on to the CLI commands or can be invoked
             from the vars directory.
        required: true
        default: Null
    condition:
        description:
            - If you specify condition=false in the inventory file against any device, the command execution
             is skipped for that device.
        required: true
        default: Null
    flag:
        description:
            - If a task needs to be executed, you have to set the flag the same as it is specified in the
             inventory for that device.
        required: true
        default: Null

'''
EXAMPLES = '''
Tasks : The following are examples of using the module cnos_conditional_command. These are written in the main.yml file of the tasks directory.
---
- name: Applying CLI template on VLAG Tier1 Leaf Switch1
  cnos_conditional_command:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_conditional_command_{{ inventory_hostname }}_output.txt"
      condition: "{{ hostvars[inventory_hostname]['condition']}}"
      flag: leaf_switch2
      command: "spanning-tree mode enable"

'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: string
  sample: "Command Applied"
'''

import sys
try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False
import time
import socket
import array
import json
import time
import re
try:
    from ansible.module_utils.network.cnos import cnos
    HAS_LIB = True
except:
    HAS_LIB = False
from ansible.module_utils.basic import AnsibleModule
from collections import defaultdict


def main():
    module = AnsibleModule(
        argument_spec=dict(
            clicommand=dict(required=True),
            outputfile=dict(required=True),
            condition=dict(required=True),
            flag=dict(required=True),
            host=dict(required=True),
            deviceType=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            enablePassword=dict(required=False, no_log=True), ), supports_check_mode=False)

    username = module.params['username']
    password = module.params['password']
    enablePassword = module.params['enablePassword']
    condition = module.params['condition']
    flag = module.params['flag']
    cliCommand = module.params['clicommand']
    outputfile = module.params['outputfile']
    deviceType = module.params['deviceType']
    hostIP = module.params['host']
    output = ""
    if not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required for this module')

    if (condition != flag):
        module.exit_json(changed=True, msg="Command Skipped for this value")
        return " "
    # Create instance of SSHClient object
    remote_conn_pre = paramiko.SSHClient()

    # Automatically add untrusted hosts (make sure okay for security policy in your environment)
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # initiate SSH connection with the switch
    remote_conn_pre.connect(hostIP, username=username, password=password)
    time.sleep(2)

    # Use invoke_shell to establish an 'interactive session'
    remote_conn = remote_conn_pre.invoke_shell()
    time.sleep(2)

    # Enable and enter configure terminal then send command
    #
    # Enable and enter configure terminal then send command
    output = output + cnos.waitForDeviceResponse("\n", ">", 2, remote_conn)
    output = output + cnos.enterEnableModeForDevice(enablePassword, 3, remote_conn)

    # Make terminal length = 0
    output = output + cnos.waitForDeviceResponse("terminal length 0\n", "#", 2, remote_conn)

    # Go to config mode
    output = output + cnos.waitForDeviceResponse("configure device\n", "(config)#", 2, remote_conn)

    # Send the CLi command
    output = output + cnos.waitForDeviceResponse(cliCommand + "\n", "(config)#", 2, remote_conn)

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # Logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="CLI Command executed and results saved in file ")
    else:
        module.fail_json(msg=errorMsg)

if __name__ == '__main__':
    main()
