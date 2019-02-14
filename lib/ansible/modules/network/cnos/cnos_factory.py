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
# Module to Reset to factory settings of Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_factory
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Reset the switch startup configuration to default (factory)
 on devices running Lenovo CNOS.
description:
    - This module allows you to reset a switch's startup configuration. The
     method provides a way to reset the startup configuration to its factory
     settings. This is helpful when you want to move the switch to another
     topology as a new network device. This module uses SSH to manage network
     device configuration. The result of the operation can be viewed in results
     directory.
version_added: "2.3"
extends_documentation_fragment: cnos
options: {}

'''
EXAMPLES = '''
Tasks : The following are examples of using the module cnos_reload. These are
 written in the main.yml file of the tasks directory.
---
- name: Test Reset to factory
  cnos_factory:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_factory_{{ inventory_hostname }}_output.txt"

'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: str
  sample: "Switch Startup Config is Reset to factory settings"
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

    command = 'write erase'
    outputfile = module.params['outputfile']
    output = ''
    cmd = [{'command': command, 'prompt': '[n]', 'answer': 'y'}]
    output = output + str(cnos.run_cnos_commands(module, cmd))

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True,
                         msg="Switch Startup Config is Reset to Factory settings")
    else:
        module.fail_json(msg=errorMsg)


if __name__ == '__main__':
    main()
