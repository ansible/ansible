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
# Module to send VLAG commands to Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_vlag
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage VLAG resources and attributes on devices running Lenovo CNOS
description:
    - This module allows you to work with virtual Link Aggregation Groups
     (vLAG) related configurations. The operators used are overloaded to ensure
     control over switch vLAG configurations. Apart from the regular device
     connection related attributes, there are four vLAG arguments which are
     overloaded variables that will perform further configurations. They are
     vlagArg1, vlagArg2, vlagArg3, and vlagArg4. For more details on how to use
     these arguments, see [Overloaded Variables].
     This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the playbook is run.
     For more information about this module from Lenovo and customizing it usage for your
     use cases, please visit U(http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_vlag.html)
version_added: "2.3"
extends_documentation_fragment: cnos
options:
  vlagArg1:
    description:
      - This is an overloaded vlag first argument. Usage of this argument can be found is the User Guide referenced above.
    required: Yes
    default: Null
    choices: [enable, auto-recovery,config-consistency,isl,mac-address-table,peer-gateway,priority,startup-delay,tier-id,vrrp,instance,hlthchk]
  vlagArg2:
    description:
      - This is an overloaded vlag second argument. Usage of this argument can be found is the User Guide referenced above.
    required: No
    default: Null
    choices: [Interval in seconds,disable or strict,Port Aggregation Number,VLAG priority,Delay time in seconds,VLAG tier-id value,
        VLAG instance number,keepalive-attempts,keepalive-interval,retry-interval,peer-ip]
  vlagArg3:
    description:
      - This is an overloaded vlag third argument. Usage of this argument can be found is the User Guide referenced above.
    required: No
    default: Null
    choices: [enable or port-aggregation,Number of keepalive attempts,Interval in seconds,Interval in seconds,VLAG health check peer IP4 address]
  vlagArg4:
    description:
      - This is an overloaded vlag fourth argument. Usage of this argument can be found is the User Guide referenced above.
    required: No
    default: Null
    choices: [Port Aggregation Number,default or management]

'''
EXAMPLES = '''

Tasks : The following are examples of using the module cnos_vlag. These are written in the main.yml file of the tasks directory.
---
- name: Test Vlag  - enable
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "enable"

- name: Test Vlag - autorecovery
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "auto-recovery"
      vlagArg2: 266

- name: Test Vlag - config-consistency
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "config-consistency"
      vlagArg2: "strict"

- name: Test Vlag - isl
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "isl"
      vlagArg2: 23

- name: Test Vlag  - mac-address-table
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "mac-address-table"

- name: Test Vlag - peer-gateway
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "peer-gateway"

- name: Test Vlag - priority
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "priority"
      vlagArg2: 1313

- name: Test Vlag - startup-delay
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "startup-delay"
      vlagArg2: 323

- name: Test Vlag  - tier-id
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "tier-id"
      vlagArg2: 313

- name: Test Vlag - vrrp
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "vrrp"

- name: Test Vlag - instance
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "instance"
      vlagArg2: 33
      vlagArg3: 333

- name: Test Vlag - instance2
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "instance"
      vlagArg2: "33"

- name: Test Vlag  - keepalive-attempts
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "hlthchk"
      vlagArg2: "keepalive-attempts"
      vlagArg3: 13

- name: Test Vlag - keepalive-interval
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "hlthchk"
      vlagArg2: "keepalive-interval"
      vlagArg3: 131

- name: Test Vlag - retry-interval
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "hlthchk"
      vlagArg2: "retry-interval"
      vlagArg3: 133

- name: Test Vlag - peer ip
  cnos_vlag:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user']}}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass']}}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "hlthchk"
      vlagArg2: "peer-ip"
      vlagArg3: "1.2.3.4"

'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: string
  sample: "vLAG configurations accomplished"
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
    #
    # Define parameters for vlag creation entry
    #
    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            enablePassword=dict(required=False, no_log=True),
            deviceType=dict(required=True),
            vlagArg1=dict(required=True),
            vlagArg2=dict(required=False),
            vlagArg3=dict(required=False),
            vlagArg4=dict(required=False),),
        supports_check_mode=False)

    username = module.params['username']
    password = module.params['password']
    enablePassword = module.params['enablePassword']
    outputfile = module.params['outputfile']
    hostIP = module.params['host']
    deviceType = module.params['deviceType']
    vlagArg1 = module.params['vlagArg1']
    vlagArg2 = module.params['vlagArg2']
    vlagArg3 = module.params['vlagArg3']
    vlagArg4 = module.params['vlagArg4']
    output = ""
    if not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required for this module')

    # Create instance of SSHClient object
    remote_conn_pre = paramiko.SSHClient()

    # Automatically add untrusted hosts (make sure okay for security policy in
    # your environment)
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # initiate SSH connection with the switch
    remote_conn_pre.connect(hostIP, username=username, password=password)
    time.sleep(2)

    # Use invoke_shell to establish an 'interactive session'
    remote_conn = remote_conn_pre.invoke_shell()
    time.sleep(2)

    # Enable and enter configure terminal then send command
    output = output + cnos.waitForDeviceResponse("\n", ">", 2, remote_conn)

    output = output + \
        cnos.enterEnableModeForDevice(enablePassword, 3, remote_conn)

    # Make terminal length = 0
    output = output + \
        cnos.waitForDeviceResponse("terminal length 0\n", "#", 2, remote_conn)

    # Go to config mode
    output = output + \
        cnos.waitForDeviceResponse(
            "configure device\n", "(config)#", 2, remote_conn)

    # Send the CLi command
    output = output + cnos.vlagConfig(
        remote_conn, deviceType, "(config)#", 2, vlagArg1, vlagArg2, vlagArg3,
        vlagArg4)

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # need to add logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="vlag configurations accomplished")
    else:
        module.fail_json(msg=errorMsg)


if __name__ == '__main__':
    main()
