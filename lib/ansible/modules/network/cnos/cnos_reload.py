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
# Module to reload Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_reload
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Perform switch restart on devices running Lenovo CNOS
description:
    - This module allows you to restart the switch using the current startup
     configuration. The module is usually invoked after the running
     configuration has been saved over the startup configuration.
     This module uses SSH to manage network device configuration.
     The results of the operation can be viewed in results directory.
version_added: "2.3"
extends_documentation_fragment: cnos
options: {}

'''
EXAMPLES = '''
Tasks : The following are examples of using the module cnos_reload. These are
 written in the main.yml file of the tasks directory.
---
- name: Test Reload
  cnos_reload:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_reload_{{ inventory_hostname }}_output.txt"
'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: str
  sample: "Device is Reloading. Please wait..."
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

    command = 'reload'
    outputfile = module.params['outputfile']
    output = ''
    cmd = [{'command': command, 'prompt': 'reboot system? (y/n): ',
            'answer': 'y'}]
    output = output + str(cnos.run_cnos_commands(module, cmd))

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg in "Device Response Timed out"):
        module.exit_json(changed=True,
                         msg="Device is Reloading. Please wait...")
    else:
        module.fail_json(msg=errorMsg)


if __name__ == '__main__':
    main()
