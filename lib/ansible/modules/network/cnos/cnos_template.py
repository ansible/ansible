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
# Module to send CLI templates to Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_template
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage switch configuration using templates on devices running Lenovo CNOS
description:
    - This module allows you to work with the running configuration of a switch. It provides a way
     to execute a set of CNOS commands on a switch by evaluating the current running configuration
     and executing the commands only if the specific settings have not been already configured.
     The configuration source can be a set of commands or a template written in the Jinja2 templating language.
     This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the playbook is run.
version_added: "2.3"
extends_documentation_fragment: cnos
options:
    commandfile:
        description:
           - This specifies the path to the CNOS command file which needs to be applied. This usually
             comes from the commands folder. Generally this file is the output of the variables applied
             on a template file. So this command is preceded by a template module.
             Note The command file must contain the Ansible keyword {{ inventory_hostname }} in its
             filename to ensure that the command file is unique for each switch and condition.
             If this is omitted, the command file will be overwritten during iteration. For example,
             commandfile=./commands/clos_leaf_bgp_{{ inventory_hostname }}_commands.txt
        required: true
        default: Null
'''
EXAMPLES = '''
Tasks : The following are examples of using the module cnos_template. These are written in the main.yml file of the tasks directory.
---
- name: Replace Config CLI command template with values
  template:
      src: demo_template.j2
      dest: "./commands/demo_template_{{ inventory_hostname }}_commands.txt"
      vlanid1: 13
      slot_chassis_number1: "1/2"
      portchannel_interface_number1: 100
      portchannel_mode1: "active"

- name: Applying CLI commands on Switches
  cnos_template:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      commandfile: "./commands/demo_template_{{ inventory_hostname }}_commands.txt"
      outputfile: "./results/demo_template_command_{{ inventory_hostname }}_output.txt"

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
            host=dict(required=False),
            deviceType=dict(required=True),
            username=dict(required=False),
            password=dict(required=False, no_log=True),
            enablePassword=dict(required=False, no_log=True),),
        supports_check_mode=False)
    commandfile = module.params['commandfile']
    outputfile = module.params['outputfile']
    output = ''

    # Send commands one by one to the device
    f = open(commandfile, "r")
    cmd = []
    for line in f:
        # Omit the comment lines in template file
        if not line.startswith("#"):
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
