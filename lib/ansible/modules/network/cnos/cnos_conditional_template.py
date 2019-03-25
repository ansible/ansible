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
# Module to send conditional template to Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_conditional_template
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage switch configuration using templates based on
 condition on devices running Lenovo CNOS
description:
    - This module allows you to work with the running configuration of a
     switch. It provides a way to execute a set of CNOS commands on a switch by
     evaluating the current running configuration and executing the commands
     only if the specific settings have not been already configured.
     The configuration source can be a set of commands or a template written in
     the Jinja2 templating language. This module functions the same as the
     cnos_template module. The only exception is that the following inventory
     variable can be specified.
     ["condition = <flag string>"]
     When this inventory variable is specified as the variable of a task, the
     template is executed for the network element that matches the flag string.
     Usually, templates are used when commands are the same across a group of
     network devices. When there is a requirement to skip the execution of the
     template on one or more devices, it is recommended to use this module.
     This module uses SSH to manage network device configuration.
version_added: "2.3"
extends_documentation_fragment: cnos
options:
    commandfile:
        description:
            - This specifies the path to the CNOS command file which needs to
             be applied. This usually comes from the commands folder. Generally
             this file is the output of the variables applied on a template
             file. So this command is preceded by a template module. The
             command file must contain the Ansible keyword
             {{ inventory_hostname }} and the condition flag in its filename to
             ensure that the command file is unique for each switch and
             condition. If this is omitted, the command file will be
             overwritten during iteration. For example,
             commandfile=./commands/clos_leaf_bgp_
                         {{ inventory_hostname }}_LP21_commands.txt
        required: true
        default: Null
    condition:
        description:
            - If you specify condition=<flag string> in the inventory file
             against any device, the template execution is done for that device
             in case it matches the flag setting for that task.
        required: true
        default: Null
    flag:
        description:
            - If a task needs to be executed, you have to set the flag the same
             as it is specified in the inventory for that device.
        required: true
        default: Null
'''
EXAMPLES = '''
Tasks : The following are examples of using the module
 cnos_conditional_template. These are written in the main.yml file of the
 tasks directory.
---
- name: Applying CLI template on VLAG Tier1 Leaf Switch1
  cnos_conditional_template:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/vlag_1tier_leaf_switch1_
                  {{ inventory_hostname }}_output.txt"
      condition: "{{ hostvars[inventory_hostname]['condition']}}"
      flag: "leaf_switch1"
      commandfile: "./commands/vlag_1tier_leaf_switch1_
                    {{ inventory_hostname }}_commands.txt"
      stp_mode1: "disable"
      port_range1: "17,18,29,30"
      portchannel_interface_number1: 1001
      portchannel_mode1: active
      slot_chassis_number1: 1/48
      switchport_mode1: trunk
'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: str
  sample: "Template Applied."
'''

import sys
import time
import socket
import array
import json
import time
import re
import os
try:
    from ansible.module_utils.network.cnos import cnos
    HAS_LIB = True
except Exception:
    HAS_LIB = False
from ansible.module_utils.basic import AnsibleModule
from collections import defaultdict


def main():
    module = AnsibleModule(
        argument_spec=dict(
            commandfile=dict(required=True),
            outputfile=dict(required=True),
            condition=dict(required=True),
            flag=dict(required=True),
            host=dict(required=False),
            deviceType=dict(required=True),
            username=dict(required=False),
            password=dict(required=False, no_log=True),
            enablePassword=dict(required=False, no_log=True),),
        supports_check_mode=False)

    condition = module.params['condition']
    flag = module.params['flag']
    commandfile = module.params['commandfile']
    outputfile = module.params['outputfile']

    output = ''
    if (condition is None or condition != flag):
        module.exit_json(changed=True, msg="Template Skipped for this switch")
        return " "
    # Send commands one by one
    f = open(commandfile, "r")
    cmd = []
    for line in f:
        # Omit the comment lines in template file
        if not line.startswith("#"):
            # cnos.debugOutput(line)
            command = line.strip()
            inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
            cmd.extend(inner_cmd)
    # Write to memory
    save_cmd = [{'command': 'save', 'prompt': None, 'answer': None}]
    cmd.extend(save_cmd)
    output = output + str(cnos.run_cnos_commands(module, cmd))
    # Write output to file
    path = outputfile.rsplit('/', 1)
    # cnos.debugOutput(path[0])
    if not os.path.exists(path[0]):
        os.makedirs(path[0])
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # Logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="Template Applied")
    else:
        module.fail_json(msg=errorMsg)


if __name__ == '__main__':
    main()
