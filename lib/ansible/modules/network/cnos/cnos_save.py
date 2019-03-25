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
# Module to save running config to start up config to Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_save
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Save the running configuration as the startup configuration
 on devices running Lenovo CNOS
description:
    - This module allows you to copy the running configuration of a switch over
     its startup configuration. It is recommended to use this module shortly
     after any major configuration changes so they persist after a switch
     restart. This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the
     playbook is run.
version_added: "2.3"
extends_documentation_fragment: cnos
options: {}

'''
EXAMPLES = '''
Tasks : The following are examples of using the module cnos_save. These are
 written in the main.yml file of the tasks directory.
---
- name: Test Save
  cnos_save:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_save_{{ inventory_hostname }}_output.txt"
'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: str
  sample: "Switch Running Config is Saved to Startup Config"
'''

import sys
import time
import socket
import array
import json
import time
import re
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
            outputfile=dict(required=True),
            host=dict(required=False),
            username=dict(required=False),
            password=dict(required=False, no_log=True),
            enablePassword=dict(required=False, no_log=True),
            deviceType=dict(required=True),),
        supports_check_mode=False)

    command = 'write memory'
    outputfile = module.params['outputfile']
    output = ''
    cmd = [{'command': command, 'prompt': None, 'answer': None}]
    output = output + str(cnos.run_cnos_commands(module, cmd))

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True,
                         msg="Switch Running Config is Saved to Startup Config ")
    else:
        module.fail_json(msg=errorMsg)


if __name__ == '__main__':
    main()
